import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from main import app

client = TestClient(app)

def test_root_endpoint():
    resp = client.get("/", headers={"accept": "application/json"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["institution"] == "SteadyHome Home Loans"
    assert data["demo_mode"] is True

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"

def test_dashboard_endpoint():
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert data["stats"]["total_borrowers"] >= 25
    assert data["stats"]["active_loans"] >= 15
    assert "collection_trends" in data
    assert "payment_mode_distribution" in data
    assert "loan_status_distribution" in data

def test_borrowers_endpoints():
    resp = client.get("/api/borrowers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 25

    # Specific profile
    resp_b = client.get("/api/borrowers/SH-BOR-1001")
    assert resp_b.status_code == 200
    b_data = resp_b.json()
    assert b_data["borrower_id"] == "SH-BOR-1001"
    assert len(b_data["loans"]) > 0

def test_verify_endpoint():
    resp = client.post("/api/verify", json={
        "borrower_id": "SH-BOR-1001",
        "date_of_birth": "1985-06-15",
        "loan_last_four": "1001"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["status"] == "SUCCESS"

def test_agent_chat_dialogue():
    resp = client.post("/api/agent/chat", json={
        "session_id": "test-session-api-1",
        "message": "Hello, I want to check my EMI"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "response_text" in data
    assert "verify" in data["response_text"].lower() or "borrower" in data["response_text"].lower()

def test_evaluation_run_all():
    resp = client.post("/api/evaluate/run")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert data["summary"]["total_tests"] >= 25
    assert data["summary"]["passed"] > 20
    assert data["summary"]["pass_percentage"] > 80.0

def test_architecture_endpoint():
    resp = client.get("/api/architecture")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    node_ids = [n["id"] for n in data["nodes"]]
    assert "root_agent" in node_ids
    assert "emi_sub_agent" in node_ids

