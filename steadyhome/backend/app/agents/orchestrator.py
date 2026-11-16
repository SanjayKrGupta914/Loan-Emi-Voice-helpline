"""
Orchestrator and Dialogue Management Engine for SteadyHome Voice Helpline.
Coordinates Root Agent and EMI Service Sub-Agent, tool invocations, state updates,
guardrail enforcement, voice speech formatting (V1-V6), and database logging.
Runs 100% locally with deterministic rule-based NLP and tool execution.
"""

import re
import uuid
from datetime import datetime, date, timezone

def get_utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings, get_simulated_now
from app.agents.state import ConversationState, ChatMessage, ToolExecutionEvent
from app.guardrails.safety import check_guardrails, sanitize_sensitive_data
from app.tools.loan_tools import (
    verify_borrower,
    lookup_loan,
    check_loan_status,
    calculate_late_fee,
    validate_payment_mode,
    validate_part_payment_amount,
    build_handoff_details
)
from database.schema import Escalation, InteractionLog
from app.services import gemini, supabase_sync

# In-memory session store (can also persist in DB)
SESSION_STORE: Dict[str, ConversationState] = {}

def get_or_create_session(session_id: Optional[str] = None) -> ConversationState:
    sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
    if sid not in SESSION_STORE:
        SESSION_STORE[sid] = ConversationState(
            session_id=sid,
            now_override=settings.CURRENT_SIMULATED_NOW,
            messages=[
                ChatMessage(
                    role="agent",
                    content="Welcome to SteadyHome. How may I help you today?",
                    spoken_text="Welcome to SteadyHome. How may I help you today?",
                    agent_name="Root Agent",
                    timestamp=get_utc_now_iso()
                )
            ]
        )
    return SESSION_STORE[sid]


def format_currency_speech(amount: float) -> str:
    """Formats amount naturally for voice speech, e.g. '39,052 rupees'."""
    return f"{int(amount):,} rupees"


def format_date_speech(date_str: str) -> str:
    """Formats date naturally for voice speech (e.g. 2026-11-15 -> 'the fifteenth of November twenty twenty-six')."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        day = dt.day
        suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        month_name = dt.strftime("%B")
        year_speech = "twenty twenty-six" if dt.year == 2026 else ("twenty twenty-seven" if dt.year == 2027 else str(dt.year))
        
        ordinals = {
            1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
            6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
            11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
            16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth",
            21: "twenty-first", 22: "twenty-second", 23: "twenty-third", 24: "twenty-fourth", 25: "twenty-fifth",
            26: "twenty-sixth", 27: "twenty-seventh", 28: "twenty-eighth", 29: "twenty-ninth", 30: "thirtieth",
            31: "thirty-first"
        }
        day_speech = ordinals.get(day, f"{day}{suffix}")
        return f"the {day_speech} of {month_name} {year_speech}"
    except Exception:
        return date_str


_DIGIT_WORDS = {"zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4",
                "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"}
_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}


def normalize_speech(text: str) -> str:
    """Turns speech-to-text artefacts into the written forms the parsers expect.

    'S H B O R one zero zero one' -> 'SH-BOR-1001'; '15 June 1985' / 'June 15th, 1985' -> '1985-06-15'.
    """
    t = text
    # Spelled-out / spaced borrower id: "SH BOR 1001", "s h b o r 1 0 0 1", "sh-bor one zero zero one"
    def _id(m: re.Match) -> str:
        digits = ""
        for tok in re.findall(r"[a-z]+|\d", m.group(1).lower()):
            digits += _DIGIT_WORDS.get(tok, tok if tok.isdigit() else "")
        return f"SH-BOR-{digits}" if len(digits) == 4 else m.group(0)
    t = re.sub(r"\bs[\s-]*h[\s-]*b[\s-]*o[\s-]*r[\s-]*((?:\d|zero|oh|one|two|three|four|five|six|seven|eight|nine)(?:[\s-]*(?:\d|zero|oh|one|two|three|four|five|six|seven|eight|nine)){3})\b",
               _id, t, flags=re.IGNORECASE)

    # Written-month dates
    def _iso(day: str, month: str, year: str) -> str:
        return f"{year}-{_MONTHS[month.lower()]:02d}-{int(day):02d}"
    months = "|".join(_MONTHS)
    t = re.sub(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({months})\s*,?\s+(\d{{4}})\b",
               lambda m: _iso(m.group(1), m.group(2), m.group(3)), t, flags=re.IGNORECASE)
    t = re.sub(rf"\b({months})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s+(\d{{4}})\b",
               lambda m: _iso(m.group(2), m.group(1), m.group(3)), t, flags=re.IGNORECASE)
    return t


def parse_credentials(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts Borrower ID, DOB (YYYY-MM-DD or DD/MM/YYYY), and loan last four from text."""
    text = normalize_speech(text)
    # Look for borrower id pattern (e.g. SH-BOR-1001 or BOR-1001 or 1001)
    b_match = re.search(r'\b(SH-BOR-\d{4})\b', text, re.IGNORECASE)
    borrower_id = b_match.group(1).upper() if b_match else None

    # Look for DOB (YYYY-MM-DD or DD-MM-YYYY)
    dob_match = re.search(r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b', text)
    dob = None
    if dob_match:
        dob = dob_match.group(1).replace('/', '-')
    else:
        # Check DD-MM-YYYY or DD/MM/YYYY
        dob_alt = re.search(r'\b(\d{2})[-/](\d{2})[-/](\d{4})\b', text)
        if dob_alt:
            dob = f"{dob_alt.group(3)}-{dob_alt.group(2)}-{dob_alt.group(1)}"

    # Look for last 4 digits of loan (explicit or implicit)
    l4_match = re.search(
        r'(?:loan(?:\s+(?:account|no\.?|number|ends?|ending))*(?:\s+(?:in|with|is))?|last\s*(?:4|four)(?:\s*digits?)?(?:\s+(?:is|are|of(?:\s+(?:my|the))?\s+loan(?:\s+number)?))?|digits?(?:\s+(?:is|are))?)\s*[:\-]?\s*(\d{4})\b',
        text, re.IGNORECASE)
    loan_last_four = l4_match.group(1) if l4_match else None
    if not loan_last_four:
        # Remove the borrower id and DOB, then take any remaining standalone 4-digit token
        remainder = re.sub(r'SH-BOR-\d{4}', ' ', text, flags=re.IGNORECASE)
        if dob:
            remainder = remainder.replace(dob, ' ')
        remainder = re.sub(r'\d{2}[-/]\d{2}[-/]\d{4}', ' ', remainder)
        tokens = re.findall(r'\b\d{4}\b', remainder)
        if tokens:
            loan_last_four = tokens[-1]

    return borrower_id, dob, loan_last_four


def parse_intent(text: str) -> Optional[str]:
    """Detects primary customer intent including keypad stand-ins 1, 2, 3."""
    t = text.lower().strip()

    # Keypad stand-in check (V6)
    if t in ["1", "one", "press 1", "option 1"]:
        return "DUE_DATE_ENQUIRY"
    if t in ["2", "two", "press 2", "option 2"]:
        return "PART_PAYMENT"
    if t in ["3", "three", "press 3", "option 3"]:
        return "LATE_FEE_ENQUIRY"
    if t in ["0", "zero", "press 0", "option 0"]:
        return "HUMAN_AGENT_REQUEST"

    # Intent keywords
    if any(k in t for k in ["due date", "when is my emi", "next emi", "due day", "bill date", "payment date", "when emi", "check my emi", "check emi", "my emi", "emi status", "know my emi"]):
        return "DUE_DATE_ENQUIRY"
    if any(k in t for k in ["part payment", "part-payment", "partial payment", "pay part", "prepay part", "advance part", "pay extra"]):
        return "PART_PAYMENT"
    if any(k in t for k in ["late fee", "penalty", "overdue charge", "overdue fee", "fine", "charges for delay", "late charge", "delay charge"]):
        return "LATE_FEE_ENQUIRY"
    if any(k in t for k in ["agent", "representative", "human", "someone", "operator", "customer service officer", "talk to person"]):
        return "HUMAN_AGENT_REQUEST"
    
    return None


def execute_escalation(
    state: ConversationState,
    reason: str,
    db: Session,
    intent: Optional[str] = None
) -> Tuple[str, str]:
    """Logs escalation in database and marks state as escalated."""
    esc_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"
    state.is_escalated = True
    state.transfer_reason = reason
    state.escalation_id = esc_id

    handoff = build_handoff_details(
        intent=intent or state.intent_tag or "UNRESOLVED_INTENT",
        payment_mode=state.payment_mode,
        transfer_reason=reason,
        borrower_id=state.borrower_id if state.verified else None
    )

    # Persist in DB
    escalation_entry = Escalation(
        escalation_id=esc_id,
        borrower_id=state.borrower_id if state.verified else None,
        intent=intent or state.intent_tag or "UNRESOLVED_INTENT",
        reason=reason,
        payment_mode=state.payment_mode,
        conversation_summary=f"Automated Voice Helpline Escalation. Session: {state.session_id}. Reason: {reason}",
        transfer_status="INITIATED",
        timestamp=get_utc_now_iso()
    )
    db.add(escalation_entry)
    db.commit()
    supabase_sync.push("escalations", {
        "escalation_id": esc_id,
        "borrower_id": escalation_entry.borrower_id,
        "intent": escalation_entry.intent,
        "reason": reason,
        "payment_mode": state.payment_mode,
        "conversation_summary": escalation_entry.conversation_summary,
        "transfer_status": "INITIATED",
        "timestamp": escalation_entry.timestamp,
    }, upsert=True)

    # Tool log
    state.tool_logs.append(
        ToolExecutionEvent(
            tool_name="build_handoff_details",
            arguments={"reason": reason, "intent": intent or state.intent_tag},
            result=handoff,
            agent_name=state.active_agent,
            timestamp=get_utc_now_iso()
        )
    )

    spoken = "Connecting you with a human representative now. Please hold while I transfer your call."
    text = f"Connecting you with a SteadyHome customer support representative now (Ref: {esc_id}). Reason: {reason}"
    return text, spoken


async def process_user_turn(
    session_id: str,
    user_input: str,
    db: Session,
    simulated_now_override: Optional[str] = None
) -> Dict[str, Any]:
    """Runs one dialogue turn, then mirrors the session to Supabase (when configured)."""
    result = await _process_user_turn(session_id, user_input, db, simulated_now_override)
    supabase_sync.sync_session(get_or_create_session(session_id))
    return result


async def _process_user_turn(
    session_id: str,
    user_input: str,
    db: Session,
    simulated_now_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main dialogue manager:
    1. Guardrails check (Crisis, Card/Aadhaar, Injection, Financial Advice)
    2. Silence & interruption handling
    3. Human agent transfer trigger check (Section 5.G: agent, representative, human, someone, zero)
    4. Borrower verification tracking (max 2 retries)
    5. Agent routing (Root Agent -> EMI Service Sub-Agent)
    6. EMI operations (Due-date, Late-fee, Part-payment)
    7. Payment mode validation & disclaimer management
    8. Speech-optimized formatting (V1-V6)
    """
    state = get_or_create_session(session_id)
    if simulated_now_override:
        state.now_override = simulated_now_override

    # Add customer message to transcript (sanitized)
    sanitized_input = sanitize_sensitive_data(user_input)
    state.messages.append(
        ChatMessage(
            role="customer",
            content=sanitized_input,
            spoken_text=sanitized_input,
            agent_name="Customer",
            timestamp=get_utc_now_iso()
        )
    )

    # V5: Silence handling
    if not user_input or not user_input.strip():
        reply = "Are you still there? Please let me know how I can assist you with your SteadyHome loan."
        state.messages.append(ChatMessage(
            role="agent",
            content=reply,
            spoken_text=reply,
            agent_name=state.active_agent,
            timestamp=get_utc_now_iso()
        ))
        return {
            "session_id": state.session_id,
            "response_text": reply,
            "spoken_text": reply,
            "active_agent": state.active_agent,
            "state": state.model_dump()
        }

    # STEP 1: Guardrail Checks
    guardrail_result = check_guardrails(user_input)
    if guardrail_result["triggered"]:
        resp_text = guardrail_result["response"]
        spoken = resp_text

        # Log guardrail event in database
        log_entry = InteractionLog(
            session_id=state.session_id,
            borrower_id=state.borrower_id,
            event_type="GUARDRAIL_TRIGGERED",
            agent_name=state.active_agent,
            details=f"Guardrail: {guardrail_result['guardrail_name']}",
            timestamp=get_utc_now_iso()
        )
        db.add(log_entry)
        db.commit()
        supabase_sync.push("interaction_logs", {
            "session_id": log_entry.session_id, "borrower_id": log_entry.borrower_id,
            "event_type": log_entry.event_type, "agent_name": log_entry.agent_name,
            "details": log_entry.details, "timestamp": log_entry.timestamp,
        })

        if guardrail_result["requires_escalation"]:
            execute_escalation(
                state,
                reason=guardrail_result["escalation_reason"],
                db=db,
                intent=guardrail_result["guardrail_name"]
            )

        state.messages.append(ChatMessage(
            role="agent",
            content=resp_text,
            spoken_text=spoken,
            agent_name=state.active_agent,
            timestamp=get_utc_now_iso(),
            metadata={"guardrail": guardrail_result["guardrail_name"]}
        ))

        return {
            "session_id": state.session_id,
            "response_text": resp_text,
            "spoken_text": spoken,
            "active_agent": state.active_agent,
            "guardrail_triggered": guardrail_result["guardrail_name"],
            "state": state.model_dump()
        }

    # STEP 2: Immediate Human Agent Request Check (Section 5.G)
    # If customer says: agent, representative, human, someone, zero -> immediately transfer
    clean_lower = user_input.lower().strip()
    human_keywords = ["agent", "representative", "human", "someone"]
    # Credentials spoken digit-by-digit ("S H B O R one zero zero one") must not read as keypad 0.
    spoken_free = re.sub(r'sh-bor-\d{4}', ' ', normalize_speech(clean_lower), flags=re.IGNORECASE)
    is_human_request = (
        any(re.search(r'\b' + re.escape(kw) + r'\b', spoken_free) for kw in human_keywords)
        or re.fullmatch(r'(?:(?:press|dial|option|number)\s+)?(?:zero|0)\.?', clean_lower) is not None
    )

    if is_human_request:
        state.intent_tag = "HUMAN_AGENT_REQUEST"
        text, spoken = execute_escalation(
            state,
            reason="Customer explicitly requested transfer to a human representative.",
            db=db,
            intent="HUMAN_AGENT_REQUEST"
        )
        state.messages.append(ChatMessage(
            role="agent",
            content=text,
            spoken_text=spoken,
            agent_name=state.active_agent,
            timestamp=get_utc_now_iso()
        ))
        return {
            "session_id": state.session_id,
            "response_text": text,
            "spoken_text": spoken,
            "active_agent": state.active_agent,
            "is_escalated": True,
            "state": state.model_dump()
        }

    # Gemini understands free-form / spoken phrasing; rule-based parsing below remains the fallback.
    nlu: Dict[str, Any] = {}
    needs_nlu = (
        state.awaiting_confirmation
        or parse_intent(user_input) is None
        or (not state.verified and not all(parse_credentials(user_input)))
        or state.intent_tag == "PART_PAYMENT"
    )
    if needs_nlu and gemini.is_enabled():
        nlu = await gemini.understand_utterance(user_input, state.awaiting_confirmation, state.intent_tag)
        if nlu:
            state.tool_logs.append(ToolExecutionEvent(
                tool_name="gemini_understand",
                arguments={"utterance": sanitized_input},
                result=nlu,
                agent_name=state.active_agent,
                timestamp=get_utc_now_iso()
            ))

    # STEP 3: Handle Confirmation If Awaiting Confirmation (V4)
    if state.awaiting_confirmation:
        yes_words = ["yes", "proceed", "confirm", "continue", "okay", "correct", "sure"]
        no_words = ["no", "cancel", "stop", "wait", "change"]
        said_yes = any(re.search(rf"\b{w}\b", clean_lower) for w in yes_words) or nlu.get("confirmation") == "yes"
        said_no = any(re.search(rf"\b{w}\b", clean_lower) for w in no_words) or nlu.get("confirmation") == "no"
        if said_yes and not said_no:
            state.awaiting_confirmation = False
            # Customer confirmed payment transfer:
            # Play short disclaimer exactly once (Section 5.F)
            state.disclaimer_played = True
            disclaimer = settings.PAYMENT_DISCLAIMER
            transfer_msg = f"{disclaimer} Transferring you to our secure payment gateway to complete your transaction."
            spoken = f"{disclaimer} Transferring you to our payment gateway now."
            state.messages.append(ChatMessage(
                role="agent",
                content=transfer_msg,
                spoken_text=spoken,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": transfer_msg,
                "spoken_text": spoken,
                "active_agent": state.active_agent,
                "state": state.model_dump()
            }
        elif said_no:
            state.awaiting_confirmation = False
            cancel_msg = "Payment transfer cancelled. How else can I assist you with your SteadyHome loan today?"
            state.messages.append(ChatMessage(
                role="agent",
                content=cancel_msg,
                spoken_text=cancel_msg,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": cancel_msg,
                "spoken_text": cancel_msg,
                "active_agent": state.active_agent,
                "state": state.model_dump()
            }

    # STEP 4: Intent Detection & Clarification Handling (Section 5.B)
    detected_intent = parse_intent(user_input)
    if not detected_intent and nlu.get("intent") in ("DUE_DATE_ENQUIRY", "PART_PAYMENT", "LATE_FEE_ENQUIRY"):
        detected_intent = nlu["intent"]
    if detected_intent == "HUMAN_AGENT_REQUEST" or nlu.get("intent") == "HUMAN_AGENT_REQUEST":
        state.intent_tag = "HUMAN_AGENT_REQUEST"
        text, spoken = execute_escalation(
            state,
            reason="Customer explicitly requested transfer to a human representative.",
            db=db,
            intent="HUMAN_AGENT_REQUEST"
        )
        state.messages.append(ChatMessage(role="agent", content=text, spoken_text=spoken,
                                          agent_name=state.active_agent, timestamp=get_utc_now_iso()))
        return {
            "session_id": state.session_id,
            "response_text": text,
            "spoken_text": spoken,
            "active_agent": state.active_agent,
            "is_escalated": True,
            "state": state.model_dump()
        }
    if detected_intent:
        state.intent_tag = detected_intent
        state.clarification_attempts = 0
    elif not state.intent_tag and not state.verified:
        # Check if caller provided credentials directly
        b_id, dob, l4 = parse_credentials(user_input)
        if not (b_id or dob or l4 or nlu.get("borrower_id") or nlu.get("date_of_birth") or nlu.get("loan_last_four")):
            state.clarification_attempts += 1
            if state.clarification_attempts >= 3:
                # Escalate on 3rd unclear attempt (Section 5.B: allow 2 clarification attempts, escalate if still unclear)
                text, spoken = execute_escalation(
                    state,
                    reason="Customer intent remained unclear after two clarification attempts.",
                    db=db,
                    intent="UNCLEAR_INTENT"
                )
                state.messages.append(ChatMessage(
                    role="agent",
                    content=text,
                    spoken_text=spoken,
                    agent_name=state.active_agent,
                    timestamp=get_utc_now_iso()
                ))
                return {
                    "session_id": state.session_id,
                    "response_text": text,
                    "spoken_text": spoken,
                    "active_agent": state.active_agent,
                    "is_escalated": True,
                    "state": state.model_dump()
                }
            else:
                clarify_msg = (
                    "I didn't quite catch that. You can say: '1' for EMI due date, '2' for part-payment, "
                    "'3' for late fee enquiry, or '0' to talk to an agent."
                )
                state.messages.append(ChatMessage(
                    role="agent",
                    content=clarify_msg,
                    spoken_text=clarify_msg,
                    agent_name=state.active_agent,
                    timestamp=get_utc_now_iso()
                ))
                return {
                    "session_id": state.session_id,
                    "response_text": clarify_msg,
                    "spoken_text": clarify_msg,
                    "active_agent": state.active_agent,
                    "state": state.model_dump()
                }

    # STEP 5: Verification Flow (Root Agent)
    if not state.verified:
        # Check if caller provided verification credentials
        b_id, dob, l4 = parse_credentials(user_input)
        b_id = b_id or nlu.get("borrower_id")
        dob = dob or nlu.get("date_of_birth")
        l4 = l4 or nlu.get("loan_last_four")
        if b_id:
            state.borrower_id = b_id
        if dob:
            state.dob = dob
        if l4:
            state.loan_last_four = l4

        if state.borrower_id and state.dob and state.loan_last_four:
            # Execute verify_borrower tool
            ver_res = verify_borrower(
                borrower_id=state.borrower_id,
                date_of_birth=state.dob,
                loan_last_four=state.loan_last_four,
                db=db
            )
            state.tool_logs.append(
                ToolExecutionEvent(
                    tool_name="verify_borrower",
                    arguments={"borrower_id": state.borrower_id, "dob": state.dob, "loan_last_four": state.loan_last_four},
                    result=ver_res,
                    agent_name="Root Agent",
                    timestamp=get_utc_now_iso()
                )
            )

            # Check for blocked status
            if ver_res["status"] == "BLOCKED":
                text, spoken = execute_escalation(
                    state,
                    reason=ver_res["escalation_reason"],
                    db=db,
                    intent=state.intent_tag or "VERIFICATION"
                )
                state.messages.append(ChatMessage(
                    role="agent",
                    content=text,
                    spoken_text=spoken,
                    agent_name="Root Agent",
                    timestamp=get_utc_now_iso()
                ))
                return {
                    "session_id": state.session_id,
                    "response_text": text,
                    "spoken_text": spoken,
                    "active_agent": state.active_agent,
                    "is_escalated": True,
                    "state": state.model_dump()
                }

            if ver_res["verified"]:
                state.verified = True
                state.borrower_name = ver_res.get("borrower_name")
                state.loan_id = ver_res.get("loan_id")
                state.verification_attempts = 0

                # Log handoff event: Root Agent -> EMI Service Sub-Agent
                state.active_agent = "EMI Service Sub-Agent"
                handoff_log = InteractionLog(
                    session_id=state.session_id,
                    borrower_id=state.borrower_id,
                    event_type="AGENT_HANDOFF",
                    agent_name="Root Agent",
                    details=f"Identity verified for {state.borrower_name}. Routing to EMI Service Sub-Agent.",
                    timestamp=get_utc_now_iso()
                )
                db.add(handoff_log)
                db.commit()
                supabase_sync.push("interaction_logs", {
                    "session_id": handoff_log.session_id, "borrower_id": handoff_log.borrower_id,
                    "event_type": handoff_log.event_type, "agent_name": handoff_log.agent_name,
                    "details": handoff_log.details, "timestamp": handoff_log.timestamp,
                })

                # Immediately proceed to fulfill customer intent
            else:
                state.verification_attempts += 1
                if state.verification_attempts >= 3:
                    # Allow 2 re-attempts after initial attempt (total 3 attempts) -> Escalate
                    text, spoken = execute_escalation(
                        state,
                        reason="Borrower verification failed after two re-attempts (3 total attempts).",
                        db=db,
                        intent="VERIFICATION_FAILURE"
                    )
                    state.messages.append(ChatMessage(
                        role="agent",
                        content=text,
                        spoken_text=spoken,
                        agent_name="Root Agent",
                        timestamp=get_utc_now_iso()
                    ))
                    return {
                        "session_id": state.session_id,
                        "response_text": text,
                        "spoken_text": spoken,
                        "active_agent": state.active_agent,
                        "is_escalated": True,
                        "state": state.model_dump()
                    }
                else:
                    # Never disclose which specific detail was incorrect!
                    retries_left = 3 - state.verification_attempts
                    err_msg = (
                        "The provided credentials could not be verified. Please check your Borrower ID, "
                        f"date of birth, and the last 4 digits of your loan number. You have {retries_left} attempt{'s' if retries_left > 1 else ''} remaining."
                    )
                    spoken_err = f"Verification failed. Please state your Borrower ID, date of birth, and the last four digits of your loan. You have {retries_left} attempts remaining."
                    state.messages.append(ChatMessage(
                        role="agent",
                        content=err_msg,
                        spoken_text=spoken_err,
                        agent_name="Root Agent",
                        timestamp=get_utc_now_iso()
                    ))
                    return {
                        "session_id": state.session_id,
                        "response_text": err_msg,
                        "spoken_text": spoken_err,
                        "active_agent": state.active_agent,
                        "state": state.model_dump()
                    }
        else:
            # Prompt caller for verification credentials
            prompt = (
                "Certainly. To proceed, I need to verify your identity. "
                "Please provide your Borrower ID, date of birth, and the last four digits of your loan number."
            )
            state.messages.append(ChatMessage(
                role="agent",
                content=prompt,
                spoken_text=prompt,
                agent_name="Root Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": prompt,
                "spoken_text": prompt,
                "active_agent": state.active_agent,
                "state": state.model_dump()
            }

    # STEP 6: Verified Sub-Agent Intent Processing (EMI Service Sub-Agent)
    # Lookup loan data for the borrower
    loan_info = lookup_loan(borrower_id=state.borrower_id, db=db)
    state.tool_logs.append(
        ToolExecutionEvent(
            tool_name="lookup_loan",
            arguments={"borrower_id": state.borrower_id},
            result=loan_info,
            agent_name="EMI Service Sub-Agent",
            timestamp=get_utc_now_iso()
        )
    )

    if not loan_info["found"]:
        text, spoken = execute_escalation(
            state,
            reason=f"No loan records found for borrower {state.borrower_id}.",
            db=db,
            intent=state.intent_tag
        )
        state.messages.append(ChatMessage(
            role="agent",
            content=text,
            spoken_text=spoken,
            agent_name="EMI Service Sub-Agent",
            timestamp=get_utc_now_iso()
        ))
        return {
            "session_id": state.session_id,
            "response_text": text,
            "spoken_text": spoken,
            "active_agent": state.active_agent,
            "state": state.model_dump()
        }

    state.loan_id = loan_info["loan_id"]
    state.emi_amount = loan_info["emi_amount"]
    state.due_date = loan_info["next_due_date"]
    state.payment_mode = loan_info.get("payment_mode", "AutoDebit")
    state.loan_status = loan_info.get("loan_status", "ACTIVE")

    current_intent = state.intent_tag or "DUE_DATE_ENQUIRY"

    # INTENT A: DUE_DATE_ENQUIRY
    if current_intent == "DUE_DATE_ENQUIRY":
        date_speech = format_date_speech(state.due_date)
        amt_speech = format_currency_speech(state.emi_amount)
        resp = (
            f"Thank you, {state.borrower_name}. Your next EMI of ₹{state.emi_amount:,.0f} "
            f"is due on {state.due_date}. Your registered payment mode is {state.payment_mode}."
        )
        spoken = f"Thank you, {state.borrower_name}. Your next EMI of {amt_speech} is due on {date_speech}. Your payment mode is {state.payment_mode}."
        state.messages.append(ChatMessage(
            role="agent",
            content=resp,
            spoken_text=spoken,
            agent_name="EMI Service Sub-Agent",
            timestamp=get_utc_now_iso()
        ))
        return {
            "session_id": state.session_id,
            "response_text": resp,
            "spoken_text": spoken,
            "active_agent": state.active_agent,
            "state": state.model_dump()
        }

    # INTENT B: LATE_FEE_ENQUIRY
    elif current_intent == "LATE_FEE_ENQUIRY":
        late_fee_res = calculate_late_fee(
            emi_amount=state.emi_amount,
            due_date=state.due_date,
            payment_status=loan_info.get("payment_status", "PENDING"),
            simulated_current_date=state.now_override
        )
        state.tool_logs.append(
            ToolExecutionEvent(
                tool_name="calculate_late_fee",
                arguments={
                    "emi_amount": state.emi_amount,
                    "due_date": state.due_date,
                    "payment_status": loan_info.get("payment_status"),
                    "simulated_date": state.now_override
                },
                result=late_fee_res,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            )
        )
        state.days_overdue = late_fee_res["days_overdue"]
        state.late_fee = late_fee_res["late_fee_amount"]

        if late_fee_res["requires_escalation"]:
            # More than 30 days overdue -> escalate to human agent
            text, spoken = execute_escalation(
                state,
                reason=late_fee_res["escalation_reason"],
                db=db,
                intent="LATE_FEE_ENQUIRY"
            )
            state.messages.append(ChatMessage(
                role="agent",
                content=text,
                spoken_text=spoken,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": text,
                "spoken_text": spoken,
                "active_agent": state.active_agent,
                "is_escalated": True,
                "state": state.model_dump()
            }

        msg = late_fee_res["message"]
        state.messages.append(ChatMessage(
            role="agent",
            content=msg,
            spoken_text=msg,
            agent_name="EMI Service Sub-Agent",
            timestamp=get_utc_now_iso()
        ))
        return {
            "session_id": state.session_id,
            "response_text": msg,
            "spoken_text": msg,
            "active_agent": state.active_agent,
            "state": state.model_dump()
        }

    # INTENT C: PART_PAYMENT
    elif current_intent == "PART_PAYMENT":
        # Rule D: check_loan_status is called for PART-PAYMENT ONLY!
        status_res = check_loan_status(loan_id=state.loan_id, db=db)
        state.tool_logs.append(
            ToolExecutionEvent(
                tool_name="check_loan_status",
                arguments={"loan_id": state.loan_id},
                result=status_res,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            )
        )

        if status_res["requires_escalation"]:
            text, spoken = execute_escalation(
                state,
                reason=status_res["escalation_reason"],
                db=db,
                intent="PART_PAYMENT"
            )
            # Give technical error message if UNKNOWN, never say loan is in default
            if status_res["status"] == "UNKNOWN":
                err_reply = "A technical error occurred while retrieving your loan status. Please hold while I connect you with an agent."
                text = err_reply
                spoken = err_reply

            state.messages.append(ChatMessage(
                role="agent",
                content=text,
                spoken_text=spoken,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": text,
                "spoken_text": spoken,
                "active_agent": state.active_agent,
                "is_escalated": True,
                "state": state.model_dump()
            }

        # Check part-payment amount
        amount_text = normalize_speech(user_input)
        amount_text = re.sub(r'SH-BOR-\d{4}|\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}', ' ', amount_text, flags=re.IGNORECASE)
        # Prefer a number tied to a currency word; otherwise drop the loan-ending digits and take the first number.
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)\s*(\d+(?:,\d+)*(?:\.\d+)?)|(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:₹|rs\b\.?|rupees?)', amount_text, re.IGNORECASE)
        if amount_match:
            amount_group = amount_match.group(1) or amount_match.group(2)
        else:
            _, _, ending = parse_credentials(user_input)
            leftover = re.sub(r'(?:loan\s+\w*\s*\w*\s*|last\s*(?:4|four)\s*(?:digits?)?\s*)' + re.escape(ending or "@@") + r'\b', ' ', amount_text, flags=re.IGNORECASE)
            fallback = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)', leftover)
            amount_group = fallback.group(1) if fallback else None
        amount_val = nlu.get("amount")
        if amount_val is None and amount_group:
            try:
                amount_val = float(amount_group.replace(',', ''))
            except Exception:
                pass

        if amount_val is not None:
            amt_res = validate_part_payment_amount(amount_val)
            if not amt_res["valid"]:
                # Rejected (< ₹500)
                rej_msg = amt_res["message"]
                state.messages.append(ChatMessage(
                    role="agent",
                    content=rej_msg,
                    spoken_text=rej_msg,
                    agent_name="EMI Service Sub-Agent",
                    timestamp=get_utc_now_iso()
                ))
                return {
                    "session_id": state.session_id,
                    "response_text": rej_msg,
                    "spoken_text": rej_msg,
                    "active_agent": state.active_agent,
                    "state": state.model_dump()
                }

            # Valid amount (>= ₹500)
            # Check requested payment mode if mentioned
            requested_mode = state.payment_mode or "AutoDebit"
            for mode_candidate in ["NetPay", "AutoDebit", "Branch Cash Desk", "KiteWallet"]:
                if mode_candidate.lower() in clean_lower:
                    requested_mode = mode_candidate
                    break
            else:
                requested_mode = nlu.get("payment_mode", requested_mode)

            mode_val = validate_payment_mode(requested_mode, state.due_date)
            state.payment_mode = mode_val.get("canonical_name", requested_mode)

            if mode_val["requires_escalation"]:
                text, spoken = execute_escalation(
                    state,
                    reason=mode_val["reason"],
                    db=db,
                    intent="PART_PAYMENT"
                )
                state.messages.append(ChatMessage(
                    role="agent",
                    content=text,
                    spoken_text=spoken,
                    agent_name="EMI Service Sub-Agent",
                    timestamp=get_utc_now_iso()
                ))
                return {
                    "session_id": state.session_id,
                    "response_text": text,
                    "spoken_text": spoken,
                    "active_agent": state.active_agent,
                    "is_escalated": True,
                    "state": state.model_dump()
                }

            # Rule V4: Confirm Before Acting
            # Read back: Borrower ID, Last 4 digits of loan, Due date. Wait for confirmation.
            state.awaiting_confirmation = True
            last_four = state.loan_id[-4:] if state.loan_id else "0000"
            date_spoken = format_date_speech(state.due_date)
            confirm_text = (
                f"You requested a part-payment of ₹{amount_val:,.0f} via {state.payment_mode}. "
                f"Before I proceed, please confirm: Borrower ID {state.borrower_id}, "
                f"loan ending in {last_four}, and next due date {state.due_date}. Should I proceed?"
            )
            confirm_spoken = (
                f"You requested a part-payment of {format_currency_speech(amount_val)} via {state.payment_mode}. "
                f"Please confirm: Borrower ID {state.borrower_id}, loan ending in {last_four}, "
                f"and next due date {date_spoken}. Should I proceed?"
            )
            state.messages.append(ChatMessage(
                role="agent",
                content=confirm_text,
                spoken_text=confirm_spoken,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": confirm_text,
                "spoken_text": confirm_spoken,
                "active_agent": state.active_agent,
                "state": state.model_dump()
            }
        else:
            # Ask for part payment amount
            prompt_amt = "Please state the part-payment amount you would like to pay towards your home loan. Note that the minimum amount is ₹500."
            state.messages.append(ChatMessage(
                role="agent",
                content=prompt_amt,
                spoken_text=prompt_amt,
                agent_name="EMI Service Sub-Agent",
                timestamp=get_utc_now_iso()
            ))
            return {
                "session_id": state.session_id,
                "response_text": prompt_amt,
                "spoken_text": prompt_amt,
                "active_agent": state.active_agent,
                "state": state.model_dump()
            }

    # Default fallback
    fallback = "I can assist you with your EMI due date, late fee calculation, or part-payment. Which would you like to enquire about?"
    state.messages.append(ChatMessage(
        role="agent",
        content=fallback,
        spoken_text=fallback,
        agent_name=state.active_agent,
        timestamp=get_utc_now_iso()
    ))
    return {
        "session_id": state.session_id,
        "response_text": fallback,
        "spoken_text": fallback,
        "active_agent": state.active_agent,
        "state": state.model_dump()
    }
