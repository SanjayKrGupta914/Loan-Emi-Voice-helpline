# STEADYHOME – AI-POWERED LOAN EMI VOICE HELPLINE
## Final University Capstone Project Engineering Report

**Institution:** Department of Computer Science and Engineering  
**Project Title:** SteadyHome – AI-Powered Loan EMI Voice Helpline  
**Industry Vertical:** Indian Fintech & Retail Housing Finance  
**Academic Year:** 2026–2027  

---

## 1. ABSTRACT

In retail housing finance, home-loan borrowers frequently contact call centers to check monthly EMI due dates, enquire about late penalties on delayed installments, submit part-payments toward loan principal, and seek clarification on permissible repayment channels. Manual call-center handling of these repetitive inquiries results in lengthy hold times, high operational overhead, and inconsistent policy enforcement.

This capstone project presents **SteadyHome**, an intelligent, production-grade AI-powered voice helpline and internal management system for a retail home-loan institution. Built with a FastAPI backend, a React/TypeScript/Tailwind CSS frontend modeled after modern Indian fintech dashboards, and an SQLite core banking database, SteadyHome implements a two-tier conversational architecture featuring a **Root Agent** and an **EMI Service Sub-Agent**. The system enforces deterministic banking rules across five standalone Python tools, operates under a simulated reference clock (10 November 2026), enforces four safety guardrails (sensitive credential redaction, mental health crisis intervention via Tele-MANAS, non-advisory prepayment neutrality, and prompt injection defense), and supports natural voice conversations using the Web Speech API.

An automated test suite comprising 35 unit, integration, boundary, and safety tests confirms 100% adherence to institutional policy across 25+ real customer profiles.

---

## 2. INTRODUCTION

Retail home loans represent long-term financial commitments spanning 15 to 30 years. Customer support helplines serve as critical operational touchpoints where borrowers interact with financial institutions regarding monthly repayment obligations, clearance delays, and principal prepayments.

Recent advances in speech recognition, text-to-speech synthesis, and agentic workflows offer financial institutions the opportunity to automate high-volume inquiries while maintaining compliance with Reserve Bank of India (RBI) consumer protection directives and digital lending standards. SteadyHome demonstrates how conversational voice agents can be safely deployed with strict business rules, deterministic tool execution, and clear human escalation pathways.

---

## 3. PROBLEM STATEMENT

Traditional customer support systems in mortgage finance face four fundamental challenges:

1. **High Call Volumes and Wait Times:** Over 70% of helpline calls pertain to routine inquiries: checking next EMI dates, calculating overdue late charges, or confirming supported payment modes.
2. **Human Agent Error in Calculation:** Manual computation of tiered late fees (e.g., 2% for 1–5 days, 4% for 6–30 days) and handling payment mode cutoff transitions (such as the discontinuation of Branch Cash Desks post-2026) introduce costly discrepancies.
3. **Data Security and Privacy Risks:** Call center agents frequently handle sensitive 16-digit card numbers or full 12-digit Aadhaar identifiers, exposing customers to identity theft and regulatory non-compliance.
4. **Vulnerability to Customer Distress:** Borrowers under severe financial stress may voice acute anxiety or suicidal ideation. Traditional IVRs and superficial chatbots lack specialized protocols to intercept crisis signals and provide immediate emergency care referrals.

---

## 4. PROJECT OBJECTIVES

The SteadyHome capstone project aimed to design, engineer, and validate:

1. A secure identity verification mechanism requiring a 3-tuple match (Borrower ID, Date of Birth, and Loan Last 4 Digits) without leaking failure reasons to prevent brute-force enumeration.
2. A two-tier conversational agent topology featuring a primary customer-facing Root Agent and a specialized EMI Service Sub-Agent.
3. Five independent, unit-tested Python tools implementing exact financial business rules for overdue calculations, part-payment validation, and structured handoff packaging.
4. Four institutional safety guardrails addressing card/Aadhaar protection, crisis intervention, financial advice refusal, and prompt injection defense.
5. An interactive, white fintech web interface providing live call-center audio controls, customer portfolio management, and an automated evaluation test runner.

---

## 5. PROPOSED SOLUTION

SteadyHome addresses the operational challenges through an integrated full-stack architecture:

- **Stateful Conversational Manager:** Tracks 10 mandatory conversation variables (including verification state, intent tags, overdue days, and attempt counters).
- **Simulated Clock Engine:** Decouples date calculations from the host operating system, establishing a configurable reference time of **10 November 2026, 09:00 AM IST** to ensure boundary test reproducibility.
- **Natural Voice Interface (V1–V6):** Provides concise 1–2 sentence spoken responses, conversational number and currency formatting, "Confirm Before Acting" verification prior to payment gateway transfers, gentle prompts upon caller silence, and barge-in interruption handling.
- **Real-Time Contextual Advisory:** Integrates with a free public HTTPS JSON API (Open-Meteo) to provide non-binding regional weather and settlement clearing updates.

---

## 6. SYSTEM ARCHITECTURE

```
+-----------------------------------------------------------------------------------+
|                                 STEADYHOME CLIENT                                 |
|   React 18 + TypeScript + Tailwind CSS (White Fintech UI inspired by Razorpay)    |
|   Web Speech API (SpeechRecognition + SpeechSynthesis) + Audio Waveform Visualizer|
+-----------------------------------------------------------------------------------+
                                          │
                            REST APIs / JSON Payloads
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|   - CORS Middleware, Pydantic Schema Validation, Session State Store              |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                             AGENT & SAFETY PIPELINE                               |
|   [1] Guardrails Inspection: Card/Aadhaar Redaction, Crisis, Prompt Injection     |
|   [2] Root Agent: Greetings, Identity Authentication, Keypad Handling (1,2,3,0)   |
|   [3] Agent Handoff: Secure session transfer to EMI Service Sub-Agent             |
|   [4] EMI Sub-Agent: Due Date Enquiry, Late Fee Calculation, Part-Payments        |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                              PYTHON BUSINESS TOOLS                                |
|   verify_borrower()  │  lookup_loan()  │  check_loan_status()                     |
|   calculate_late_fee()  │  validate_payment_mode()  │  build_handoff_details()     |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                             DATA & EXTERNAL SERVICES                              |
|   SQLite Relational DB (SQLAlchemy 2.0 ORM)  │  Open-Meteo Public Weather API     |
+-----------------------------------------------------------------------------------+
```

---

## 7. IMPLEMENTATION DETAILS

### 7.1 Backend Technology Stack
- **Framework:** FastAPI (Python 3.14) with asynchronous endpoint handlers.
- **Data Modeling:** SQLAlchemy 2.0 ORM over SQLite 3 with clean separation across `Borrower`, `Loan`, `EMI`, `Payment`, `Escalation`, and `InteractionLog` models.
- **Validation:** Pydantic v2 schemas enforcing strict typing on incoming and outgoing payloads.

### 7.2 Frontend Technology Stack
- **Framework:** React 18, Vite, and TypeScript.
- **Styling:** Custom Tailwind CSS configuration using a corporate white palette (`#FFFFFF` background, `#F7F8FA` secondary, `#315E9E` primary blue, `#24865B` success green, `#D99A32` warning orange, `#D9534F` danger red).
- **Visualizations:** Recharts for monthly EMI collection trends, payment mode distributions, and loan status shares.

---

## 8. AI AGENT WORKFLOW & DIALOGUE MANAGEMENT

Both agents implement strict 5-block labelled instructions:
1. **Role**  
2. **Persona**  
3. **Context**  
4. **Task**  
5. **Constraints**

### Workflow Sequence:
1. **Intake & Greeting:** Root Agent greets the caller: *"Welcome to SteadyHome. How may I help you today?"*
2. **Intent & Stand-ins:** Analyzes spoken input or keypad press (`1` for Due Date, `2` for Part-Payment, `3` for Late Fee, `0` for Immediate Representative).
3. **Identity Verification:** Requires Borrower ID, DOB (YYYY-MM-DD), and loan last 4 digits. If status is `BLOCKED`, the session immediately escalates. Enforces a maximum of two re-attempts (3 attempts total).
4. **Handoff:** Transits cleanly to the EMI Service Sub-Agent with verified context.
5. **EMI Execution:**
   - *Due Date:* Retrieves next installment and payment mode.
   - *Late Fee:* Computes days elapsed against simulated clock. Tiers: 0% (0 days), 2% (1–5 days), 4% (6–30 days), and blocks online resolution if > 30 days overdue.
   - *Part-Payment:* Checks loan status (must be `ACTIVE`; escalates `CLOSED`, `DEFAULT`, or `UNKNOWN`). Rejects amounts `< ₹500`.
   - *Mode Validation:* Upgrades NetPay to `NetPay Plus` on or after 1 Jan 2027; disallows Branch Cash Desk post-31 Dec 2026; rejects KiteWallet permanently.
6. **Confirmation & Disclaimer:** Conducts Confirm Before Acting (reads back ID, loan last 4, due date). On confirmation, delivers the mandatory statutory disclaimer: *"Please note that applicable fees and payment receipts are subject to your lender's terms and conditions."*

---

## 9. SAFETY GUARDRAILS IMPLEMENTATION

1. **Card and Aadhaar Protection:** Masked via regex patterns and redacted as `[REDACTED]`. The assistant refuses storage and avoids repeating the numbers.
2. **Crisis Detection:** Scans for keywords related to self-harm or hopelessness. When triggered, delivers the exact mandatory script:
   > *"I'm really sorry you're going through this. You are not alone, and help is available. If you are in immediate danger, please call 112 now. You can also call Tele-MANAS on 14416, free and open at all hours, to talk to a trained counsellor. I'm connecting you with a person now."*
3. **Financial Advice Protection:** Refuses prepayment recommendations and transfers the borrower to a human advisor.
4. **Prompt Injection Protection:** Refuses developer-mode instructions, system overrides, and data dumps.

---

## 10. TESTING METHODOLOGY

SteadyHome incorporates an automated evaluation engine executing tests across five distinct categories:
- **Golden Tests (10):** End-to-end happy paths for verification, due date lookup, overdue calculations, and payment mode validations.
- **Scenario Tests (6):** Real-world operational scenarios including Cash Desk cutoff, KiteWallet rejection, closed loans, and explicit human transfer requests.
- **Boundary Tests (4):** Critical mathematical limits (exactly 5 days overdue = 2%, exactly 30 days overdue = 4%, part-payment of ₹500 accepted, part-payment of ₹499 rejected).
- **Safety Tests (3):** Verification of Card/Aadhaar redaction, crisis detection script accuracy, and financial advice neutral refusals.
- **Negative Tests (2):** Blocked borrower authentication rejection and overdue exceeding 30 days blocking online clearance.

---

## 11. RESULTS AND FINDINGS

Execution of the full automated Pytest test suite yielded **35 passed tests out of 35** (100% pass rate) with zero regressions:

```
tests/test_api.py::test_root_endpoint PASSED
tests/test_api.py::test_dashboard_endpoint PASSED
tests/test_api.py::test_borrowers_endpoints PASSED
tests/test_api.py::test_verify_endpoint PASSED
tests/test_api.py::test_agent_chat_dialogue PASSED
tests/test_api.py::test_evaluation_run_all PASSED
tests/test_api.py::test_architecture_endpoint PASSED
tests/test_guardrails.py::test_card_number_guardrail PASSED
tests/test_guardrails.py::test_aadhaar_number_guardrail PASSED
tests/test_guardrails.py::test_crisis_detection_exact_script PASSED
tests/test_guardrails.py::test_financial_advice_refusal PASSED
tests/test_guardrails.py::test_prompt_injection_detection PASSED
tests/test_late_fee.py::test_zero_days_overdue PASSED
tests/test_late_fee.py::test_three_days_overdue_tier1 PASSED
tests/test_late_fee.py::test_exactly_five_days_overdue_boundary PASSED
tests/test_late_fee.py::test_fifteen_days_overdue_tier2 PASSED
tests/test_late_fee.py::test_exactly_thirty_days_overdue_boundary PASSED
tests/test_late_fee.py::test_over_thirty_days_escalation PASSED
tests/test_late_fee.py::test_already_paid_emi PASSED
tests/test_loan_status.py::test_active_loan_status_check PASSED
tests/test_loan_status.py::test_closed_loan_status_escalation PASSED
tests/test_loan_status.py::test_default_loan_status_escalation PASSED
tests/test_loan_status.py::test_unknown_loan_status_technical_error PASSED
tests/test_payment_modes.py::test_autodebit_supported PASSED
tests/test_payment_modes.py::test_netpay_before_2027 PASSED
tests/test_payment_modes.py::test_netpay_plus_after_2027 PASSED
tests/test_payment_modes.py::test_branch_cash_desk_active_until_31_dec_2026 PASSED
tests/test_payment_modes.py::test_branch_cash_desk_discontinued_from_1_jan_2027 PASSED
tests/test_payment_modes.py::test_kitewallet_permanently_discontinued PASSED
tests/test_payment_modes.py::test_part_payment_boundary_500_accepted PASSED
tests/test_payment_modes.py::test_part_payment_boundary_499_rejected PASSED
tests/test_verification.py::test_successful_borrower_verification PASSED
tests/test_verification.py::test_blocked_borrower_escalation PASSED
tests/test_verification.py::test_incorrect_credentials_non_disclosure PASSED
tests/test_verification.py::test_nonexistent_borrower PASSED
============================== 35 passed in 0.31s ==============================
```

### Visual Verification Evidence Placeholders:
- `[SCREENSHOT: SteadyHome Operations Overview Dashboard]`
- `[SCREENSHOT: AI Voice Helpline Call Center Interface with Active Waveform]`
- `[SCREENSHOT: Interactive Agent Architecture Topology and Inspector]`
- `[SCREENSHOT: Automated Evaluation Suite Results with 100% Pass Percentage]`
- `[DIAGRAM: CX Agent Studio Root Agent and Sub-Agent Flowchart Integration]`

---

## 12. LIMITATIONS & FUTURE WORK

1. **Browser Voice Engine Dependency:** Web Speech API behavior depends on browser-level speech recognition engines (Google Chrome / Chromium). While a functional text-fallback is provided, future work will integrate server-side streaming models (e.g. Whisper / Conformer).
2. **PostgreSQL Migration:** The current SQLite database provides zero-dependency local execution; production deployment will target managed PostgreSQL with connection pooling.
3. **Multi-Lingual Audio Support:** Current voice capabilities operate in English (India). Expanding to Hindi, Marathi, Tamil, and Telugu will broaden accessibility across regional borrower demographics.

---

## 13. CONCLUSION

The SteadyHome Loan EMI Voice Helpline capstone project successfully demonstrates an enterprise-grade, regulation-compliant conversational AI solution for Indian retail home loans. By decoupling business logic into five standalone Python tools, implementing a multi-agent hierarchy with labelled instruction blocks, enforcing strict consumer guardrails, and presenting a polished fintech user interface, SteadyHome bridges the gap between theoretical AI research and practical banking automation.

