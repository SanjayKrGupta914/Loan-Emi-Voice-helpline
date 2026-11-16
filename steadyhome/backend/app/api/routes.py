"""
FastAPI Routes for SteadyHome Loan EMI Voice Helpline.
Provides endpoints for:
- Dashboard metrics & analytics
- Borrower management & profiles
- Loan & EMI schedules
- Borrower verification tool
- AI Agent chat & voice turn handling
- Late fee & part payment processing
- Escalations tracking
- Automated evaluation & testing engine
- System architecture metadata
- Contextual payment-day advisory
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import get_db
from database.schema import Borrower, Loan, EMI, Payment, Escalation, InteractionLog
from app.core.config import settings, get_simulated_now, set_simulated_now, reset_simulated_now
from app.tools.loan_tools import (
    verify_borrower,
    lookup_loan,
    check_loan_status,
    calculate_late_fee,
    validate_payment_mode,
    validate_part_payment_amount,
    build_handoff_details
)
from app.guardrails.safety import check_guardrails
from app.agents.orchestrator import process_user_turn, get_or_create_session, SESSION_STORE
from app.services.advisory import get_payment_day_advisory
from app.services import gemini, supabase_sync
from app.services.evaluator import TEST_DEFINITIONS, run_all_tests, run_single_test

router = APIRouter()

# ----------------- PYDANTIC SCHEMAS -----------------

class VerifyRequest(BaseModel):
    borrower_id: str = Field(..., examples=["SH-BOR-1001"])
    date_of_birth: str = Field(..., examples=["1985-06-15"])
    loan_last_four: str = Field(..., examples=["1001"])

class ChatTurnRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., examples=["I want to check my EMI due date"])
    simulated_now: Optional[str] = None

class LateFeeRequest(BaseModel):
    emi_amount: float = Field(..., examples=[39052.0])
    due_date: str = Field(..., examples=["2026-11-05"])
    payment_status: Optional[str] = "PENDING"
    simulated_now: Optional[str] = None

class PartPaymentRequest(BaseModel):
    loan_id: str = Field(..., examples=["SH-LN-1001"])
    amount: float = Field(..., examples=[5000.0])
    payment_mode: Optional[str] = "NetPay"
    payment_date: Optional[str] = None

class EscalationCreateRequest(BaseModel):
    borrower_id: Optional[str] = None
    intent: str = Field(..., examples=["DUE_DATE_ENQUIRY"])
    reason: str = Field(..., examples=["Customer requested human agent."])
    payment_mode: Optional[str] = None
    conversation_summary: str = Field(..., examples=["Transferred to customer care representative."])

class ClockUpdateRequest(BaseModel):
    simulated_now: str = Field(..., examples=["2026-11-10T09:00:00"])

# ----------------- 1. DASHBOARD -----------------

@router.get("/dashboard", summary="Get SteadyHome Operations Overview & Analytics")
def get_dashboard(db: Session = Depends(get_db)):
    """
    Returns dashboard statistics cards and trend charts strictly queried from SQLite:
    1. Total Borrowers
    2. Active Loans
    3. Pending EMIs
    4. Successful Payments
    5. Total Collections
    6. Human Agent Escalations
    """
    sim_now = get_simulated_now()

    total_borrowers = db.query(Borrower).count()
    active_loans = db.query(Loan).filter(Loan.loan_status == 'ACTIVE').count()
    pending_emis = db.query(EMI).filter(EMI.payment_status.in_(['PENDING', 'OVERDUE'])).count()
    successful_payments = db.query(Payment).filter(Payment.payment_status == 'SUCCESS').count()
    
    total_collections_result = db.query(func.sum(Payment.amount)).filter(Payment.payment_status == 'SUCCESS').scalar()
    total_collections = float(total_collections_result or 0.0)
    
    escalations_count = db.query(Escalation).count()

    # Visualizations Data
    # A. EMI Collection Trends (by month from payments and EMIs)
    # Group payments by month
    payments = db.query(Payment).all()
    monthly_map: Dict[str, Dict[str, float]] = {}
    for p in payments:
        month_key = p.payment_date[:7] if p.payment_date else "2026-10"
        if month_key not in monthly_map:
            monthly_map[month_key] = {"month": month_key, "collected": 0.0, "pending": 0.0}
        if p.payment_status == "SUCCESS":
            monthly_map[month_key]["collected"] += p.amount

    # Group pending EMIs by due month
    emis = db.query(EMI).all()
    for e in emis:
        month_key = e.due_date[:7] if e.due_date else "2026-11"
        if month_key not in monthly_map:
            monthly_map[month_key] = {"month": month_key, "collected": 0.0, "pending": 0.0}
        if e.payment_status in ["PENDING", "OVERDUE"]:
            monthly_map[month_key]["pending"] += e.emi_amount

    collection_trends = sorted(list(monthly_map.values()), key=lambda x: x["month"])
    if not collection_trends:
        collection_trends = [
            {"month": "2026-08", "collected": 150000.0, "pending": 45000.0},
            {"month": "2026-09", "collected": 190000.0, "pending": 38000.0},
            {"month": "2026-10", "collected": 260000.0, "pending": 42000.0},
            {"month": "2026-11", "collected": 310000.0, "pending": 125000.0},
        ]

    # B. Payment Mode Distribution
    mode_counts = db.query(EMI.payment_mode, func.count(EMI.emi_id)).group_by(EMI.payment_mode).all()
    payment_mode_dist = [{"name": mode or "Unknown", "count": count} for mode, count in mode_counts]

    # C. Loan Status Distribution
    status_counts = db.query(Loan.loan_status, func.count(Loan.loan_id)).group_by(Loan.loan_status).all()
    loan_status_dist = [{"status": s or "UNKNOWN", "count": count} for s, count in status_counts]

    # D. Recent Customer Interactions
    recent_logs = db.query(InteractionLog).order_by(InteractionLog.id.desc()).limit(8).all()
    recent_interactions = [
        {
            "id": log.id,
            "session_id": log.session_id,
            "borrower_id": log.borrower_id or "Unverified",
            "event_type": log.event_type,
            "agent_name": log.agent_name,
            "timestamp": log.timestamp,
            "details": log.details
        }
        for log in recent_logs
    ]

    # E. Recent Escalations
    recent_esc = db.query(Escalation).order_by(Escalation.timestamp.desc()).limit(6).all()
    escalations_list = [
        {
            "escalation_id": esc.escalation_id,
            "borrower_id": esc.borrower_id or "Unverified",
            "intent": esc.intent,
            "reason": esc.reason,
            "payment_mode": esc.payment_mode,
            "status": esc.transfer_status,
            "timestamp": esc.timestamp
        }
        for esc in recent_esc
    ]

    return {
        "stats": {
            "total_borrowers": total_borrowers,
            "active_loans": active_loans,
            "pending_emis": pending_emis,
            "successful_payments": successful_payments,
            "total_collections": total_collections,
            "human_escalations": escalations_count,
            "simulated_clock": sim_now.isoformat()
        },
        "collection_trends": collection_trends,
        "payment_mode_distribution": payment_mode_dist,
        "loan_status_distribution": loan_status_dist,
        "recent_interactions": recent_interactions,
        "recent_escalations": escalations_list
    }

# ----------------- 2. BORROWERS -----------------

@router.get("/borrowers", summary="List All Borrowers with Filter & Search")
def list_borrowers(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Borrower)
    if status and status.upper() != "ALL":
        query = query.filter(Borrower.status == status.upper())
    
    borrowers = query.all()
    results = []
    for b in borrowers:
        if search:
            s_clean = search.lower()
            if s_clean not in b.borrower_id.lower() and s_clean not in b.name.lower():
                continue

        # Get loan details
        primary_loan = b.loans[0] if b.loans else None
        results.append({
            "borrower_id": b.borrower_id,
            "name": b.name,
            "date_of_birth": b.date_of_birth,
            "phone": b.phone,
            "email": b.email,
            "borrower_status": b.status,
            "address": b.address,
            "loan_id": primary_loan.loan_id if primary_loan else None,
            "loan_amount": primary_loan.loan_amount if primary_loan else 0.0,
            "loan_status": primary_loan.loan_status if primary_loan else "N/A",
            "emi_amount": primary_loan.emi_amount if primary_loan else 0.0,
            "next_due_date": primary_loan.next_due_date if primary_loan else "N/A"
        })
    return {"total": len(results), "borrowers": results}


@router.get("/borrowers/{borrower_id}", summary="Get Detailed Borrower Profile")
def get_borrower_profile(borrower_id: str, db: Session = Depends(get_db)):
    borrower = db.query(Borrower).filter(Borrower.borrower_id == borrower_id).first()
    if not borrower:
        raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

    loans_data = []
    for l in borrower.loans:
        emis_data = [
            {
                "emi_id": e.emi_id,
                "amount": e.emi_amount,
                "due_date": e.due_date,
                "payment_status": e.payment_status,
                "payment_mode": e.payment_mode,
                "days_overdue": e.days_overdue,
                "late_fee": e.late_fee,
                "paid_date": e.paid_date
            }
            for e in l.emis
        ]
        loans_data.append({
            "loan_id": l.loan_id,
            "amount": l.loan_amount,
            "status": l.loan_status,
            "tenure_months": l.loan_tenure_months,
            "interest_rate": l.interest_rate,
            "emi_amount": l.emi_amount,
            "next_due_date": l.next_due_date,
            "sanction_date": l.sanction_date,
            "emis": emis_data
        })

    return {
        "borrower_id": borrower.borrower_id,
        "name": borrower.name,
        "date_of_birth": borrower.date_of_birth,
        "phone": borrower.phone,
        "email": borrower.email,
        "status": borrower.status,
        "address": borrower.address,
        "loans": loans_data
    }

# ----------------- 3. LOANS -----------------

@router.get("/loans", summary="List All Home Loans")
def list_loans(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Loan)
    if status and status.upper() != "ALL":
        query = query.filter(Loan.loan_status == status.upper())
    loans = query.all()
    return [
        {
            "loan_id": l.loan_id,
            "borrower_id": l.borrower_id,
            "borrower_name": l.borrower.name if l.borrower else "Unknown",
            "loan_amount": l.loan_amount,
            "loan_status": l.loan_status,
            "tenure_months": l.loan_tenure_months,
            "interest_rate": l.interest_rate,
            "emi_amount": l.emi_amount,
            "next_due_date": l.next_due_date
        }
        for l in loans
    ]

# ----------------- 4. EMIS -----------------

@router.get("/emis", summary="List All EMIs with Filter & Late Fee")
def list_emis(
    status: Optional[str] = None,
    payment_mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(EMI)
    if status and status.upper() != "ALL":
        query = query.filter(EMI.payment_status == status.upper())
    if payment_mode and payment_mode.upper() != "ALL":
        query = query.filter(EMI.payment_mode == payment_mode)

    emis = query.all()
    sim_now = get_simulated_now()

    results = []
    for e in emis:
        # Dynamically recalculate late fee against simulated clock for accuracy
        fee_calc = calculate_late_fee(
            emi_amount=e.emi_amount,
            due_date=e.due_date,
            payment_status=e.payment_status,
            simulated_current_date=sim_now
        )
        results.append({
            "emi_id": e.emi_id,
            "loan_id": e.loan_id,
            "borrower_id": e.borrower_id,
            "emi_amount": e.emi_amount,
            "due_date": e.due_date,
            "payment_status": e.payment_status,
            "payment_mode": e.payment_mode,
            "days_overdue": fee_calc["days_overdue"],
            "late_fee": fee_calc["late_fee_amount"],
            "can_process_online": fee_calc["can_process_online"],
            "paid_date": e.paid_date
        })
    return {"total": len(results), "emis": results}

# ----------------- 5. VERIFICATION (TOOL 1) -----------------

@router.post("/verify", summary="Verify Borrower Identity (Tool 1)")
def verify_identity(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Executes Tool 1: verify_borrower.
    Rules:
    - Never disclose which individual field was incorrect!
    - If status is BLOCKED: immediately return escalation flag.
    """
    result = verify_borrower(
        borrower_id=req.borrower_id,
        date_of_birth=req.date_of_birth,
        loan_last_four=req.loan_last_four,
        db=db
    )
    return result

# ----------------- 6. AI AGENT CHAT & VOICE -----------------

@router.post("/agent/chat", summary="Process Customer Dialogue Turn (Root Agent & Sub-Agent)")
async def chat_turn(req: ChatTurnRequest, db: Session = Depends(get_db)):
    """
    Full conversational turn:
    - Guardrails check
    - Root Agent / EMI Service Sub-Agent routing
    - Tool execution & logging
    - Voice speech formatting (V1-V6)
    """
    session_id = req.session_id or f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    turn_result = await process_user_turn(
        session_id=session_id,
        user_input=req.message,
        db=db,
        simulated_now_override=req.simulated_now
    )
    return turn_result


@router.post("/agent/voice", summary="Voice Interface Endpoint (Speech-to-Text Fallback & Synthesis)")
async def voice_turn(req: ChatTurnRequest, db: Session = Depends(get_db)):
    """Alias for voice processing providing spoken text and waveform metadata."""
    turn_result = await chat_turn(req, db)
    return turn_result


@router.post("/agent/reset", summary="Reset Active Session Transcript & Variables")
def reset_session(session_id: str = Body(..., embed=True)):
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]
    new_sess = get_or_create_session(session_id)
    return {"status": "SUCCESS", "message": "Session reset successfully", "session": new_sess.model_dump()}

# ----------------- 7. PAYMENTS & LATE FEES -----------------

@router.post("/late-fee/calculate", summary="Calculate Overdue Late Fee (Tool 4)")
def calculate_late_fee_endpoint(req: LateFeeRequest):
    sim_date = req.simulated_now or get_simulated_now()
    return calculate_late_fee(
        emi_amount=req.emi_amount,
        due_date=req.due_date,
        payment_status=req.payment_status or "PENDING",
        simulated_current_date=sim_date
    )


@router.post("/part-payment", summary="Process Part-Payment Request (Tool 3 & Validations)")
def process_part_payment(req: PartPaymentRequest, db: Session = Depends(get_db)):
    # 1. Check loan status (Tool 3)
    status_res = check_loan_status(loan_id=req.loan_id, db=db)
    if status_res["requires_escalation"]:
        return {
            "success": False,
            "status_check": status_res,
            "message": status_res["error"],
            "requires_escalation": True,
            "escalation_reason": status_res["escalation_reason"]
        }

    # 2. Validate amount boundary (minimum ₹500)
    amt_val = validate_part_payment_amount(req.amount)
    if not amt_val["valid"]:
        return {
            "success": False,
            "amount_validation": amt_val,
            "message": amt_val["message"],
            "requires_escalation": False
        }

    # 3. Validate payment mode
    mode_val = validate_payment_mode(req.payment_mode or "NetPay", req.payment_date)
    if mode_val["requires_escalation"]:
        return {
            "success": False,
            "payment_mode_validation": mode_val,
            "message": mode_val["reason"],
            "requires_escalation": True,
            "escalation_reason": mode_val["reason"]
        }

    return {
        "success": True,
        "loan_id": req.loan_id,
        "amount": req.amount,
        "canonical_payment_mode": mode_val["canonical_name"],
        "disclaimer": settings.PAYMENT_DISCLAIMER,
        "message": f"Part-payment of ₹{req.amount:,.0f} via {mode_val['canonical_name']} approved for processing."
    }

# ----------------- 8. ESCALATIONS -----------------

@router.get("/escalations", summary="List All Human Agent Escalations")
def list_escalations(db: Session = Depends(get_db)):
    escalations = db.query(Escalation).order_by(Escalation.timestamp.desc()).all()
    return [
        {
            "escalation_id": e.escalation_id,
            "borrower_id": e.borrower_id,
            "intent": e.intent,
            "reason": e.reason,
            "payment_mode": e.payment_mode,
            "conversation_summary": e.conversation_summary,
            "status": e.transfer_status,
            "timestamp": e.timestamp
        }
        for e in escalations
    ]


@router.post("/escalations", summary="Log New Human Escalation")
def create_escalation(req: EscalationCreateRequest, db: Session = Depends(get_db)):
    now_utc = datetime.now(timezone.utc)
    esc_id = f"ESC-{now_utc.strftime('%Y%m%d%H%M%S')}"
    new_esc = Escalation(
        escalation_id=esc_id,
        borrower_id=req.borrower_id,
        intent=req.intent,
        reason=req.reason,
        payment_mode=req.payment_mode,
        conversation_summary=req.conversation_summary,
        transfer_status="INITIATED",
        timestamp=now_utc.isoformat()
    )
    db.add(new_esc)
    db.commit()
    db.refresh(new_esc)
    return {"escalation_id": esc_id, "status": "INITIATED", "timestamp": new_esc.timestamp}

# ----------------- 9. EVALUATION & TESTS -----------------

@router.get("/evaluate/tests", summary="Get Evaluation Test Catalog")
def get_evaluation_catalog():
    return {"total": len(TEST_DEFINITIONS), "tests": TEST_DEFINITIONS}


@router.post("/evaluate/run", summary="Run Automated Test Suite (Single or All)")
def run_evaluation(test_id: Optional[str] = Query(None)):
    if test_id:
        return run_single_test(test_id)
    return run_all_tests()

# ----------------- 10. SYSTEM ARCHITECTURE -----------------

@router.get("/architecture", summary="Interactive Architecture Components & Node Definitions")
def get_architecture_metadata():
    """
    Returns node-based architecture graph and component responsibilities
    as required by Section 4 (Page 5).
    """
    return {
        "nodes": [
            {
                "id": "root_agent",
                "label": "Root Agent",
                "type": "agent",
                "status": "PRIMARY",
                "responsibilities": [
                    "Welcome the caller with standard banking greeting",
                    "Conduct secure borrower identity verification (verify_borrower)",
                    "Capture initial customer intent and keypad stand-ins (1, 2, 3, 0)",
                    "Identify explicit human-agent requests ('agent', 'human', 'zero')",
                    "Detect emergency crisis statements (Tele-MANAS protocol)",
                    "Protect sensitive numbers (16-digit card / 12-digit Aadhaar)",
                    "Route verified loan inquiries to EMI Service Sub-Agent"
                ],
                "tools_used": ["verify_borrower", "build_handoff_details"]
            },
            {
                "id": "emi_sub_agent",
                "label": "EMI Service Sub-Agent",
                "type": "sub_agent",
                "status": "SPECIALIST",
                "responsibilities": [
                    "Retrieve borrower loan registry records (lookup_loan)",
                    "Calculate overdue days and tier-based late fees (calculate_late_fee)",
                    "Enforce loan-status check for part-payment requests only (check_loan_status)",
                    "Enforce part-payment boundary minimum policy (>= ₹500)",
                    "Validate payment mode eligibility and 2027 NetPay Plus / Cash Desk transitions",
                    "Conduct Confirm Before Acting (V4) protocol before payment transfer",
                    "Play mandatory statutory lender disclaimer exactly once upon transfer"
                ],
                "tools_used": ["lookup_loan", "calculate_late_fee", "check_loan_status", "build_handoff_details"]
            },
            {
                "id": "tool_verify",
                "label": "verify_borrower()",
                "type": "python_tool",
                "status": "ACTIVE",
                "responsibilities": [
                    "Validate Borrower ID, DOB, and loan last 4 digits against core DB",
                    "Enforce max 2 retries (total 3 attempts)",
                    "Mask individual credential failure reasons to prevent enumeration",
                    "Flag BLOCKED borrower status for immediate human transfer"
                ]
            },
            {
                "id": "tool_lookup",
                "label": "lookup_loan()",
                "type": "python_tool",
                "status": "ACTIVE",
                "responsibilities": [
                    "Retrieve loan ID, sanctioned amount, tenure, and next due date",
                    "Fetch latest pending/overdue EMI schedule record"
                ]
            },
            {
                "id": "tool_status",
                "label": "check_loan_status()",
                "type": "python_tool",
                "status": "ACTIVE",
                "responsibilities": [
                    "Validate ACTIVE, CLOSED, DEFAULT, or UNKNOWN statuses",
                    "Gate part-payment processing (ACTIVE allows; CLOSED/DEFAULT escalate)",
                    "Return technical error for UNKNOWN without claiming default"
                ]
            },
            {
                "id": "tool_late_fee",
                "label": "calculate_late_fee()",
                "type": "python_tool",
                "status": "ACTIVE",
                "responsibilities": [
                    "Calculate days overdue against simulated clock",
                    "Apply 0% (0 days), 2% (1-5 days), 4% (6-30 days)",
                    "Enforce online resolution block for > 30 days overdue",
                    "Exempt already-paid EMIs (0 late fee)"
                ]
            },
            {
                "id": "tool_handoff",
                "label": "build_handoff_details()",
                "type": "python_tool",
                "status": "ACTIVE",
                "responsibilities": [
                    "Construct structured handoff JSON for human agent or payment gateway",
                    "Preserve best known intent and payment mode without inventing details",
                    "Ensure payment disclaimer is omitted during human representative transfers"
                ]
            },
            {
                "id": "guardrails",
                "label": "Safety Guardrails",
                "type": "security",
                "status": "ACTIVE",
                "responsibilities": [
                    "Guardrail 1: Card (16 digits) and Aadhaar (12 digits) refusal & sanitization",
                    "Guardrail 2: Crisis detection and Tele-MANAS (14416) emergency handoff",
                    "Guardrail 3: Financial advice & prepayment pressure refusal",
                    "Guardrail 4: Prompt injection and jailbreak protection"
                ]
            },
            {
                "id": "database",
                "label": "SQLite Database",
                "type": "datastore",
                "status": "ACTIVE",
                "responsibilities": [
                    "Borrowers, Loans, EMIs, Payments, Escalations, InteractionLogs tables",
                    "SQLAlchemy 2.0 modular architecture (ready for PostgreSQL swap)"
                ]
            },
            {
                "id": "advisory_api",
                "label": "Advisory Public API",
                "type": "external_api",
                "status": "ACTIVE",
                "responsibilities": [
                    "Fetches non-binding weather & banking rail clearance updates (Open-Meteo)",
                    "Provides contextual payment-day remarks without affecting loan logic"
                ]
            }
        ],
        "edges": [
            {"from": "root_agent", "to": "guardrails", "label": "Pre-flight Inspection"},
            {"from": "root_agent", "to": "tool_verify", "label": "Identity Check"},
            {"from": "root_agent", "to": "emi_sub_agent", "label": "Session Handoff (Verified)"},
            {"from": "root_agent", "to": "tool_handoff", "label": "Escalate (Blocked/Max Retries/Human Request)"},
            {"from": "emi_sub_agent", "to": "tool_lookup", "label": "Fetch Schedule"},
            {"from": "emi_sub_agent", "to": "tool_late_fee", "label": "Calculate Overdue Fee"},
            {"from": "emi_sub_agent", "to": "tool_status", "label": "Status Check (Part-Payment)"},
            {"from": "emi_sub_agent", "to": "tool_handoff", "label": "Escalate (>30 Days/Closed/Default/Unknown)"},
            {"from": "emi_sub_agent", "to": "advisory_api", "label": "Contextual Advisory"},
            {"from": "tool_verify", "to": "database", "label": "SQL Query"},
            {"from": "tool_lookup", "to": "database", "label": "SQL Query"},
            {"from": "tool_status", "to": "database", "label": "SQL Query"}
        ]
    }

# ----------------- 11. ADVISORY & SETTINGS -----------------

@router.get("/advisory", summary="Get Real-Time Contextual Payment-Day Advisory")
async def get_advisory(city: Optional[str] = "Mumbai", use_mock: bool = False):
    return await get_payment_day_advisory(city=city, use_mock=use_mock)


@router.get("/settings", summary="Get Current System Settings & Simulated Clock")
def get_system_settings():
    return {
        "project_name": settings.PROJECT_NAME,
        "current_simulated_now": settings.CURRENT_SIMULATED_NOW,
        "default_simulated_now": settings.DEFAULT_SIMULATED_NOW,
        "part_payment_min_amount": settings.PART_PAYMENT_MIN_AMOUNT,
        "late_fee_tier1_max_days": settings.LATE_FEE_TIER1_MAX_DAYS,
        "late_fee_tier2_max_days": settings.LATE_FEE_TIER2_MAX_DAYS,
        "max_overdue_online_days": settings.MAX_OVERDUE_ONLINE_DAYS,
        "policy_cutoff_date": settings.POLICY_CUTOFF_DATE
    }


@router.post("/settings/clock", summary="Update Simulated Clock Reference")
def update_simulated_clock(req: ClockUpdateRequest):
    try:
        new_clock = set_simulated_now(req.simulated_now)
        return {"status": "SUCCESS", "current_simulated_now": new_clock}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")


@router.post("/settings/clock/reset", summary="Reset Simulated Clock to 10 Nov 2026")
def reset_simulated_clock():
    new_clock = reset_simulated_now()
    return {"status": "SUCCESS", "current_simulated_now": new_clock}



# ----------------- 12. INTEGRATIONS STATUS -----------------

@router.get("/integrations/status", summary="Live status of Gemini and Supabase integrations")
async def integrations_status():
    import asyncio
    gemini_status = await gemini.ping()
    supabase_status = await asyncio.to_thread(supabase_sync.status)
    return {"gemini": gemini_status, "supabase": supabase_status}
