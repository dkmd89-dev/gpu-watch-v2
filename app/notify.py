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


def emoji_for(deal_rating: str | None) -> str:
    return DEAL_EMOJI.get(deal_rating or "", DEAL_EMOJI_FALLBACK)


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
