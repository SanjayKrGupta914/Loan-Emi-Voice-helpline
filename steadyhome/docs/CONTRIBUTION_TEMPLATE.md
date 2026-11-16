# SteadyHome – Capstone Project Contribution Template
## Four-Member Engineering Team Task Distribution

---

### Team Member 1: Requirements Architect & Agent Designer
- **Assigned Domain:** Requirements Analysis & Multi-Agent Architecture
- **Key Deliverables:**
  - Authored user stories (US-01 through US-08) with Given/When/Then acceptance criteria.
  - Designed Root Agent and EMI Service Sub-Agent 5-block prompts (Role, Persona, Context, Task, Constraints).
  - Defined few-shot speech dialogues and conversational state transition flows.
  - Specified Confirm Before Acting (V4) protocol and payment disclaimer delivery rules.
- **Key Source Code Files:**
  - `backend/app/agents/prompts.py`
  - `backend/app/agents/state.py`
  - `docs/REQUIREMENTS_AND_TEST_DATA.md`

---

### Team Member 2: Backend Engineer & Database Architect
- **Assigned Domain:** Python Business Tools & Relational Datastore
- **Key Deliverables:**
  - Implemented 5 Python business tools: `verify_borrower()`, `lookup_loan()`, `check_loan_status()`, `calculate_late_fee()`, and `build_handoff_details()`.
  - Designed SQLite database schema (`Borrower`, `Loan`, `EMI`, `Payment`, `Escalation`, `InteractionLog`).
  - Synthesized rich seed data across 25+ fictional customer scenarios.
  - Implemented simulated clock architecture (`2026-11-10T09:00:00`) and Open-Meteo HTTPS advisory integration.
- **Key Source Code Files:**
  - `backend/app/tools/loan_tools.py`
  - `database/schema.py`
  - `database/seed.py`
  - `backend/app/services/advisory.py`

---

### Team Member 3: Full-Stack Developer & UI/UX Designer
- **Assigned Domain:** Frontend Engineering & Fintech Design System
- **Key Deliverables:**
  - Built white fintech design system (Razorpay/Stripe aesthetic: `#FFFFFF`, `#315E9E`, `#24865B`, `#D99A32`, `#D9534F`).
  - Developed 9 responsive pages: Dashboard, Voice Helpline, Borrowers, EMIs, Architecture, Guardrails, Evaluate, Escalations, Settings.
  - Engineered 3-panel call center console with live waveform animation and customer drawer.
  - Developed interactive node-based agent architecture topology visualizer.
- **Key Source Code Files:**
  - `frontend/src/pages/*`
  - `frontend/src/layouts/*`
  - `frontend/src/components/*`
  - `frontend/src/hooks/useVoice.ts`

---

### Team Member 4: QA Engineer & Safety Specialist
- **Assigned Domain:** Safety Guardrails & Automated Testing Suite
- **Key Deliverables:**
  - Implemented 4 safety guardrails (Card/Aadhaar masking, Tele-MANAS crisis intervention, financial advice refusal, prompt injection defense).
  - Developed automated evaluation runner covering 25+ test cases across 5 categories.
  - Authored comprehensive Pytest suite (35 automated tests verifying boundaries, negative conditions, and APIs).
  - Prepared final project engineering report and technical architecture documentation.
- **Key Source Code Files:**
  - `backend/app/guardrails/safety.py`
  - `backend/app/services/evaluator.py`
  - `tests/*`
  - `docs/REPORT.md`
  - `docs/ARCHITECTURE.md`

