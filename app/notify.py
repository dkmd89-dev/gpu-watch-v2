import os
import json
import logging
import requests

log = logging.getLogger(__name__)

# ⭐ Top-Deal, 👍 guter Preis, ⚠️ okay, 💰 Fallback (unbekannte/fehlende Bewertung)
DEAL_EMOJI = {
    "Top-Deal": "⭐",
    "Guter Preis": "👍",
    "Okay": "⚠️",
}
DEAL_EMOJI_FALLBACK = "💰"

# Dashboard-Badge (feste Sternezahl je regelbasiertem deal_rating,
# unabhaengig vom dynamisch berechneten deal_score/deal_stars aus
# scoring/deal_score.py -- siehe app.py "deal_rating_badge_stars"). Bewusst
# nur fuer "Top-Deal"/"Guter Preis" definiert; "Okay" bekommt kein eigenes
# Sterne-Badge im Dashboard.
DEAL_RATING_STARS = {
    "Top-Deal": "★★★★★",
    "Guter Preis": "★★★☆☆",
}


def emoji_for(deal_rating: str | None) -> str:
    return DEAL_EMOJI.get(deal_rating or "", DEAL_EMOJI_FALLBACK)


def rating_stars_for(deal_rating: str | None) -> str | None:
    """Feste Sternezahl fuers Dashboard-Rating-Badge, None wenn deal_rating
    nicht "Top-Deal"/"Guter Preis" ist (z.B. "Okay" oder kein Treffer)."""
    return DEAL_RATING_STARS.get(deal_rating or "")


def send_ntfy(title: str, message: str, priority: str = "default", tags: list[str] | None = None):
    """Sendet eine ntfy-Benachrichtigung über die JSON-API (nicht per HTTP-Header).

    Das unterstützt volles UTF-8 im Titel (Emojis!) ohne die Latin-1-Encoding-
    Probleme, die bei Emojis in HTTP-Headern häufig auftreten (siehe
    https://docs.ntfy.sh/publish/#publish-as-json).
    """
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        log.warning("NTFY_TOPIC nicht gesetzt, Benachrichtigung wird übersprungen.")
        return

    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh")

    payload = {
        "topic": topic,
        "title": title,
        "message": message,
        "priority": {"min": 1, "low": 2, "default": 3, "high": 4, "urgent": 5}.get(priority, 3),
    }
    if tags:
        payload["tags"] = tags

    log.info(f"Sende ntfy: {title} (Priority: {priority})")
    log.debug(f"   Message: {message[:100]}...")

    try:
        response = requests.post(
            server,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=10,
        )

        if response.status_code == 200:
            log.info(f"ntfy-Benachrichtigung gesendet: {title}")
        else:
            log.warning(f"ntfy-Fehler (HTTP {response.status_code}): {response.text[:200]}")

    except requests.RequestException as e:
        log.error(f"ntfy-Verbindungsfehler: {e}", exc_info=True)
