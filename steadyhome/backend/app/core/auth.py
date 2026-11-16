"""
Minimal signed-token authentication for the SteadyHome demo (no external dependency).

Tokens are `base64url(payload).hmac_sha256` with role, subject and expiry. Two roles:
  - "admin":    bank operations console (all management APIs)
  - "borrower": self-service portal (only that borrower's own loan data)
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, Request

from app.core.config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body: str) -> str:
    return _b64(hmac.new(settings.AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest())


def create_token(role: str, subject: str, name: str) -> str:
    payload = {"role": role, "sub": subject, "name": name, "exp": int(time.time()) + settings.AUTH_TOKEN_TTL_SECONDS}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body)}"


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        body, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body)):
            return None
        payload = json.loads(_unb64(body))
        return payload if payload.get("exp", 0) > time.time() else None
    except Exception:
        return None


def _bearer(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return decode_token(authorization[7:].strip())


def current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = _bearer(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return user


def current_borrower(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = current_user(authorization)
    if user.get("role") != "borrower":
        raise HTTPException(status_code=403, detail="Borrower sign-in required.")
    return user


# Endpoints the public helpline and login screens need without signing in.
PUBLIC_API_PATHS = ("/api/agent/", "/api/advisory", "/api/health")


def admin_guard(request: Request, authorization: Optional[str] = Header(None)) -> None:
    """Router-level guard: everything under /api needs an admin token except the public helpline paths."""
    if not settings.AUTH_REQUIRED:
        return
    if request.url.path.startswith(PUBLIC_API_PATHS):
        return
    user = _bearer(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
