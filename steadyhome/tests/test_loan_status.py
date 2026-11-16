import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.tools.loan_tools import check_loan_status
from app.models.database import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_active_loan_status_check(db):
    """GT-09: Active loan permits part-payment."""
    res = check_loan_status("SH-LN-1001", db=db)
    assert res["status"] == "ACTIVE"
    assert res["can_part_pay"] is True
    assert res["requires_escalation"] is False

def test_closed_loan_status_escalation(db):
    """ST-03: Closed loan rejects part-payment and escalates."""
    res = check_loan_status("SH-LN-1008", db=db)
    assert res["status"] == "CLOSED"
    assert res["can_part_pay"] is False
    assert res["requires_escalation"] is True
    assert "CLOSED" in res["escalation_reason"]

def test_default_loan_status_escalation(db):
    """ST-04: Defaulted loan rejects part-payment and escalates."""
    res = check_loan_status("SH-LN-1009", db=db)
    assert res["status"] == "DEFAULT"
    assert res["can_part_pay"] is False
    assert res["requires_escalation"] is True
    assert "DEFAULT" in res["escalation_reason"]

def test_unknown_loan_status_technical_error(db):
    """ST-05: Unknown loan status returns technical error and escalates; NEVER says loan is in default."""
    res = check_loan_status("SH-LN-1010", db=db)
    assert res["status"] == "UNKNOWN"
    assert res["can_part_pay"] is False
    assert res["requires_escalation"] is True
    assert "technical" in res["error"].lower()
    # Critical verification: Must never state or claim default!
    assert "default" not in res["error"].lower()

