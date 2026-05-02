"""
core/db.py — Persistance SQLite pour Nour-Net.

Remplace botnet/zombies.txt comme source de verite.
zombies.txt reste genere automatiquement pour la retrocompatibilite.
"""

import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "botnet" / "nour_net.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cree la table zombies si elle n'existe pas."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS zombies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                url         TEXT UNIQUE NOT NULL,
                score       INTEGER DEFAULT 0,
                status      TEXT DEFAULT 'alive',
                status_code INTEGER,
                latency_ms  INTEGER,
                first_seen  REAL NOT NULL,
                last_checked REAL NOT NULL,
                dork_source TEXT DEFAULT '',
                country     TEXT DEFAULT '',
                city        TEXT DEFAULT ''
            )
            """
        )
        conn.commit()


def upsert_zombie(
    url: str,
    score: int,
    status: str,
    status_code: Optional[int],
    latency_ms: Optional[int],
    dork_source: str = "",
    country: str = "",
    city: str = "",
) -> bool:
    """
    Insere ou met a jour un zombie.
    Retourne True si c'est une nouvelle entree.
    """
    now = time.time()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM zombies WHERE url = ?", (url,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE zombies
                SET score=?, status=?, status_code=?, latency_ms=?,
                    last_checked=?, dork_source=?, country=?, city=?
                WHERE url=?
                """,
                (score, status, status_code, latency_ms, now, dork_source, country, city, url),
            )
            conn.commit()
            return False
        else:
            conn.execute(
                """
                INSERT INTO zombies
                    (url, score, status, status_code, latency_ms,
                     first_seen, last_checked, dork_source, country, city)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (url, score, status, status_code, latency_ms, now, now, dork_source, country, city),
            )
            conn.commit()
            return True


def mark_dead(url: str) -> None:
    """Marque un zombie comme mort."""
    now = time.time()
    with get_connection() as conn:
        conn.execute(
            "UPDATE zombies SET status='dead', last_checked=? WHERE url=?",
            (now, url),
        )
        conn.commit()


def get_stale_zombies(max_age_hours: int = 24) -> List[Dict[str, Any]]:
    """
    Retourne les zombies vivants non verifies depuis max_age_hours.
    Utilise pour le re-check automatique.
    """
    cutoff = time.time() - max_age_hours * 3600
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT url, score FROM zombies WHERE last_checked < ? AND status = 'alive'",
            (cutoff,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_alive(min_score: int = 0) -> List[Dict[str, Any]]:
    """Retourne tous les zombies vivants tries par score decroissant."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM zombies WHERE status='alive' AND score >= ? ORDER BY score DESC",
            (min_score,),
        ).fetchall()
    return [dict(row) for row in rows]


def count_zombies() -> Dict[str, int]:
    """Retourne les compteurs total / alive / dead."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM zombies").fetchone()[0]
        alive = conn.execute(
            "SELECT COUNT(*) FROM zombies WHERE status='alive'"
        ).fetchone()[0]
        dead = conn.execute(
            "SELECT COUNT(*) FROM zombies WHERE status='dead'"
        ).fetchone()[0]
    return {"total": total, "alive": alive, "dead": dead}


def export_to_txt(relative_path: str = "botnet/zombies.txt") -> None:
    """
    Exporte les URLs des zombies vivants dans un fichier texte.
    Assure la retrocompatibilite avec l'ancien format.
    """
    rows = get_all_alive()
    txt_path = Path(__file__).resolve().parent.parent / relative_path
    with open(txt_path, "w") as f:
        for row in rows:
            f.write(row["url"] + "\n")
