import pytest
from fastapi.testclient import TestClient

from main import app
from app.api import auth_routes
from app.core.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def auth_on(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    auth_routes._failures.clear()


def admin_token():
    r = client.post("/api/auth/admin-login", json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD})
    assert r.status_code == 200
    return r.json()["token"]


def borrower_token(bid="SH-BOR-1001", dob="1985-06-15", l4="1001"):
    return client.post("/api/auth/borrower-login", json={"borrower_id": bid, "date_of_birth": dob, "loan_last_four": l4})


def test_admin_routes_require_login():
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/borrowers").status_code == 401


def test_public_helpline_stays_open():
    assert client.post("/api/agent/chat", json={"session_id": "auth_pub", "message": "1"}).status_code == 200
    assert client.get("/api/health").status_code == 200


def test_admin_login_and_access():
    h = {"Authorization": f"Bearer {admin_token()}"}
    assert client.get("/api/dashboard", headers=h).status_code == 200


def test_admin_wrong_password():
    r = client.post("/api/auth/admin-login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401


def test_tampered_token_rejected():
    tok = admin_token()
    bad = tok[:-3] + ("AAA" if not tok.endswith("AAA") else "BBB")
    assert client.get("/api/dashboard", headers={"Authorization": f"Bearer {bad}"}).status_code == 401


def test_borrower_login_and_portal():
    r = borrower_token()
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    data = client.get("/api/portal/me", headers=h).json()
    assert data["borrower"]["borrower_id"] == "SH-BOR-1001"
    assert data["loans"][0]["emis"]


def test_borrower_cannot_use_admin_api_or_other_data():
    h = {"Authorization": f"Bearer {borrower_token().json()['token']}"}
    assert client.get("/api/borrowers", headers=h).status_code == 403
    assert client.get("/api/borrowers/SH-BOR-1003", headers=h).status_code == 403


def test_admin_token_is_not_a_borrower_token():
    h = {"Authorization": f"Bearer {admin_token()}"}
    assert client.get("/api/portal/me", headers=h).status_code == 403


def test_borrower_wrong_details_generic_error():
    r = borrower_token(l4="9999")
    assert r.status_code == 401
    assert "Borrower ID" in r.json()["detail"] and "1001" not in r.json()["detail"]


def test_blocked_borrower_refused():
    assert borrower_token("SH-BOR-1002", "1990-03-22", "1002").status_code == 403


def test_lockout_after_repeated_failures():
    for _ in range(auth_routes.MAX_FAILED_LOGINS):
        borrower_token(l4="0000")
    assert borrower_token().status_code == 429
