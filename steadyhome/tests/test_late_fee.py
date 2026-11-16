import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.tools.loan_tools import calculate_late_fee

SIMULATED_DATE = "2026-11-10T09:00:00"

def test_zero_days_overdue():
    """Due today or in future: 0 late fee, can process online."""
    res = calculate_late_fee(39052.0, "2026-11-10", "PENDING", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 0
    assert res["late_fee_amount"] == 0
    assert res["can_process_online"] is True
    assert res["requires_escalation"] is False

def test_three_days_overdue_tier1():
    """3 days overdue: 2% tier."""
    res = calculate_late_fee(47368.0, "2026-11-07", "OVERDUE", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 3
    assert res["late_fee_percentage"] == 2.0
    assert res["late_fee_amount"] == round(47368.0 * 0.02) # 947
    assert res["can_process_online"] is True

def test_exactly_five_days_overdue_boundary():
    """BT-01: Exactly 5 days overdue belongs to 2% tier."""
    res = calculate_late_fee(27815.0, "2026-11-05", "OVERDUE", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 5
    assert res["late_fee_percentage"] == 2.0
    assert res["late_fee_amount"] == round(27815.0 * 0.02) # 556
    assert res["can_process_online"] is True

def test_fifteen_days_overdue_tier2():
    """15 days overdue: 4% tier."""
    res = calculate_late_fee(52070.0, "2026-10-26", "OVERDUE", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 15
    assert res["late_fee_percentage"] == 4.0
    assert res["late_fee_amount"] == round(52070.0 * 0.04) # 2083
    assert res["can_process_online"] is True

def test_exactly_thirty_days_overdue_boundary():
    """BT-02: Exactly 30 days overdue belongs to 4% tier."""
    res = calculate_late_fee(34713.0, "2026-10-11", "OVERDUE", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 30
    assert res["late_fee_percentage"] == 4.0
    assert res["late_fee_amount"] == round(34713.0 * 0.04) # 1389
    assert res["can_process_online"] is True

def test_over_thirty_days_escalation():
    """NT-02: More than 30 days overdue blocks online resolution and requires human agent."""
    res = calculate_late_fee(43708.0, "2026-10-06", "OVERDUE", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 35
    assert res["can_process_online"] is False
    assert res["requires_escalation"] is True
    assert "30-day" in res["escalation_reason"]

def test_already_paid_emi():
    """GT-10: Paid EMI has 0 late fee."""
    res = calculate_late_fee(32978.0, "2026-10-10", "PAID", simulated_current_date=SIMULATED_DATE)
    assert res["days_overdue"] == 0
    assert res["late_fee_amount"] == 0
    assert res["can_process_online"] is True

