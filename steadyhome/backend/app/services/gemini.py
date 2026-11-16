"""
Gemini natural-language understanding for the SteadyHome voice helpline.

Gemini is used ONLY to interpret what the caller said (intent, credentials, amount,
payment mode, yes/no). All decisions, tool calls, guardrails and policy rules stay in
deterministic Python, so a missing key, network error or odd model output degrades to the
rule-based parser instead of breaking a call.
"""

import json
import re
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

VALID_INTENTS = {"DUE_DATE_ENQUIRY", "PART_PAYMENT", "LATE_FEE_ENQUIRY", "HUMAN_AGENT_REQUEST", "GENERAL_ENQUIRY"}
VALID_MODES = {"AutoDebit", "NetPay", "Branch Cash Desk", "KiteWallet"}

NLU_PROMPT = """You are the speech-understanding layer of a home-loan voice helpline (SteadyHome, India).
The caller's words come from speech-to-text and may be messy: spelled-out IDs ("S H B O R one zero zero one"),
spoken dates ("fifteenth of June nineteen eighty five"), number words, or Indian-English phrasing.
Return ONLY a JSON object with these keys (use null when not stated, never guess):
  "intent": one of DUE_DATE_ENQUIRY, PART_PAYMENT, LATE_FEE_ENQUIRY, HUMAN_AGENT_REQUEST, GENERAL_ENQUIRY, or null
  "borrower_id": string like "SH-BOR-1001" or null
  "date_of_birth": "YYYY-MM-DD" or null
  "loan_last_four": 4 digit string or null
  "amount": number in rupees or null
  "payment_mode": one of AutoDebit, NetPay, "Branch Cash Desk", KiteWallet, or null
  "confirmation": "yes", "no" or null (only if the caller is answering a yes/no question)
Conversation context: awaiting_confirmation={awaiting}; current_intent={intent}.
Caller said: {text}"""


def is_enabled() -> bool:
    return bool(settings.USE_EXTERNAL_LLM and settings.GEMINI_API_KEY)


FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]

# Circuit breaker: after a failed call (quota / overload / timeout) skip Gemini briefly so a live
# call falls straight to the rule-based parser instead of waiting on every turn.
_COOLDOWN_SECONDS = 45.0
_blocked_until = 0.0


async def _generate(prompt: str, json_mode: bool, timeout: float = 3.5, force: bool = False) -> Optional[str]:
    """Calls Gemini, moving to the next model when one is overloaded (503/429) or retired (404)."""
    global _blocked_until
    if not force and time.monotonic() < _blocked_until:
        return None
    result = await _generate_once(prompt, json_mode, timeout)
    if result is None:
        _blocked_until = time.monotonic() + _COOLDOWN_SECONDS
    else:
        _blocked_until = 0.0
    return result


async def _generate_once(prompt: str, json_mode: bool, timeout: float) -> Optional[str]:
    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 600},
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    models = [settings.GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != settings.GEMINI_MODEL]
    headers = {"x-goog-api-key": settings.GEMINI_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            for model in models:
                resp = await client.post(GEMINI_ENDPOINT.format(model=model), headers=headers, json=body)
                if resp.status_code == 200:
                    parts = resp.json()["candidates"][0]["content"]["parts"]
                    return "".join(p.get("text", "") for p in parts if not p.get("thought"))
                if resp.status_code not in (404, 429, 500, 502, 503, 504):
                    return None  # bad key / bad request: another model won't help
    except Exception:
        return None
    return None


def _clean(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validates the model output so only well-formed values reach the dialogue manager."""
    out: Dict[str, Any] = {}
    intent = raw.get("intent")
    if intent in VALID_INTENTS:
        out["intent"] = intent
    bid = raw.get("borrower_id")
    if isinstance(bid, str) and re.fullmatch(r"SH-BOR-\d{4}", bid.strip(), re.IGNORECASE):
        out["borrower_id"] = bid.strip().upper()
    dob = raw.get("date_of_birth")
    if isinstance(dob, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", dob.strip()):
        out["date_of_birth"] = dob.strip()
    l4 = raw.get("loan_last_four")
    if l4 is not None and re.fullmatch(r"\d{4}", str(l4).strip()):
        out["loan_last_four"] = str(l4).strip()
    amount = raw.get("amount")
    if isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > 0:
        out["amount"] = float(amount)
    mode = raw.get("payment_mode")
    if mode in VALID_MODES:
        out["payment_mode"] = mode
    if raw.get("confirmation") in ("yes", "no"):
        out["confirmation"] = raw["confirmation"]
    return out


async def understand_utterance(text: str, awaiting_confirmation: bool = False, current_intent: Optional[str] = None) -> Dict[str, Any]:
    """Returns validated NLU fields for the utterance, or {} when Gemini is off/unavailable."""
    if not is_enabled() or not text.strip():
        return {}
    prompt = NLU_PROMPT.format(awaiting=awaiting_confirmation, intent=current_intent, text=json.dumps(text))
    raw = await _generate(prompt, json_mode=True)
    if not raw:
        return {}
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return _clean(json.loads(match.group(0))) if match else {}
    except Exception:
        return {}


async def ping() -> Dict[str, Any]:
    """Live connectivity check used by the integration status endpoint."""
    if not settings.GEMINI_API_KEY:
        return {"configured": False, "reachable": False, "detail": "GEMINI_API_KEY not set"}
    if not settings.USE_EXTERNAL_LLM:
        return {"configured": True, "reachable": False, "detail": "USE_EXTERNAL_LLM is disabled"}
    text = await _generate("Reply with the single word: ok", json_mode=False, timeout=8.0, force=True)
    return {
        "configured": True,
        "reachable": text is not None,
        "model": settings.GEMINI_MODEL,
        "detail": "OK" if text is not None else "Request failed (check key, model name and network)",
    }
