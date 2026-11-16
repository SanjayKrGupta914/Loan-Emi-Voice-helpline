"""
Supabase persistence for SteadyHome (PostgREST over HTTPS, no extra dependency).

SQLite stays the system of record for the demo; when SUPABASE_URL and a key are configured,
escalations, interaction logs and call transcripts are mirrored to Supabase. Every call is
best-effort: a Supabase outage never interrupts a live call.
"""

import json
import threading
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

TABLES = ("escalations", "interaction_logs", "call_sessions")


def is_enabled() -> bool:
    return bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)


def _headers(prefer: str = "return=minimal") -> Dict[str, str]:
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


def _post(table: str, row: Dict[str, Any], upsert: bool = False) -> None:
    prefer = "resolution=merge-duplicates,return=minimal" if upsert else "return=minimal"
    try:
        httpx.post(
            f"{settings.SUPABASE_URL}/rest/v1/{table}",
            headers=_headers(prefer),
            content=json.dumps(row, default=str),
            timeout=5.0,
        )
    except Exception:
        pass


def push(table: str, row: Dict[str, Any], upsert: bool = False) -> None:
    """Fire-and-forget mirror of one row (runs in a daemon thread so the call isn't delayed)."""
    if not is_enabled():
        return
    threading.Thread(target=_post, args=(table, row, upsert), daemon=True).start()


def sync_session(state: Any) -> None:
    """Upserts the whole conversation (transcript + tool trace + key variables) for a session."""
    push("call_sessions", {
        "session_id": state.session_id,
        "borrower_id": state.borrower_id if state.verified else None,
        "verified": state.verified,
        "intent_tag": state.intent_tag,
        "is_escalated": state.is_escalated,
        "escalation_id": state.escalation_id,
        "transcript": [m.model_dump() for m in state.messages],
        "tool_logs": [t.model_dump() for t in state.tool_logs],
    }, upsert=True)


def status() -> Dict[str, Any]:
    """Live check: does the project answer and do all expected tables exist?"""
    if not is_enabled():
        return {"configured": False, "reachable": False, "detail": "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set"}
    missing: List[str] = []
    try:
        for table in TABLES:
            r = httpx.get(f"{settings.SUPABASE_URL}/rest/v1/{table}", params={"select": "*", "limit": "1"},
                          headers=_headers(), timeout=6.0)
            if r.status_code in (401, 403):
                return {"configured": True, "reachable": True, "tables_ok": False,
                        "detail": f"Key rejected (HTTP {r.status_code})"}
            if r.status_code != 200:
                missing.append(table)
    except Exception as exc:
        return {"configured": True, "reachable": False, "detail": f"Connection failed: {type(exc).__name__}"}
    if missing:
        return {"configured": True, "reachable": True, "tables_ok": False,
                "detail": f"Missing tables: {', '.join(missing)} - run database/supabase_schema.sql"}
    return {"configured": True, "reachable": True, "tables_ok": True, "detail": "OK"}
