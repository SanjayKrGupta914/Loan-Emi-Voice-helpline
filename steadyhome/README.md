# SteadyHome – AI-Powered Loan EMI Voice Helpline
## University Capstone Engineering Project

SteadyHome is an enterprise-grade, regulation-compliant conversational AI voice helpline and internal management system designed for a retail home-loan financial institution.

The project demonstrates an intelligent voice assistant capable of authenticating borrowers, resolving EMI due-date inquiries, calculating tiered late fees, validating part-payments, advising on permissible payment channels across policy transitions, enforcing safety guardrails, and escalating complex inquiries to human customer support desks.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **Two-Tier Conversational Agent Architecture:**
   - **Root Agent:** Welcomes caller, captures intent, conducts 3-tuple borrower verification (`verify_borrower()`), detects emergency crisis statements, handles keypad stand-ins (`1`, `2`, `3`, `0`), and routes verified inquiries.
   - **EMI Service Sub-Agent:** Domain specialist handling loan registry lookups (`lookup_loan()`), late fee computations (`calculate_late_fee()`), part-payment gating (`check_loan_status()`), minimum threshold validation (`>= ₹500`), and Confirm Before Acting (`V4`) protocol.

2. **Five Deterministic Python Tools:**
   - `verify_borrower()`: Validates Borrower ID, DOB, and loan last 4 digits; flags BLOCKED accounts; prevents credential enumeration.
   - `lookup_loan()`: Retrieves active loan amount, interest rate, tenure, and next due date.
   - `check_loan_status()`: Gating validation executed for part-payments ONLY (`ACTIVE` permitted; `CLOSED` and `DEFAULT` escalate; `UNKNOWN` triggers technical error).
   - `calculate_late_fee()`: Evaluates overdue days (0% for 0 days, 2% for 1–5 days, 4% for 6–30 days; blocks online resolution for >30 days).
   - `build_handoff_details()`: Prepares structured JSON context for human representatives; omits payment disclaimer on human handoffs.

3. **Institutional Safety Guardrails:**
   - **Guardrail 1:** 16-digit card and 12-digit Aadhaar number detection, refusal, and redaction (`[REDACTED]`).
   - **Guardrail 2:** Mental health crisis intervention delivering exact statutory script for **Tele-MANAS (14416)** and **Emergency (112)**.
   - **Guardrail 3:** Prepayment advice refusal with mandatory financial neutrality disclosure.
   - **Guardrail 4:** Prompt injection, system override, and database extraction defense.

4. **Simulated Reference Clock (Section 5.I):**
   - Configurable reference time fixed at **10 November 2026, 09:00 AM IST**.
   - Ensures exact, reproducible boundary evaluations independent of system clock.

5. **White Fintech Design System (Section 3):**
   - Professional Indian fintech aesthetic inspired by Razorpay, Stripe, and Linear.
   - Palette: `#FFFFFF` (base), `#F7F8FA` (secondary), `#315E9E` (primary blue), `#24865B` (success green), `#D99A32` (warning orange), `#D9534F` (danger red).

6. **Interactive Automated Testing Dashboard (25+ Tests):**
   - 10 Golden tests, 6 Scenario tests, 4 Boundary tests, 3 Safety tests, and 2 Negative tests.
   - Real tool execution satisfying assertions (not hardcoded).

---

## 🛠️ Technology Stack

- **Backend:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn, Pytest.
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide React, Recharts.
- **Database:** SQLite 3 with modular schema supporting PostgreSQL migration.
- **Voice:** Web Speech API (`SpeechRecognition` en-IN) + Browser Text-to-Speech (`SpeechSynthesis`).
- **External Integration:** Free public HTTPS JSON API (Open-Meteo) for real-time payment day weather and clearing telemetry.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.14 supported)
- Node.js v18+ and npm v9+

### 2. Database Initialization & Seeding
From the `steadyhome` directory, initialize the SQLite database with 25+ fictional customer scenarios:

```bash
cd steadyhome
python3 database/seed.py
```

Output:
```
Database seeded successfully with 25 borrowers, 25 loans, 25 EMIs, 10 payments, and 5 escalations.
```

### 3. Run Automated Pytest Suite
Verify all 35 unit, integration, boundary, safety, and API tests:

```bash
pytest -v tests/
```

All 35 tests execute and pass with zero regressions:
```
======================= 35 passed in 0.31s ========================
```

### 4. Start the Backend API Server
Start FastAPI on port 8000:

```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### 5. Start or Build the Frontend

**Option A: Development Mode (Hot-Reloading on Port 3000)**
```bash
cd frontend
npm run dev
```
Open `http://localhost:3000` in Google Chrome or any modern browser.

**Option B: Production Mode (Served directly by FastAPI)**
The frontend is already built into `frontend/dist/`. Simply open `http://127.0.0.1:8000` in your browser to access the complete application!

---

## 🔐 Login

- **Borrower portal:** sign in with Borrower ID + date of birth + last 4 digits of the loan (same 3-factor check as the voice call). Shows their loan, EMI schedule, late fees, and the AI helpline. Blocked accounts are refused; 5 wrong attempts lock that ID for 60 seconds.
- **Administrator:** `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env` (demo default `admin` / `SteadyAdmin@2026`). All management APIs require an admin token; the public AI helpline endpoints stay open.
- Demo borrowers: `SH-BOR-1001 / 1985-06-15 / 1001`, `SH-BOR-1003 / 1982-11-04 / 1003`. (`SH-BOR-1002` is BLOCKED, `SH-BOR-1008` is a closed loan.)

---

## 🔌 Gemini & Supabase Setup

1. `cp .env.example .env`
2. **Gemini:** create a key at https://aistudio.google.com/apikey and set `GEMINI_API_KEY`. Gemini only *interprets* caller speech (intent, ID, DOB, amount, yes/no); guardrails, tools and policy rules stay deterministic, and the call falls back to the rule-based parser if Gemini is off or errors.
3. **Supabase:** run `database/supabase_schema.sql` in the Supabase SQL editor, then set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Escalations, interaction logs and full call transcripts are mirrored (best-effort) to `escalations`, `interaction_logs` and `call_sessions`. SQLite remains the local system of record.
4. Restart the server and open **Settings -> Integrations** (or `GET /api/integrations/status`) to confirm both show CONNECTED.

Voice calls need Chrome or Edge (Web Speech API) on `http://localhost`; allow the microphone when prompted.

---

## 📋 Nine Application Modules

1. **Operations Overview (`/` or Dashboard):** Real-time statistic cards (Borrowers, Active Loans, Collections, Escalations), collection trends, payment mode distributions, and recent interactions.
2. **AI Voice Helpline (`Helpline`):** 3-panel call center layout with real-time transcript, microphone audio waveform visualizer, keypad stand-in guide, speech synthesis, and live customer profile drawer.
3. **Borrower Portfolio (`Borrowers`):** Filterable portfolio listing with comprehensive profile modals showing loan accounts and repayment schedules.
4. **EMI Management Desk (`EMI Management`):** Overdue tracking and breakdown calculator enforcing late fee tiers (0%, 2%, 4%).
5. **Agent Architecture Topology (`Agent Architecture`):** Interactive node-based visualization displaying 5-block instruction sets (Role, Persona, Context, Task, Constraints) and tool signatures.
6. **Safety Guardrails Console (`Guardrails`):** Live compliance tester for Card/Aadhaar redaction, crisis detection, and prompt injection defense.
7. **Evaluation Dashboard (`Evaluate`):** Automated test suite runner executing 25+ Golden, Boundary, Scenario, Safety, and Negative test cases with diff inspection.
8. **Escalations Queue (`Escalations`):** Specialized human representative dispatch queue for account blocks, long overdue accounts (>30 days), and customer requests.
9. **Settings & Clock Configuration (`Settings`):** Simulated reference clock adjuster, Open-Meteo live advisory inspector, and policy threshold monitor.

---

## 🔒 Safety & Regulatory Compliance

- **Card/Aadhaar Redaction:** 16-digit card and 12-digit Aadhaar numbers are immediately replaced with `[REDACTED]` and never echoed in transcripts.
- **Mental Health Crisis Interception:** Emergency phrases trigger the mandatory script:
  > *"I'm really sorry you're going through this. You are not alone, and help is available. If you are in immediate danger, please call 112 now. You can also call Tele-MANAS on 14416, free and open at all hours, to talk to a trained counsellor. I'm connecting you with a person now."*
- **Prepayment Advice Neutrality:** Neutrality maintained; callers asking whether to prepay are directed to human advisory representatives.

---

## 📚 Project Documentation Directory

- [`docs/REQUIREMENTS_AND_TEST_DATA.md`](docs/REQUIREMENTS_AND_TEST_DATA.md): 8 User Stories, 20+ Edge cases, and 25+ fictional test rows.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Multi-agent diagrams, 5-block prompts, 10 variables, and tool specifications.
- [`docs/REPORT.md`](docs/REPORT.md): 10-page academic capstone report.
- [`docs/CONTRIBUTION_TEMPLATE.md`](docs/CONTRIBUTION_TEMPLATE.md): Four-member team task distribution matrix.

