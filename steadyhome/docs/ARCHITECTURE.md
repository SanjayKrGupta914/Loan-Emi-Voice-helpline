# SteadyHome – AI Agent Architecture & System Specification
## Technical Architecture for Loan EMI Voice Helpline

---

## 1. SYSTEM OVERVIEW

SteadyHome's AI-Powered Loan EMI Voice Helpline is engineered as a two-tier agentic architecture operating over a local SQLite relational datastore. The system models a production Indian home-loan call-center environment with deterministic tool execution, identity verification, voice synthesis, compliance guardrails, and human escalation workflows.

```
+-----------------------------------------------------------------------------------------+
|                                    CLIENT LAYER                                         |
|  - Web Speech API (SpeechRecognition en-IN)   - Browser SpeechSynthesis (TTS en-IN)     |
|  - Interactive Helpline Console                - Direct Text Fallback                   |
+-----------------------------------------------------------------------------------------+
                                            │
                                            ▼
+-----------------------------------------------------------------------------------------+
|                                  SECURITY GATEWAY                                       |
|  - Guardrail 1: Card (16-digit) & Aadhaar (12-digit) Redaction and Refusal              |
|  - Guardrail 2: Crisis & Distress Detection (Tele-MANAS 14416 / 112 protocol)           |
|  - Guardrail 3: Prepayment & Financial Advice Refusal                                    |
|  - Guardrail 4: Prompt Injection & System Tampering Filter                              |
+-----------------------------------------------------------------------------------------+
                                            │
                                            ▼
+-----------------------------------------------------------------------------------------+
|                                    AI AGENT CORE                                        |
|                                                                                         |
|  +---------------------------------+          +--------------------------------------+  |
|  |           ROOT AGENT            |          |       EMI SERVICE SUB-AGENT          |  |
|  | - Welcomes Caller               |  Handoff | - Loan Registry Lookup               |  |
|  | - Identity Verification         | ───────> | - Late Fee Tiers (2% & 4%)           |  |
|  | - Intent Capture (Keypad 1,2,3) | (Verified| - Part-Payment Rules (>= ₹500)       |  |
|  | - Immediate Escalation ('zero') |  Session)| - Confirm Before Acting (V4)         |  |
|  +---------------------------------+          +--------------------------------------+  |
+-----------------------------------------------------------------------------------------+
                       │                                         │
                       ▼                                         ▼
+-----------------------------------------------------------------------------------------+
|                                 PYTHON BUSINESS TOOLS                                   |
|  1. verify_borrower()     - Validates 3-tuple credentials, flags BLOCKED status         |
|  2. lookup_loan()         - Retrieves loan record, EMI amount, next due date            |
|  3. check_loan_status()   - Gates part-payments (ACTIVE/CLOSED/DEFAULT/UNKNOWN)         |
|  4. calculate_late_fee()  - Computes overdue tiers, enforces 30-day online boundary     |
|  5. build_handoff_details - Packages non-sensitive handoff context for human desk       |
+-----------------------------------------------------------------------------------------+
                       │                                         │
                       ▼                                         ▼
+-------------------------------------+   +-----------------------------------------------+
|      SQLITE RELATIONAL DATASTORE     |   |         EXTERNAL ADVISORY INTEGRATION         |
| - Borrowers (25+ Scenarios)         |   | - Free Open-Meteo HTTPS JSON API              |
| - Loans & EMIs                      |   | - Contextual payment day weather & settlement |
| - Payments & Escalations Logs       |   | - Deterministic mock fallback for tests       |
+-------------------------------------+   +-----------------------------------------------+
```

---

## 2. ROOT AGENT SPECIFICATION (5 LABELLED BLOCKS)

1. **Role:** Primary customer-facing voice assistant for SteadyHome Home Loans.
2. **Persona:** Courteous, calm, efficient, strictly professional banking officer tone.
3. **Context:** Helpline intake point operating under simulated clock 10 November 2026, 09:00 AM IST.
4. **Task:** Greet caller, capture intent (enquiry, part-payment, late fee), execute borrower identity verification with `verify_borrower()`, listen for keypad stand-ins (1, 2, 3, 0), and hand off verified sessions cleanly to the EMI Service Sub-Agent.
5. **Constraints:** Never reveal loan balance before verification; never disclose which individual credential failed; enforce max 2 re-attempts; trigger immediate crisis script if self-harm is detected; escalate on explicit agent request without confirmation.

---

## 3. EMI SERVICE SUB-AGENT SPECIFICATION (5 LABELLED BLOCKS)

1. **Role:** Specialist home-loan EMI assistant dedicated exclusively to home loan EMI due dates, late fees, payment mode validations, and part-payment requests.
2. **Persona:** Precise, mathematically exact, empathetic yet strictly compliant with banking policies.
3. **Context:** Operating with verified borrowers under reference clock 10 November 2026.
4. **Task:** Capture EMI intent, query loan schedule via `lookup_loan()`, compute late fees with `calculate_late_fee()`, gate part-payment through `check_loan_status()`, validate part-payment amount >= ₹500, manage 2027 NetPay Plus / Cash Desk transitions, execute Confirm Before Acting (V4) protocol, and issue statutory payment disclaimers.
5. **Constraints:** Reject part-payments below ₹500; report technical error on UNKNOWN loan status without alleging default; block online resolution if overdue exceeds 30 days; play payment disclaimer exactly once upon transfer; never play disclaimer for human agent handoffs.

---

## 4. TEN MANDATORY CONVERSATION VARIABLES (SECTION 7)

| Variable | Type | Default | Description |
|---|---|---|---|
| `borrower_id` | `Optional[str]` | `None` | Verified borrower identifier (e.g. `"SH-BOR-1001"`) |
| `verified` | `bool` | `False` | Boolean flag indicating successful authentication |
| `payment_mode` | `Optional[str]` | `None` | Active payment channel (`"AutoDebit"`, `"NetPay"`, `"NetPay Plus"`, `"Branch Cash Desk"`) |
| `intent_tag` | `Optional[str]` | `None` | Classified intent (`"DUE_DATE_ENQUIRY"`, `"PART_PAYMENT"`, `"LATE_FEE_ENQUIRY"`, etc.) |
| `now_override` | `str` (ISO Datetime) | `"2026-11-10T09:00:00"` | Configurable simulated clock reference |
| `days_overdue` | `int` | `0` | Calculated days elapsed between due date and simulated clock |
| `transfer_reason` | `Optional[str]` | `None` | Specific reason recorded when call is escalated |
| `loan_status` | `Optional[str]` | `None` | Status of loan account (`"ACTIVE"`, `"CLOSED"`, `"DEFAULT"`, `"UNKNOWN"`) |
| `verification_attempts`| `int` | `0` | Counter for credential check failures (max 2 retries allowed) |
| `clarification_attempts`| `int`| `0` | Counter for ambiguous speech inputs (max 2 retries allowed) |

---

## 5. PYTHON BUSINESS TOOLS SPECIFICATION

### Tool 1: `verify_borrower()`
- **Signature:** `verify_borrower(borrower_id: str, date_of_birth: str, loan_last_four: str, db: Session) -> Dict[str, Any]`
- **Logic:** Performs strict 3-tuple validation. If account status is `"BLOCKED"`, returns escalation flag. For failed authentication, returns a generic error to prevent brute-force field enumeration.

### Tool 2: `lookup_loan()`
- **Signature:** `lookup_loan(borrower_id: str, db: Session) -> Dict[str, Any]`
- **Logic:** Retrieves primary loan ID, sanctioned principal, tenure, interest rate, and latest pending/overdue installment schedule.

### Tool 3: `check_loan_status()`
- **Signature:** `check_loan_status(loan_id: str, db: Session) -> Dict[str, Any]`
- **Logic:** Gating check executed **exclusively for part-payments**. Permits `"ACTIVE"` status; escalates `"CLOSED"` and `"DEFAULT"`; generates technical error for `"UNKNOWN"` without alleging default.

### Tool 4: `calculate_late_fee()`
- **Signature:** `calculate_late_fee(emi_amount: float, due_date: str, payment_status: str, simulated_current_date: datetime) -> Dict[str, Any]`
- **Logic:** Computes `days_overdue = (simulated_now - due_date).days`.
  - `<= 0 days`: 0% fee (Online: YES)
  - `1–5 days`: 2% fee (Online: YES; exactly 5 days belongs to 2%)
  - `6–30 days`: 4% fee (Online: YES after fee paid; exactly 30 days belongs to 4%)
  - `> 30 days`: Online resolution blocked; escalates to human agent.
  - Rounding to nearest whole rupee; exempts already-paid EMIs.

### Tool 5: `build_handoff_details()`
- **Signature:** `build_handoff_details(intent: str, payment_mode: Optional[str], transfer_reason: str, borrower_id: Optional[str]) -> Dict[str, Any]`
- **Logic:** Constructs structured JSON handoff context. Preserves available facts, leaves unknown fields empty, and guarantees payment disclaimer is omitted during human transfers.

---

## 6. SAFETY GUARDRAILS ARCHITECTURE

1. **Card & Aadhaar Protection:**
   - Regex pattern matches 16-digit card and 12-digit Aadhaar sequences.
   - Refuses storage, masks as `[REDACTED]`, and never echoes numbers in spoken audio or transcripts.
2. **Crisis Detection:**
   - Lexical matching on suicidal ideation, self-harm, and extreme distress.
   - Halts loan processing immediately and delivers mandatory statutory script referencing Tele-MANAS (14416) and 112.
3. **Financial Advice & Pressure Protection:**
   - Intercepts prepayment advice queries. Issues explicit refusal and offers human representative consultation.
4. **Harm & Prompt Injection Protection:**
   - Detects system prompt overrides, developer-mode triggers, and bulk extraction attempts.

---

## 7. VOICE REQUIREMENTS IMPLEMENTATION (V1 - V6)

- **V1 (Short):** Spoken output constrained to 1–2 short sentences (except statutory disclaimer and crisis script).
- **V2 (Plain Speech):** Text-to-speech sanitizer strips all asterisks, markdown syntax, tables, and emojis before calling `SpeechSynthesisUtterance`.
- **V3 (Natural Numbers):** Currencies formatted as rupees (`"39,052 rupees"`); dates rendered conversationally (`"the fifteenth of November twenty twenty-six"`).
- **V4 (Confirm Before Acting):** Before payment transfer, agent recites Borrower ID, last 4 digits of loan, and due date, awaiting caller confirmation.
- **V5 (Silence & Interruption):** Silence triggers gentle re-prompt. Caller speech immediately interrupts and cancels in-progress TTS audio (`synth.cancel()`).
- **V6 (Keypad Stand-in):** Voice and numeric stand-ins mapped directly: 1 = Due Date, 2 = Part-Payment, 3 = Late Fee, 0 = Immediate Human Transfer.

