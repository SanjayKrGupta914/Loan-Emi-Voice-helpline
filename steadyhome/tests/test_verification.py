import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.tools.loan_tools import verify_borrower
from app.models.database import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_successful_borrower_verification(db):
    """GT-01: Active borrower identity verification succeeds."""
    res = verify_borrower("SH-BOR-1001", "1985-06-15", "1001", db=db)
    assert res["verified"] is True
    assert res["status"] == "SUCCESS"
    assert res["borrower_name"] == "Rajesh Sharma"
    assert res["loan_id"] == "SH-LN-1001"
    assert res["requires_escalation"] is False

def test_blocked_borrower_escalation(db):
    """NT-01: Blocked borrower triggers immediate escalation to human agent."""
    res = verify_borrower("SH-BOR-1002", "1990-03-22", "1002", db=db)
    assert res["verified"] is False
    assert res["status"] == "BLOCKED"
    assert res["requires_escalation"] is True
    assert "BLOCKED" in res["escalation_reason"]

def test_incorrect_credentials_non_disclosure(db):
    """Rule A: Never disclose which individual credential failed."""
    # Incorrect DOB
    res_dob = verify_borrower("SH-BOR-1001", "1999-01-01", "1001", db=db)
    assert res_dob["verified"] is False
    assert res_dob["status"] == "FAILED"
    # Incorrect loan last 4
    res_l4 = verify_borrower("SH-BOR-1001", "1985-06-15", "9999", db=db)
    assert res_l4["verified"] is False
    assert res_l4["status"] == "FAILED"
    # Both error messages must be identical generic security messages
    assert res_dob["error"] == res_l4["error"]
    assert "date of birth" not in res_dob["error"].lower() or "check your" in res_dob["error"].lower()
    assert "last 4 digits" not in res_dob["error"].lower() or "check your" in res_dob["error"].lower()

def test_nonexistent_borrower(db):
    res = verify_borrower("SH-BOR-9999", "1985-06-15", "1001", db=db)
    assert res["verified"] is False
    assert res["status"] == "FAILED"

