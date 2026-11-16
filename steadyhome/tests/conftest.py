import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.core.config import settings


@pytest.fixture(autouse=True)
def isolate_external_services(monkeypatch):
    """Tests never call the real Gemini or write to the real Supabase project from .env."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "")
    monkeypatch.setattr(settings, "AUTH_REQUIRED", False)  # auth has its own tests (test_auth.py)
