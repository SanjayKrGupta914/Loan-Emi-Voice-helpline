"""
Backend Python Tools for SteadyHome Loan EMI Voice Helpline.
Contains 5 standalone, independently testable tools implementing strict business rules:
1. verify_borrower
2. lookup_loan
3. check_loan_status
4. calculate_late_fee
5. build_handoff_details
"""

import math
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings, get_simulated_now
from database.schema import Borrower, Loan, EMI, Escalation

def verify_borrower(
    borrower_id: str,
    date_of_birth: str,
    loan_last_four: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    TOOL 1: verify_borrower
    Verifies borrower identity against Borrower ID, DOB (YYYY-MM-DD), and last 4 digits of loan.
    Rules:
    - Never disclose which individual field was incorrect!
    - If borrower status is BLOCKED: immediately flag for human escalation.
    - Never reveal loan balance before successful verification.
    """
    if not borrower_id or not date_of_birth or not loan_last_four:
        return {
            "verified": False,
            "status": "FAILED",
            "borrower_id": None,
            "borrower_name": None,
            "error": "The provided credentials could not be verified. Please check your Borrower ID, date of birth, and the last 4 digits of your loan number.",
            "requires_escalation": False,
            "escalation_reason": None
        }

    # Clean inputs
    b_id = borrower_id.strip()
    dob = date_of_birth.strip()
    l_last_four = loan_last_four.strip()

    own_session = False
    if db is None:
        from app.models.database import SessionLocal
        db = SessionLocal()
        own_session = True

    try:
        borrower = db.query(Borrower).filter(Borrower.borrower_id == b_id).first()
        if not borrower:
            return {
                "verified": False,
                "status": "FAILED",
                "borrower_id": None,
                "borrower_name": None,
                "error": "The provided credentials could not be verified. Please check your Borrower ID, date of birth, and the last 4 digits of your loan number.",
                "requires_escalation": False,
                "escalation_reason": None
            }

        # Check blocked borrower rule:
        # If borrower status is BLOCKED, immediately escalate to a human agent.
        if borrower.status == "BLOCKED":
            return {
                "verified": False,
                "status": "BLOCKED",
                "borrower_id": borrower.borrower_id,
                "borrower_name": borrower.name,
                "error": "Your account requires assistance from a customer care representative.",
                "requires_escalation": True,
                "escalation_reason": f"Borrower {borrower.borrower_id} account status is BLOCKED in core banking."
            }

        # Check DOB match
        if borrower.date_of_birth != dob:
            return {
                "verified": False,
                "status": "FAILED",
                "borrower_id": None,
                "borrower_name": None,
                "error": "The provided credentials could not be verified. Please check your Borrower ID, date of birth, and the last 4 digits of your loan number.",
                "requires_escalation": False,
                "escalation_reason": None
            }

        # Check matching loan with last 4 digits
        matched_loan = None
        for loan in borrower.loans:
            if loan.loan_id.endswith(l_last_four):
                matched_loan = loan
                break

        if not matched_loan:
            return {
                "verified": False,
                "status": "FAILED",
                "borrower_id": None,
                "borrower_name": None,
                "error": "The provided credentials could not be verified. Please check your Borrower ID, date of birth, and the last 4 digits of your loan number.",
                "requires_escalation": False,
                "escalation_reason": None
            }

        return {
            "verified": True,
            "status": "SUCCESS",
            "borrower_id": borrower.borrower_id,
            "borrower_name": borrower.name,
            "loan_id": matched_loan.loan_id,
            "error": None,
            "requires_escalation": False,
            "escalation_reason": None
        }
    finally:
        if own_session:
            db.close()


def lookup_loan(
    borrower_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    TOOL 2: lookup_loan
    Retrieves primary active loan and latest EMI info for a verified borrower.
    Handles missing records cleanly.
    """
    if not borrower_id:
        return {
            "found": False,
            "loan_id": None,
            "loan_amount": None,
            "loan_status": None,
            "emi_amount": None,
            "next_due_date": None,
            "tenure_months": None,
            "interest_rate": None,
            "error": "Borrower ID is required for loan lookup."
        }

    own_session = False
    if db is None:
        from app.models.database import SessionLocal
        db = SessionLocal()
        own_session = True

    try:
        loan = db.query(Loan).filter(Loan.borrower_id == borrower_id.strip()).first()
        if not loan:
            return {
                "found": False,
                "loan_id": None,
                "loan_amount": None,
                "loan_status": None,
                "emi_amount": None,
                "next_due_date": None,
                "tenure_months": None,
                "interest_rate": None,
                "error": f"No active home loan records found for borrower ID {borrower_id}."
            }

        # Fetch latest pending/overdue EMI or last EMI
        latest_emi = db.query(EMI).filter(EMI.loan_id == loan.loan_id).order_by(EMI.due_date.desc()).first()

        return {
            "found": True,
            "loan_id": loan.loan_id,
            "loan_amount": loan.loan_amount,
            "loan_status": loan.loan_status,
            "emi_amount": loan.emi_amount,
            "next_due_date": loan.next_due_date,
            "tenure_months": loan.loan_tenure_months,
            "interest_rate": loan.interest_rate,
            "emi_id": latest_emi.emi_id if latest_emi else None,
            "payment_status": latest_emi.payment_status if latest_emi else "PENDING",
            "payment_mode": latest_emi.payment_mode if latest_emi else "AutoDebit",
            "error": None
        }
    finally:
        if own_session:
            db.close()


def check_loan_status(
    loan_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    TOOL 3: check_loan_status
    Checked for PART-PAYMENT requests only!
    Status rules:
    - ACTIVE: Allow the process to continue.
    - CLOSED: Escalate to human agent.
    - DEFAULT: Escalate to human agent.
    - UNKNOWN: Give a technical error message + escalate to a human agent. Never say the loan is in default.
    """
    if not loan_id:
        return {
            "loan_id": None,
            "status": "UNKNOWN",
            "can_part_pay": False,
            "error": "A technical error occurred while retrieving the loan record. Please hold while I connect you with an agent.",
            "requires_escalation": True,
            "escalation_reason": "Loan ID was missing or invalid during part-payment status check."
        }

    own_session = False
    if db is None:
        from app.models.database import SessionLocal
        db = SessionLocal()
        own_session = True

    try:
        loan = db.query(Loan).filter(Loan.loan_id == loan_id.strip()).first()
        if not loan:
            return {
                "loan_id": loan_id,
                "status": "UNKNOWN",
                "can_part_pay": False,
                "error": "A technical error occurred while retrieving your loan status. I am connecting you with a support representative.",
                "requires_escalation": True,
                "escalation_reason": f"Loan ID {loan_id} not found in database (UNKNOWN status)."
            }

        status = (loan.loan_status or "UNKNOWN").upper()

        if status == "ACTIVE":
            return {
                "loan_id": loan.loan_id,
                "status": "ACTIVE",
                "can_part_pay": True,
                "error": None,
                "requires_escalation": False,
                "escalation_reason": None
            }
        elif status == "CLOSED":
            return {
                "loan_id": loan.loan_id,
                "status": "CLOSED",
                "can_part_pay": False,
                "error": "This loan account is currently closed. Part-payments cannot be processed on closed loans.",
                "requires_escalation": True,
                "escalation_reason": f"Loan {loan.loan_id} is CLOSED; part-payment requested."
            }
        elif status == "DEFAULT":
            return {
                "loan_id": loan.loan_id,
                "status": "DEFAULT",
                "can_part_pay": False,
                "error": "Your loan account requires specialized support from our loan servicing team.",
                "requires_escalation": True,
                "escalation_reason": f"Loan {loan.loan_id} is in DEFAULT status; part-payment requested."
            }
        else: # UNKNOWN or any other unrecognized status
            return {
                "loan_id": loan.loan_id,
                "status": "UNKNOWN",
                "can_part_pay": False,
                "error": "A technical system error occurred while validating your loan status. Please wait while I connect you to an agent.",
                "requires_escalation": True,
                "escalation_reason": f"Loan {loan.loan_id} returned UNKNOWN status during part-payment check."
            }
    finally:
        if own_session:
            db.close()


def calculate_late_fee(
    emi_amount: float,
    due_date: str,
    payment_status: str = "PENDING",
    simulated_current_date: Optional[Any] = None
) -> Dict[str, Any]:
    """
    TOOL 4: calculate_late_fee
    Parameters:
    - emi_amount: Monthly EMI in INR
    - due_date: YYYY-MM-DD
    - payment_status: PAID, PENDING, OVERDUE
    - simulated_current_date: datetime or ISO string (defaults to simulated clock)

    Rules:
    - Days overdue = (simulated_now.date() - due_date).days
    - Overdue <= 0: No fee, online payment YES
    - Overdue 1-5 days: 2% of EMI, online payment YES (exactly 5 days belongs to 2%)
    - Overdue 6-30 days: 4% of EMI, online payment YES after late fee is paid (exactly 30 days belongs to 4%)
    - Overdue > 30 days: No online processing, human agent escalation
    - Round to nearest whole rupee.
    - Already-paid EMI has no late fee (0 rupees).
    """
    if simulated_current_date is None:
        sim_now = get_simulated_now()
    elif isinstance(simulated_current_date, str):
        sim_now = datetime.fromisoformat(simulated_current_date)
    else:
        sim_now = simulated_current_date

    # If already paid, late fee is 0
    if (payment_status or "").upper() == "PAID":
        return {
            "days_overdue": 0,
            "late_fee_amount": 0,
            "late_fee_percentage": 0.0,
            "can_process_online": True,
            "payment_status": "PAID",
            "message": "This EMI has already been paid in full. There is no outstanding late fee.",
            "requires_escalation": False,
            "escalation_reason": None
        }

    try:
        due_d = datetime.strptime(due_date.strip()[:10], "%Y-%m-%d").date()
    except Exception as e:
        return {
            "days_overdue": 0,
            "late_fee_amount": 0,
            "late_fee_percentage": 0.0,
            "can_process_online": False,
            "payment_status": payment_status,
            "message": f"Invalid due date format: {due_date}",
            "requires_escalation": True,
            "escalation_reason": f"Invalid due date provided: {due_date}"
        }

    sim_date = sim_now.date() if isinstance(sim_now, datetime) else sim_now
    delta_days = (sim_date - due_d).days

    if delta_days <= 0:
        # Not overdue yet or due today
        return {
            "days_overdue": 0,
            "late_fee_amount": 0,
            "late_fee_percentage": 0.0,
            "can_process_online": True,
            "payment_status": "PENDING",
            "message": "Your EMI is not overdue. No late fee applies.",
            "requires_escalation": False,
            "escalation_reason": None
        }
    elif 1 <= delta_days <= 5:
        # 1-5 days: 2% of EMI (exactly 5 days belongs to 2%)
        fee = round(emi_amount * 0.02)
        return {
            "days_overdue": delta_days,
            "late_fee_amount": fee,
            "late_fee_percentage": 2.0,
            "can_process_online": True,
            "payment_status": "OVERDUE",
            "message": f"Your EMI is {delta_days} days overdue. A 2% late fee of ₹{fee} applies. Online payment is supported.",
            "requires_escalation": False,
            "escalation_reason": None
        }
    elif 6 <= delta_days <= 30:
        # 6-30 days: 4% of EMI (exactly 30 days belongs to 4%)
        fee = round(emi_amount * 0.04)
        return {
            "days_overdue": delta_days,
            "late_fee_amount": fee,
            "late_fee_percentage": 4.0,
            "can_process_online": True,
            "payment_status": "OVERDUE",
            "message": f"Your EMI is {delta_days} days overdue. A 4% late fee of ₹{fee} applies. Online payment is permitted after paying the late fee.",
            "requires_escalation": False,
            "escalation_reason": None
        }
    else:
        # More than 30 days: No online processing, human agent escalation
        return {
            "days_overdue": delta_days,
            "late_fee_amount": round(emi_amount * 0.04),
            "late_fee_percentage": 4.0,
            "can_process_online": False,
            "payment_status": "OVERDUE",
            "message": f"Your EMI is {delta_days} days overdue. Accounts overdue by more than 30 days cannot be processed online and require human agent assistance.",
            "requires_escalation": True,
            "escalation_reason": f"EMI overdue by {delta_days} days (exceeds 30-day online resolution limit)."
        }


def validate_payment_mode(
    payment_mode: str,
    payment_date_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates payment mode according to Section 5.C:
    - AutoDebit: Supported.
    - NetPay: Supported. If payment date on or after 1 Jan 2027: called 'NetPay Plus'.
    - Branch Cash Desk: Supported up to 31 Dec 2026. Unsupported from 1 Jan 2027 onwards (human escalation).
    - KiteWallet: Discontinued. Never supported (human escalation).
    - The REQUESTED PAYMENT DATE determines eligibility, NOT today's date!
    """
    if not payment_mode:
        return {
            "supported": False,
            "canonical_name": None,
            "requires_escalation": True,
            "reason": "Payment mode not specified.",
            "disclaimer": None
        }

    mode_raw = payment_mode.strip()
    mode_lower = mode_raw.lower()

    # Determine reference payment date
    if payment_date_str:
        try:
            req_date = datetime.strptime(payment_date_str.strip()[:10], "%Y-%m-%d").date()
        except Exception:
            req_date = get_simulated_now().date()
    else:
        req_date = get_simulated_now().date()

    cutoff_2027 = date(2027, 1, 1)

    # 1. KiteWallet
    if "kitewallet" in mode_lower or "kite" in mode_lower:
        return {
            "supported": False,
            "canonical_name": "KiteWallet",
            "requires_escalation": True,
            "reason": "KiteWallet is discontinued and is no longer supported for loan repayments.",
            "disclaimer": None
        }

    # 2. Branch Cash Desk
    if "branch" in mode_lower or "cash" in mode_lower or "desk" in mode_lower:
        if req_date >= cutoff_2027:
            return {
                "supported": False,
                "canonical_name": "Branch Cash Desk",
                "requires_escalation": True,
                "reason": f"Branch Cash Desk payments are discontinued from 1 January 2027 onwards (supported only up to 31 December 2026; requested date: {req_date.isoformat()}).",
                "disclaimer": None
            }
        else:
            return {
                "supported": True,
                "canonical_name": "Branch Cash Desk",
                "requires_escalation": False,
                "reason": f"Branch Cash Desk is supported for dates up to 31 December 2026 (requested date: {req_date.isoformat()}).",
                "disclaimer": settings.PAYMENT_DISCLAIMER
            }

    # 3. NetPay / NetPay Plus
    if "netpay" in mode_lower or "net pay" in mode_lower:
        if req_date >= cutoff_2027:
            return {
                "supported": True,
                "canonical_name": "NetPay Plus",
                "requires_escalation": False,
                "reason": f"NetPay Plus is active and supported for payments on or after 1 January 2027.",
                "disclaimer": settings.PAYMENT_DISCLAIMER
            }
        else:
            return {
                "supported": True,
                "canonical_name": "NetPay",
                "requires_escalation": False,
                "reason": "NetPay is supported.",
                "disclaimer": settings.PAYMENT_DISCLAIMER
            }

    # 4. AutoDebit
    if "auto" in mode_lower or "debit" in mode_lower or "nach" in mode_lower or "ecs" in mode_lower:
        return {
            "supported": True,
            "canonical_name": "AutoDebit",
            "requires_escalation": False,
            "reason": "AutoDebit is supported.",
            "disclaimer": settings.PAYMENT_DISCLAIMER
        }

    # Unrecognized payment mode
    return {
        "supported": False,
        "canonical_name": mode_raw,
        "requires_escalation": True,
        "reason": f"Payment mode '{mode_raw}' is unsupported.",
        "disclaimer": None
    }


def validate_part_payment_amount(amount: float) -> Dict[str, Any]:
    """
    Validates part-payment amount rules:
    - Minimum ₹500 is accepted.
    - Below ₹500 (e.g. ₹499) is rejected.
    """
    if amount < 500.0:
        return {
            "valid": False,
            "amount": amount,
            "message": f"Part-payment of ₹{amount:,.0f} cannot be processed. The minimum permitted part-payment amount is ₹500.",
            "error_code": "AMOUNT_BELOW_MINIMUM"
        }
    return {
        "valid": True,
        "amount": amount,
        "message": f"Part-payment of ₹{amount:,.0f} satisfies the minimum amount policy.",
        "error_code": None
    }


def build_handoff_details(
    intent: str,
    payment_mode: Optional[str] = None,
    transfer_reason: str = "Customer requested human representative.",
    borrower_id: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    TOOL 5: build_handoff_details
    Parameters:
    - intent: Best known intent tag (e.g. DUE_DATE_ENQUIRY, PART_PAYMENT, LATE_FEE_ENQUIRY, HUMAN_AGENT_REQUEST)
    - payment_mode: Preserved known payment mode, or empty/None
    - transfer_reason: Clear professional reason for escalation
    - borrower_id: Borrower ID where permitted, or None
    - extra_context: Dictionary of non-sensitive context

    Rules:
    - Preserves known information.
    - Leaves unknown information empty/None.
    - NEVER invents missing details!
    - Does NOT play payment-mode disclaimer during human agent transfer.
    """
    now_utc = datetime.now(timezone.utc)
    handoff_payload = {
        "handoff_id": f"HO-{now_utc.strftime('%Y%m%d%H%M%S')}",
        "timestamp": now_utc.isoformat(),
        "intent": intent or "UNRESOLVED_INTENT",
        "payment_mode": payment_mode if payment_mode else None,
        "borrower_id": borrower_id if borrower_id else None,
        "transfer_reason": transfer_reason,
        "disclaimer_played": False,  # As required by Section 5.F: Do NOT play payment-mode disclaimer for human handoff
        "summary": f"Escalated to human agent desk. Reason: {transfer_reason}. Intent: {intent or 'N/A'}.",
        "context": extra_context or {}
    }
    return handoff_payload
