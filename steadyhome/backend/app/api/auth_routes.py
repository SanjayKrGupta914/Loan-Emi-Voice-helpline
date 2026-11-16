"""Login endpoints and the borrower self-service portal API."""

import hmac
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import create_token, current_user, current_borrower
from app.core.config import settings, get_simulated_now
from app.models.database import get_db
from app.tools.loan_tools import verify_borrower, calculate_late_fee
from database.schema import Borrower

router = APIRouter()

MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 60
_failures: Dict[str, Dict[str, float]] = {}

GENERIC_FAILURE = "We could not verify those details. Please check your Borrower ID, date of birth and the last 4 digits of your loan number."


class AdminLogin(BaseModel):
    username: str
    password: str


class BorrowerLogin(BaseModel):
    borrower_id: str = Field(..., examples=["SH-BOR-1001"])
    date_of_birth: str = Field(..., examples=["1985-06-15"])
    loan_last_four: str = Field(..., examples=["1001"])


def _check_lock(key: str) -> None:
    rec = _failures.get(key)
    if rec and rec["count"] >= MAX_FAILED_LOGINS and time.time() < rec["until"]:
        wait = int(rec["until"] - time.time()) + 1
        raise HTTPException(status_code=429, detail=f"Too many failed attempts. Try again in {wait} seconds.")


def _record_failure(key: str) -> None:
    rec = _failures.setdefault(key, {"count": 0, "until": 0})
    if time.time() >= rec["until"] and rec["count"] >= MAX_FAILED_LOGINS:
        rec["count"] = 0
    rec["count"] += 1
    if rec["count"] >= MAX_FAILED_LOGINS:
        rec["until"] = time.time() + LOCKOUT_SECONDS


@router.post("/auth/admin-login", summary="Administrator sign-in")
def admin_login(req: AdminLogin):
    key = f"admin:{req.username.lower()}"
    _check_lock(key)
    ok = hmac.compare_digest(req.username.encode(), settings.ADMIN_USERNAME.encode()) and \
        hmac.compare_digest(req.password.encode(), settings.ADMIN_PASSWORD.encode())
    if not ok:
        _record_failure(key)
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    _failures.pop(key, None)
    return {"token": create_token("admin", req.username, "Administrator"),
            "user": {"role": "admin", "name": "Administrator"}}


@router.post("/auth/borrower-login", summary="Borrower sign-in using Borrower ID, DOB and loan last 4 digits")
def borrower_login(req: BorrowerLogin, db: Session = Depends(get_db)):
    key = f"borrower:{req.borrower_id.strip().upper()}"
    _check_lock(key)
    result = verify_borrower(
        borrower_id=req.borrower_id.strip().upper(),
        date_of_birth=req.date_of_birth,
        loan_last_four=req.loan_last_four,
        db=db,
    )
    if result.get("status") == "BLOCKED":
        raise HTTPException(status_code=403, detail="Your account needs assistance from a customer care representative. Please call the helpline.")
    if not result.get("verified"):
        _record_failure(key)
        raise HTTPException(status_code=401, detail=GENERIC_FAILURE)
    _failures.pop(key, None)
    name = result.get("borrower_name") or "Borrower"
    return {"token": create_token("borrower", result["borrower_id"], name),
            "user": {"role": "borrower", "name": name, "borrower_id": result["borrower_id"]}}


@router.get("/auth/me", summary="Current signed-in user")
def me(user: Dict[str, Any] = Depends(current_user)):
    return {"role": user["role"], "name": user["name"], "borrower_id": user["sub"] if user["role"] == "borrower" else None}


@router.get("/portal/me", summary="Signed-in borrower's loan, EMI schedule and late fees")
def portal_me(user: Dict[str, Any] = Depends(current_borrower), db: Session = Depends(get_db)):
    borrower = db.query(Borrower).filter(Borrower.borrower_id == user["sub"]).first()
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    sim_now = get_simulated_now()
    loans = []
    for loan in borrower.loans:
        emis = []
        for e in sorted(loan.emis, key=lambda x: x.due_date):
            fee = calculate_late_fee(emi_amount=e.emi_amount, due_date=e.due_date,
                                     payment_status=e.payment_status, simulated_current_date=sim_now)
            emis.append({
                "emi_id": e.emi_id, "amount": e.emi_amount, "due_date": e.due_date,
                "payment_status": e.payment_status, "payment_mode": e.payment_mode,
                "days_overdue": fee["days_overdue"], "late_fee": fee["late_fee_amount"],
                "needs_human_help": fee["requires_escalation"], "paid_date": e.paid_date,
            })
        outstanding = [x for x in emis if x["payment_status"] in ("PENDING", "OVERDUE")]
        loans.append({
            "loan_id": loan.loan_id, "status": loan.loan_status, "amount": loan.loan_amount,
            "tenure_months": loan.loan_tenure_months, "interest_rate": loan.interest_rate,
            "emi_amount": loan.emi_amount, "next_due_date": loan.next_due_date,
            "sanction_date": loan.sanction_date,
            "total_due_now": round(sum(x["amount"] + x["late_fee"] for x in outstanding if x["days_overdue"] > 0
                                       or x["due_date"] <= sim_now.date().isoformat()), 2),
            "total_late_fees": round(sum(x["late_fee"] for x in outstanding), 2),
            "emis": emis,
        })
    return {
        "borrower": {"borrower_id": borrower.borrower_id, "name": borrower.name, "phone": borrower.phone,
                     "email": borrower.email, "address": borrower.address},
        "simulated_now": sim_now.isoformat(),
        "loans": loans,
    }
