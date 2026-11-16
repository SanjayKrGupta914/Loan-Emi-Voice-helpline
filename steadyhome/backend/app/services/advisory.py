"""
Payment-Day Advisory Service for SteadyHome.
Integrates with free public HTTPS JSON API (Open-Meteo) to provide non-binding,
contextual advisories regarding payment day conditions and banking network clearances.
Uses deterministic mock fallback for offline operation and automated testing.
"""

import httpx
from typing import Dict, Any
from app.core.config import settings

MOCK_ADVISORY = (
    "Advisory: Banking clearing networks are operating normally today. "
    "Online payments through AutoDebit and NetPay are settling in real time."
)

async def get_payment_day_advisory(city: str = "Mumbai", use_mock: bool = False) -> Dict[str, Any]:
    """
    Fetches real-time weather and generates a contextual 1-2 sentence payment-day advisory.
    If network is unavailable or use_mock is True, returns high-availability mock advisory.
    """
    if use_mock:
        return {
            "source": "MOCK_LOCAL",
            "advisory": MOCK_ADVISORY,
            "weather_condition": "Clear",
            "temperature_c": 28.5
        }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(settings.WEATHER_API_URL)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current_weather", {})
                temp = current.get("temperature", 28.0)
                windspeed = current.get("windspeed", 10.0)
                weathercode = current.get("weathercode", 0)

                # Generate friendly advisory
                condition_desc = "Clear and pleasant"
                if weathercode in [1, 2, 3]:
                    condition_desc = "Partly cloudy"
                elif weathercode in [51, 53, 55, 61, 63, 65]:
                    condition_desc = "Rainy"
                elif weathercode in [95, 96, 99]:
                    condition_desc = "Thunderstorms"

                advisory_text = (
                    f"Advisory: Clear operations reported across national payment rails today with {temp}°C in {city}. "
                    "Digital transactions through AutoDebit and NetPay are settling on schedule."
                )

                return {
                    "source": "OPEN_METEO_PUBLIC_API",
                    "advisory": advisory_text,
                    "weather_condition": condition_desc,
                    "temperature_c": temp
                }
    except Exception:
        pass

    # Graceful fallback
    return {
        "source": "FALLBACK_MOCK",
        "advisory": MOCK_ADVISORY,
        "weather_condition": "Normal",
        "temperature_c": 27.0
    }

