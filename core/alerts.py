"""
core/alerts.py — Alertes Discord pour Nour-Net.

Configure DISCORD_WEBHOOK_URL dans un fichier .env ou en variable d'environnement.
Les alertes sont envoyees uniquement pour les zombies dont le score >= ALERT_SCORE_THRESHOLD.
"""

import os
from typing import Optional

import requests

ALERT_SCORE_THRESHOLD = 60


def send_discord_alert(
    url: str,
    score: int,
    country: str = "",
    dork: str = "",
) -> bool:
    """
    Envoie un embed Discord quand un zombie haute valeur est detecte.
    Retourne True si l'envoi a reussi, False sinon (webhook absent, erreur reseau...).
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return False

    color = 0x22C55E if score >= 80 else 0x0EA5E9  # vert si excellent, bleu sinon
    flag = _country_to_flag(country)

    embed = {
        "title": "\U0001f7e2 Nour-Net — Zombie haute valeur detecte",
        "color": color,
        "fields": [
            {"name": "URL", "value": f"`{url}`", "inline": False},
            {"name": "Score", "value": f"**{score}/100**", "inline": True},
            {
                "name": "Pays",
                "value": f"{flag} {country}".strip() if country else "—",
                "inline": True,
            },
            {
                "name": "Dork source",
                "value": f"`{dork}`" if dork else "—",
                "inline": False,
            },
        ],
        "footer": {"text": "Nour-Net Command Center"},
    }

    try:
        resp = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=5,
        )
        return resp.status_code in (200, 204)
    except Exception:
        return False


def _country_to_flag(country_code: str) -> str:
    """Convertit un code pays ISO 3166-1 alpha-2 en emoji drapeau Unicode."""
    if not country_code or len(country_code) < 2:
        return ""
    try:
        return "".join(
            chr(0x1F1E0 + ord(c) - ord("A"))
            for c in country_code.upper()[:2]
        )
    except Exception:
        return ""
