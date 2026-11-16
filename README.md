# SteadyHome – AI-Powered Loan EMI Voice Helpline
## University Capstone Engineering Project

The complete project codebase is organized under `steadyhome/` with:
- **`steadyhome/backend/`**: FastAPI, Python tools, agents, guardrails, and APIs.
- **`steadyhome/frontend/`**: React, Vite, TypeScript, Tailwind CSS, Lucide icons, Recharts.
- **`steadyhome/database/`**: SQLite schema and seed script with 25+ rich scenarios.
- **`steadyhome/tests/`**: Pytest automated test suite (35 passed tests).
- **`steadyhome/docs/`**: Comprehensive requirements, architecture, report, and contribution guide.

### Quick Start:
```bash
# 1. Initialize and Seed Database
cd steadyhome
python3 database/seed.py

# 2. Run All Automated Pytest Tests
pytest -v tests/

# 3. Start Backend Server
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Once started, open `http://127.0.0.1:8000` in Google Chrome to access the complete application!

Refer to `steadyhome/README.md` and `steadyhome/docs/` for full architectural details and capstone documentation.

