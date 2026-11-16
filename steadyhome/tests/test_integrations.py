import sys
import os

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from main import app
from app.agents.orchestrator import parse_credentials, normalize_speech
from app.core.config import settings
from app.services import gemini, supabase_sync

client = TestClient(app)


def test_credentials_from_written_text():
    text = "My Borrower ID is SH-BOR-1001, date of birth is 1985-06-15, and my loan ends in 1001"
    assert parse_credentials(text) == ("SH-BOR-1001", "1985-06-15", "1001")


def test_credentials_from_spoken_text():
    text = "S H B O R one zero zero one, born 15th of June 1985, last four digits 1001"
    assert parse_credentials(text) == ("SH-BOR-1001", "1985-06-15", "1001")
    assert normalize_speech("June 5, 1990") == "1990-06-05"


def test_voice_verification_end_to_end():
    sid = "test_voice_verify"
    client.post("/api/agent/reset", json={"session_id": sid})
    client.post("/api/agent/chat", json={"session_id": sid, "message": "1"})
    resp = client.post("/api/agent/chat", json={
        "session_id": sid,
        "message": "S H B O R one zero zero one, born 15th June 1985, loan ending 1001"})
    assert resp.status_code == 200
    state = resp.json()["state"]
    assert state["verified"] is True
    assert "due" in resp.json()["spoken_text"]


def test_part_payment_amount_ignores_credentials():
    sid = "test_amount_creds"
    client.post("/api/agent/reset", json={"session_id": sid})
    client.post("/api/agent/chat", json={"session_id": sid, "message": "2"})
    resp = client.post("/api/agent/chat", json={
        "session_id": sid,
        "message": "SH-BOR-1001 1985-06-15 loan ending 1001 part payment of 700 rupees"})
    assert "700" in resp.json()["response_text"]


def test_integrations_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "")
    data = client.get("/api/integrations/status").json()
    assert data["gemini"]["configured"] is False
    assert data["supabase"]["configured"] is False


def test_gemini_output_is_validated():
    cleaned = gemini._clean({
        "intent": "DROP_TABLE", "borrower_id": "SH-BOR-1002", "date_of_birth": "bad",
        "loan_last_four": 1002, "amount": -5, "payment_mode": "NetPay", "confirmation": "yes"})
    assert cleaned == {"borrower_id": "SH-BOR-1002", "loan_last_four": "1002",
                       "payment_mode": "NetPay", "confirmation": "yes"}


def test_gemini_nlu_drives_dialogue(monkeypatch):
    async def fake_understand(text, awaiting=False, intent=None):
        return {"intent": "DUE_DATE_ENQUIRY", "borrower_id": "SH-BOR-1001",
                "date_of_birth": "1985-06-15", "loan_last_four": "1001"}
    monkeypatch.setattr(gemini, "is_enabled", lambda: True)
    monkeypatch.setattr(gemini, "understand_utterance", fake_understand)
    sid = "test_gemini_nlu"
    client.post("/api/agent/reset", json={"session_id": sid})
    resp = client.post("/api/agent/chat", json={
        "session_id": sid, "message": "tell me about that monthly instalment thing, my details are as registered"})
    state = resp.json()["state"]
    assert state["verified"] is True
    assert any(t["tool_name"] == "gemini_understand" for t in state["tool_logs"])


def test_gemini_failure_falls_back_to_rules(monkeypatch):
    async def broken(*a, **k):
        return {}
    monkeypatch.setattr(gemini, "is_enabled", lambda: True)
    monkeypatch.setattr(gemini, "understand_utterance", broken)
    sid = "test_gemini_down"
    client.post("/api/agent/reset", json={"session_id": sid})
    resp = client.post("/api/agent/chat", json={"session_id": sid, "message": "1"})
    assert resp.status_code == 200
    assert "verify your identity" in resp.json()["response_text"]


def test_supabase_mirrors_session(monkeypatch):
    pushed = []
    monkeypatch.setattr(supabase_sync, "is_enabled", lambda: True)
    monkeypatch.setattr(supabase_sync, "_post", lambda table, row, upsert=False: pushed.append((table, row)))
    # run the thread synchronously
    monkeypatch.setattr(supabase_sync.threading, "Thread",
                        lambda target, args, daemon: type("T", (), {"start": lambda self: target(*args)})())
    sid = "test_supabase_mirror"
    client.post("/api/agent/reset", json={"session_id": sid})
    client.post("/api/agent/chat", json={"session_id": sid, "message": "connect me to a human agent"})
    tables = {t for t, _ in pushed}
    assert {"escalations", "call_sessions"} <= tables
    session_row = [r for t, r in pushed if t == "call_sessions"][-1]
    assert session_row["session_id"] == sid and session_row["is_escalated"] is True
