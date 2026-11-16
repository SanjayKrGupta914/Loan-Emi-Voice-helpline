import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.tools.loan_tools import validate_payment_mode, validate_part_payment_amount

def test_autodebit_supported():
    res = validate_payment_mode("AutoDebit", "2026-11-10")
    assert res["supported"] is True
    assert res["canonical_name"] == "AutoDebit"
    assert res["requires_escalation"] is False
    assert res["disclaimer"] is not None

def test_netpay_before_2027():
    res = validate_payment_mode("NetPay", "2026-11-20")
    assert res["supported"] is True
    assert res["canonical_name"] == "NetPay"
    assert res["requires_escalation"] is False

def test_netpay_plus_after_2027():
    """GT-07: NetPay called NetPay Plus on or after 1 January 2027."""
    res = validate_payment_mode("NetPay", "2027-01-10")
    assert res["supported"] is True
    assert res["canonical_name"] == "NetPay Plus"
    assert res["requires_escalation"] is False

def test_branch_cash_desk_active_until_31_dec_2026():
    """GT-08: Branch Cash Desk supported on 31 December 2026."""
    res = validate_payment_mode("Branch Cash Desk", "2026-12-31")
    assert res["supported"] is True
    assert res["canonical_name"] == "Branch Cash Desk"
    assert res["requires_escalation"] is False

def test_branch_cash_desk_discontinued_from_1_jan_2027():
    """ST-01: Branch Cash Desk unsupported on 1 January 2027."""
    res = validate_payment_mode("Branch Cash Desk", "2027-01-01")
    assert res["supported"] is False
    assert res["requires_escalation"] is True
    assert "31 December 2026" in res["reason"]

def test_kitewallet_permanently_discontinued():
    """ST-02: KiteWallet is discontinued and never supported."""
    res = validate_payment_mode("KiteWallet", "2026-11-10")
    assert res["supported"] is False
    assert res["requires_escalation"] is True
    assert "discontinued" in res["reason"].lower()

def test_part_payment_boundary_500_accepted():
    """BT-03: Part-payment of exactly ₹500 is accepted."""
    res = validate_part_payment_amount(500.0)
    assert res["valid"] is True
    assert res["error_code"] is None

def test_part_payment_boundary_499_rejected():
    """BT-04: Part-payment of ₹499 is rejected."""
    res = validate_part_payment_amount(499.0)
    assert res["valid"] is False
    assert res["error_code"] == "AMOUNT_BELOW_MINIMUM"

