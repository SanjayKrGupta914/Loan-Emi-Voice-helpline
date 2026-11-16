# SteadyHome – Requirements and Fictional Test Dataset
## Comprehensive University Capstone Specification

---

## 1. USER STORIES AND GIVEN / WHEN / THEN ACCEPTANCE CRITERIA

### User Story 1: Secure Borrower Verification (US-01)
**As a** home-loan customer calling the SteadyHome helpline,  
**I want** my identity verified using my Borrower ID, Date of Birth, and the last 4 digits of my loan number,  
**So that** my confidential loan balance and payment schedule remain protected from unauthorized disclosure.

- **Acceptance Criteria 1.1 (Valid Credentials):**
  - **Given** an ACTIVE borrower with Borrower ID `"SH-BOR-1001"`, Date of Birth `"1985-06-15"`, and Loan Number ending in `"1001"`,
  - **When** the caller provides these credentials in full or sequentially,
  - **Then** the system must invoke `verify_borrower()`, set `verified = True`, and transition from the Root Agent to the EMI Service Sub-Agent.

- **Acceptance Criteria 1.2 (Security Non-Disclosure of Specific Failed Field):**
  - **Given** a caller providing incorrect DOB or loan digits,
  - **When** `verify_borrower()` evaluates the input,
  - **Then** the system must return a generic verification error without disclosing which individual credential failed.

- **Acceptance Criteria 1.3 (Blocked Borrower Escalation):**
  - **Given** borrower `"SH-BOR-1002"` whose status is `"BLOCKED"` in the core database,
  - **When** the borrower attempts verification,
  - **Then** the system must refuse online automated service and immediately transfer the call to a human representative.

- **Acceptance Criteria 1.4 (Two Re-attempts Rule):**
  - **Given** an unverified caller attempting authentication,
  - **When** the caller fails authentication 3 consecutive times (initial attempt + 2 re-attempts),
  - **Then** the session must escalate to a human agent with reason `"Borrower verification failed after two re-attempts"`.

---

### User Story 2: EMI Due Date Enquiry (US-02)
**As a** verified borrower,  
**I want** to ask when my next EMI installment is due and check my registered payment mode,  
**So that** I can ensure sufficient bank balance prior to the clearing cycle.

- **Acceptance Criteria 2.1:**
  - **Given** verified borrower `"SH-BOR-1001"` on loan `"SH-LN-1001"`,
  - **When** the caller asks "When is my EMI due?" or speaks/presses `"1"`,
  - **Then** the system must invoke `lookup_loan()` and state the next due date (`15 November 2026`), amount (`₹39,052`), and registered payment mode (`AutoDebit`) in natural spoken English.

- **Acceptance Criteria 2.2:**
  - **Given** an unverified caller asking for their due date,
  - **When** the intent is detected,
  - **Then** the system must withhold loan information until identity verification is successfully completed.

---

### User Story 3: Late Fee Calculation and Overdue Tiers (US-03)
**As a** borrower whose installment is delayed,  
**I want** an exact, rule-based calculation of applicable late fees,  
**So that** I know the penalty amount and whether I can clear my balance online.

- **Acceptance Criteria 3.1 (0 Days Overdue):**
  - **Given** an EMI due today or in the future evaluated on simulated date `10 November 2026`,
  - **When** `calculate_late_fee()` is executed,
  - **Then** late fee percentage must be `0.0%`, late fee amount must be `₹0`, and online clearance must be permitted.

- **Acceptance Criteria 3.2 (1–5 Days Overdue):**
  - **Given** an EMI overdue between 1 and 5 days (e.g. Due 2026-11-05, exactly 5 days),
  - **When** `calculate_late_fee()` is executed,
  - **Then** late fee must be calculated as exactly `2%` of EMI amount rounded to the nearest whole rupee, and online clearance is permitted.

- **Acceptance Criteria 3.3 (6–30 Days Overdue):**
  - **Given** an EMI overdue between 6 and 30 days (e.g. Due 2026-10-11, exactly 30 days),
  - **When** `calculate_late_fee()` is executed,
  - **Then** late fee must be calculated as exactly `4%` of EMI amount rounded to the nearest whole rupee, and online clearance is permitted after paying the fee.

- **Acceptance Criteria 3.4 (> 30 Days Overdue Escalation):**
  - **Given** an EMI overdue by more than 30 days (e.g. Due 2026-10-06, 35 days),
  - **When** `calculate_late_fee()` is executed,
  - **Then** `can_process_online` must be `False`, and the system must transfer the caller to a human agent.

- **Acceptance Criteria 3.5 (Already-Paid Exemption):**
  - **Given** an EMI with status `"PAID"`,
  - **When** late fee enquiry is made,
  - **Then** overdue days must be `0` and late fee must be `₹0`.

---

### User Story 4: Part-Payment Processing and Minimum Threshold (US-04)
**As a** verified borrower with surplus liquidity,  
**I want** to make a partial prepayment toward my home loan principal,  
**So that** I can reduce my outstanding balance and tenure.

- **Acceptance Criteria 4.1 (Loan Status Gatekeeping):**
  - **Given** a borrower initiating a part-payment,
  - **When** `check_loan_status()` is called,
  - **Then** the process must continue ONLY if status is `"ACTIVE"`. If `"CLOSED"` or `"DEFAULT"`, it must escalate. If `"UNKNOWN"`, it must issue a technical error message and escalate without declaring default.

- **Acceptance Criteria 4.2 (Minimum Amount Threshold ₹500):**
  - **Given** an active loan,
  - **When** the customer requests a part-payment of `₹499`,
  - **Then** the system must reject the request and cite the mandatory minimum threshold of `₹500`.
  - **When** the customer requests `₹500`,
  - **Then** the system must accept and proceed.

---

### User Story 5: Payment Mode Transitions Across 1 January 2027 (US-05)
**As an** operations auditor,  
**I want** the voice helpline to enforce payment mode sunset policies based on requested payment date,  
**So that** discontinued payment channels are not offered to customers.

- **Acceptance Criteria 5.1 (AutoDebit):**
  - Supported for all dates.

- **Acceptance Criteria 5.2 (NetPay vs NetPay Plus):**
  - Supported as `"NetPay"` before `1 January 2027`.
  - Automatically canonically upgraded to `"NetPay Plus"` on or after `1 January 2027`.

- **Acceptance Criteria 5.3 (Branch Cash Desk Discontinuation):**
  - Supported for dates up to `31 December 2026`.
  - Unsupported for dates on or after `1 January 2027`, triggering human escalation.

- **Acceptance Criteria 5.4 (KiteWallet Permanent Discontinuation):**
  - Discontinued across all dates; immediately triggers human agent escalation.

---

### User Story 6: Statutory Disclaimer & Confirm Before Acting Protocol (US-06)
**As a** compliance officer,  
**I want** mandatory confirmations and disclaimers delivered accurately,  
**So that** SteadyHome satisfies financial consumer protection guidelines.

- **Acceptance Criteria 6.1 (Confirm Before Acting - V4):**
  - Prior to initiating a payment-mode transfer, the agent must read back: Borrower ID, Last 4 digits of loan, and Due date, and await confirmation.

- **Acceptance Criteria 6.2 (Statutory Payment Disclaimer - Section 5.F):**
  - When transferring to payment mode, the agent must play the single disclaimer exactly once:
    *"Please note that applicable fees and payment receipts are subject to your lender's terms and conditions."*

- **Acceptance Criteria 6.3 (Disclaimer Omission on Human Transfer):**
  - When transferring to a human representative, the payment disclaimer must NOT be played.

---

### User Story 7: Safety Guardrails Enforcement (US-07)
**As a** customer protection officer,  
**I want** sensitive card numbers, suicidal crisis phrases, and prompt injections blocked in real time,  
**So that** vulnerable customers receive emergency care and credentials are protected.

- **Acceptance Criteria 7.1 (Card and Aadhaar Protection):**
  - 16-digit card numbers or 12-digit Aadhaar numbers must be refused and masked as `[REDACTED]`. The sensitive numbers must never be repeated in speech or transcript.

- **Acceptance Criteria 7.2 (Crisis Protocol):**
  - Expressions of self-harm or suicidal intent must trigger the exact mandatory script:
    *"I'm really sorry you're going through this. You are not alone, and help is available. If you are in immediate danger, please call 112 now. You can also call Tele-MANAS on 14416, free and open at all hours, to talk to a trained counsellor. I'm connecting you with a person now."*
  - The session must immediately escalate to a human agent.

- **Acceptance Criteria 7.3 (Financial Advice Refusal):**
  - Prepayment recommendations must be refused with:
    *"I can provide information about your loan, but I cannot offer financial advice or recommend whether you should prepay. I can connect you with a human representative."*

---

### User Story 8: Keypad Stand-in and Explicit Human Escalation (US-08)
**As a** caller using a mobile phone,  
**I want** voice or keypad stand-ins (1, 2, 3, 0) and spoken triggers to navigate effortlessly,  
**So that** I can reach human assistance or choose options instantly without menu delays.

- **Acceptance Criteria 8.1:**
  - Keypad stand-ins: `'1'` = Due Date, `'2'` = Part-Payment, `'3'` = Late Fee, `'0'` = Human Agent.

- **Acceptance Criteria 8.2 (Immediate Transfer Words):**
  - Saying `"agent"`, `"representative"`, `"human"`, `"someone"`, or `"zero"` triggers immediate transfer without confirmation prompts.

---

## 2. AT LEAST 20 EDGE CASES COVERED

1. **Borrower ID correct but DOB mismatch:** Rejected with generic non-disclosing message.
2. **Borrower ID correct but Loan Last 4 mismatch:** Rejected with generic non-disclosing message.
3. **Blocked borrower account:** Immediately escalated to human desk.
4. **Third consecutive verification failure:** Escalated after exhausting 2 retries.
5. **EMI due date is today (0 days overdue):** 0% late fee applied.
6. **EMI due date is exactly 5 days overdue:** Exactly 2% fee applied (boundary test).
7. **EMI due date is exactly 6 days overdue:** Exactly 4% fee applied.
8. **EMI due date is exactly 30 days overdue:** Exactly 4% fee applied; online payment allowed after late fee paid.
9. **EMI due date is 31 days overdue:** Online payment blocked; escalated to human representative.
10. **Already-paid EMI:** 0 late fee; status reflects PAID.
11. **Part-payment amount exactly ₹500:** Accepted as satisfying minimum threshold.
12. **Part-payment amount ₹499:** Rejected for failing ₹500 minimum threshold.
13. **Part-payment on CLOSED loan:** Escalated to human agent.
14. **Part-payment on DEFAULT loan:** Escalated to recovery desk.
15. **Part-payment on UNKNOWN status loan:** Technical error issued; escalated without stating default.
16. **Branch Cash Desk payment on 31 December 2026:** Accepted as supported.
17. **Branch Cash Desk payment on 1 January 2027:** Rejected as discontinued; escalated.
18. **NetPay payment on or after 1 January 2027:** Accepted and renamed "NetPay Plus".
19. **KiteWallet payment requested:** Discontinued; immediately escalated.
20. **Spoken 16-digit card number:** Masked, redacted, and refused.
21. **Spoken 12-digit Aadhaar number:** Masked, redacted, and refused.
22. **Crisis phrase spoken during loan enquiry:** Normal workflow stopped; Tele-MANAS script delivered.
23. **Prepayment advice question:** Refused with mandatory non-advisory disclaimer.
24. **Prompt injection / system jailbreak attempt:** Safely refused under institutional guidelines.
25. **Caller silence (V5):** Re-prompted with gentle reminder.

---

## 3. FICTIONAL TEST DATASET (25+ ROWS)

| # | Borrower ID | Name | DOB | Account Status | Loan ID | Loan Amount (₹) | Loan Status | Monthly EMI (₹) | Next Due Date | Registered Mode | Scenario Description |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SH-BOR-1001 | Rajesh Sharma | 1985-06-15 | ACTIVE | SH-LN-1001 | 4,500,000 | ACTIVE | 39,052 | 2026-11-15 | AutoDebit | Standard active borrower; due in future |
| 2 | SH-BOR-1002 | Priya Venkat | 1990-03-22 | BLOCKED | SH-LN-1002 | 3,200,000 | ACTIVE | 32,014 | 2026-11-20 | NetPay | Blocked status; triggers immediate escalation |
| 3 | SH-BOR-1003 | Amit Patel | 1982-11-04 | ACTIVE | SH-LN-1003 | 5,500,000 | ACTIVE | 47,368 | 2026-11-07 | NetPay | 3 days overdue (2% late fee = ₹947) |
| 4 | SH-BOR-1004 | Sunita Rao | 1987-09-18 | ACTIVE | SH-LN-1004 | 2,800,000 | ACTIVE | 27,815 | 2026-11-05 | AutoDebit | Exactly 5 days overdue (2% late fee = ₹556) |
| 5 | SH-BOR-1005 | Vikram Malhotra | 1979-01-30 | ACTIVE | SH-LN-1005 | 6,000,000 | ACTIVE | 52,070 | 2026-10-26 | AutoDebit | 15 days overdue (4% late fee = ₹2,083) |
| 6 | SH-BOR-1006 | Neha Kulkarni | 1992-07-12 | ACTIVE | SH-LN-1006 | 4,000,000 | ACTIVE | 34,713 | 2026-10-11 | Branch Cash Desk | Exactly 30 days overdue (4% late fee = ₹1,389) |
| 7 | SH-BOR-1007 | Rohan Gupta | 1984-04-25 | ACTIVE | SH-LN-1007 | 5,000,000 | ACTIVE | 43,708 | 2026-10-06 | AutoDebit | 35 days overdue (>30d); human escalation |
| 8 | SH-BOR-1008 | Ananya Iyer | 1989-12-08 | ACTIVE | SH-LN-1008 | 2,500,000 | CLOSED | 31,000 | 2026-05-15 | NetPay | Closed loan; part-payment escalates |
| 9 | SH-BOR-1009 | Deepak Verma | 1978-08-14 | ACTIVE | SH-LN-1009 | 4,800,000 | DEFAULT | 43,980 | 2026-08-10 | Branch Cash Desk | Defaulted loan; part-payment escalates |
| 10 | SH-BOR-1010 | Kavita Nair | 1991-05-19 | ACTIVE | SH-LN-1010 | 3,500,000 | UNKNOWN | 34,466 | 2026-11-18 | AutoDebit | Unknown loan status; technical error escalation |
| 11 | SH-BOR-1011 | Suresh Menon | 1983-02-10 | ACTIVE | SH-LN-1011 | 3,800,000 | ACTIVE | 32,978 | 2026-10-10 | AutoDebit | Already-paid EMI; late fee is ₹0 |
| 12 | SH-BOR-1012 | Pooja Joshi | 1986-10-05 | ACTIVE | SH-LN-1012 | 4,200,000 | ACTIVE | 36,449 | 2026-12-31 | Branch Cash Desk | Cash desk payment on 31 Dec 2026 (Supported) |
| 13 | SH-BOR-1013 | Manish Pandey | 1980-08-28 | ACTIVE | SH-LN-1013 | 5,100,000 | ACTIVE | 44,430 | 2027-01-01 | Branch Cash Desk | Cash desk on 1 Jan 2027 (Discontinued; escalates) |
| 14 | SH-BOR-1014 | Divya Chawla | 1993-04-16 | ACTIVE | SH-LN-1014 | 3,000,000 | ACTIVE | 29,542 | 2026-11-20 | NetPay | NetPay before Jan 2027 (Supported) |
| 15 | SH-BOR-1015 | Arvind Swaminathan | 1975-09-03 | ACTIVE | SH-LN-1015 | 4,600,000 | ACTIVE | 39,920 | 2027-01-10 | NetPay | NetPay on or after 1 Jan 2027 (NetPay Plus) |
| 16 | SH-BOR-1016 | Sneha Kapoor | 1994-01-21 | ACTIVE | SH-LN-1016 | 3,600,000 | ACTIVE | 35,451 | 2026-11-25 | KiteWallet | KiteWallet requested (Discontinued; escalates) |
| 17 | SH-BOR-1017 | Tarun Saxena | 1988-11-11 | ACTIVE | SH-LN-1017 | 4,000,000 | ACTIVE | 34,713 | 2026-11-15 | AutoDebit | Part-payment ₹500 exact boundary (Accepted) |
| 18 | SH-BOR-1018 | Meera Nambiar | 1981-03-14 | ACTIVE | SH-LN-1018 | 4,000,000 | ACTIVE | 34,713 | 2026-11-15 | AutoDebit | Part-payment ₹499 boundary (Rejected) |
| 19 | SH-BOR-1019 | Harish Reddy | 1985-07-29 | ACTIVE | SH-LN-1019 | 6,500,000 | ACTIVE | 55,800 | 2026-11-12 | AutoDebit | High balance premium home loan |
| 20 | SH-BOR-1020 | Shruti Sen | 1990-10-10 | ACTIVE | SH-LN-1020 | 3,500,000 | ACTIVE | 34,466 | 2026-11-10 | NetPay | Due today on simulated clock (0 days overdue) |
| 21 | SH-BOR-1021 | Nitin Deshmukh | 1976-12-05 | ACTIVE | SH-LN-1021 | 9,500,000 | ACTIVE | 81,000 | 2026-11-14 | AutoDebit | Luxury villa loan |
| 22 | SH-BOR-1022 | Ritu Bhatia | 1995-02-17 | ACTIVE | SH-LN-1022 | 1,500,000 | ACTIVE | 15,124 | 2026-11-16 | NetPay | Affordable housing scheme loan |
| 23 | SH-BOR-1023 | Alok Chatterjee | 1958-04-12 | ACTIVE | SH-LN-1023 | 2,200,000 | ACTIVE | 27,400 | 2026-11-08 | AutoDebit | Senior citizen borrower (DOB 1958) |
| 24 | SH-BOR-1024 | Farah Khan | 1987-08-20 | ACTIVE | SH-LN-1024 | 5,200,000 | ACTIVE | 45,127 | 2026-11-22 | AutoDebit | Joint applicant repayment account |
| 25 | SH-BOR-1025 | Karthik Subramanian | 1991-11-25 | ACTIVE | SH-LN-1025 | 4,800,000 | ACTIVE | 41,512 | 2026-11-28 | AutoDebit | Scheduled advance clearance account |

