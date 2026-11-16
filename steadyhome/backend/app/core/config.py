import os
from datetime import datetime
from pydantic import BaseModel


def _load_dotenv() -> None:
    """Loads KEY=VALUE pairs from the project .env into os.environ (existing env vars win)."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    for candidate in (os.path.join(root, ".env"), os.path.join(root, "backend", ".env")):
        if not os.path.isfile(candidate):
            continue
        with open(candidate, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "SteadyHome – AI-Powered Loan EMI Voice Helpline"
    API_V1_STR: str = "/api"
    # Simulated current clock: 10 November 2026, 09:00:00
    DEFAULT_SIMULATED_NOW: str = "2026-11-10T09:00:00"
    CURRENT_SIMULATED_NOW: str = os.getenv("SIMULATED_NOW", "2026-11-10T09:00:00")
    
    # Database
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../steadyhome.db"))
    )

    # Gemini (LLM natural-language understanding). Disabled unless a key is present.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    USE_EXTERNAL_LLM: bool = os.getenv("USE_EXTERNAL_LLM", "true").lower() not in ("0", "false", "no")

    # Supabase (cloud persistence of escalations, interaction logs and transcripts)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")

    # Authentication (demo credentials; override in .env)
    AUTH_REQUIRED: bool = os.getenv("AUTH_REQUIRED", "true").lower() not in ("0", "false", "no")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "SteadyAdmin@2026")
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "steadyhome-demo-secret-change-me")
    AUTH_TOKEN_TTL_SECONDS: int = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "28800"))

    # Weather / Advisory
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast?latitude=19.0760&longitude=72.8777&current_weather=true"

    # Boundaries
    PART_PAYMENT_MIN_AMOUNT: float = 500.0
    LATE_FEE_TIER1_MAX_DAYS: int = 5   # <= 5 days: 2%
    LATE_FEE_TIER2_MAX_DAYS: int = 30  # <= 30 days: 4%
    MAX_OVERDUE_ONLINE_DAYS: int = 30  # > 30 days: escalate to human agent

    # Policy date for NetPay Plus and Branch Cash Desk discontinuation: 1 Jan 2027
    POLICY_CUTOFF_DATE: str = "2027-01-01"

    # Crisis exact prompt
    CRISIS_RESPONSE: str = (
        "I'm really sorry you're going through this. You are not alone, and help is available. "
        "If you are in immediate danger, please call 112 now. You can also call Tele-MANAS on "
        "14416, free and open at all hours, to talk to a trained counsellor. "
        "I'm connecting you with a person now."
    )

    # Financial advice exact prompt
    FINANCIAL_ADVICE_RESPONSE: str = (
        "I can provide information about your loan, but I cannot offer financial advice or recommend "
        "whether you should prepay. I can connect you with a human representative."
    )

    # Payment transfer disclaimer exact text
    PAYMENT_DISCLAIMER: str = (
        "Please note that applicable fees and payment receipts are subject to your lender's terms and conditions."
    )

settings = Settings()

def get_simulated_now() -> datetime:
    """Returns the current simulated clock as a datetime object."""
    try:
        return datetime.fromisoformat(settings.CURRENT_SIMULATED_NOW)
    except Exception:
        return datetime.fromisoformat(settings.DEFAULT_SIMULATED_NOW)

def set_simulated_now(new_iso: str):
    """Sets a new simulated datetime."""
    # Validate format
    dt = datetime.fromisoformat(new_iso)
    settings.CURRENT_SIMULATED_NOW = dt.isoformat()
    return settings.CURRENT_SIMULATED_NOW

def reset_simulated_now():
    """Resets the simulated clock to default: 2026-11-10T09:00:00."""
    settings.CURRENT_SIMULATED_NOW = settings.DEFAULT_SIMULATED_NOW
    return settings.CURRENT_SIMULATED_NOW

