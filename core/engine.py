"""
core/engine.py — Orchestration des sessions Nour-Net.

Nouveautes :
  - tor_newnym() : rotation de circuit Tor entre chaque dork
  - recheck_stale_zombies() : re-validation des zombies anciens en debut de session
  - validate_batch() : validation async parallele (x10 plus rapide)
  - Alertes Discord pour les zombies haute valeur (score >= threshold)
  - Persistance SQLite via core.db
"""

import random
import socket
import time
from typing import Callable, Dict, List, Optional

import requests

from core.scanner import NourScanner
from core.validator import NourValidator


EventEmitter = Callable[..., None]
StopChecker = Callable[[], bool]


def default_dorks() -> List[str]:
    return [
        '"Simple PHP Proxy script"',
        '"powered by PHProxy"',
        '"open web proxy" "anonymous browsing"',
        '"nph-proxy" "CGI Proxy"',
    ]


def emit_event(
    emit: Optional[EventEmitter],
    event: str,
    message: str,
    level: str = "info",
    data: Optional[Dict] = None,
) -> None:
    if callable(emit):
        emit(event=event, message=message, level=level, data=data or {})


def check_connection(proxy: str = "http://127.0.0.1:8118", timeout: int = 15) -> bool:
    proxies = {"http": proxy, "https": proxy}
    response = requests.get(
        "https://check.torproject.org/", proxies=proxies, timeout=timeout
    )
    return "Congratulations" in response.text


def tor_newnym(control_port: int = 9051) -> bool:
    """
    Demande a Tor un nouveau circuit (SIGNAL NEWNYM).
    Utilise stem pour l'authentification (cookie ou sans mot de passe).
    Retourne True si reussi, False sinon (sans lever d'exception).
    """
    try:
        from stem import Signal
        from stem.control import Controller

        with Controller.from_port(port=control_port) as ctrl:
            ctrl.authenticate()
            ctrl.signal(Signal.NEWNYM)
        return True
    except Exception:
        return False


def recheck_stale_zombies(
    proxy: str,
    emit: Optional[EventEmitter],
    max_age_hours: int = 24,
) -> None:
    """
    Re-valide les zombies vivants non verifies depuis max_age_hours.
    Marque les morts en DB. Emet des evenements pour le GUI.
    """
    from core.db import get_stale_zombies, init_db, mark_dead

    init_db()
    stale = get_stale_zombies(max_age_hours=max_age_hours)
    if not stale:
        return

    emit_event(
        emit,
        event="RECHECK_START",
        message=f"Re-verification de {len(stale)} zombie(s) ancien(s)",
        data={"count": len(stale)},
    )

    validator = NourValidator(proxy=proxy, emit=None, verbose=False)
    urls = [z["url"] for z in stale]
    results = validator.validate_batch(urls)

    dead_count = 0
    for r in results:
        if not r["alive"]:
            mark_dead(r["url"])
            dead_count += 1
            emit_event(
                emit,
                event="RECHECK_DEAD",
                message=f"[RECHECK-DEAD] {r['url']}",
                level="warning",
                data={"url": r["url"]},
            )

    emit_event(
        emit,
        event="RECHECK_DONE",
        message=f"Re-check termine : {dead_count} zombie(s) marques morts",
        data={"checked": len(stale), "dead": dead_count},
    )


def run_session(config: Dict, emit: Optional[EventEmitter] = None) -> Dict:
    """Wrapper pour compatibilite CLI — delogue vers run_session_with_stop."""
    return run_session_with_stop(config=config, emit=emit, should_stop=None)


def extract_host(url: str) -> Optional[str]:
    if not isinstance(url, str) or not url.strip():
        return None
    raw = url.strip()
    if "://" not in raw:
        raw = f"http://{raw}"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(raw)
        return parsed.hostname
    except Exception:
        return None


def geolocate_url(url: str, timeout: int = 6) -> Dict:
    host = extract_host(url)
    if not host:
        return {"ok": False, "reason": "host_invalid"}

    try:
        ip_address = socket.gethostbyname(host)
    except Exception:
        return {"ok": False, "reason": "dns_resolution_failed", "host": host}

    if (
        ip_address.startswith("127.")
        or ip_address.startswith("10.")
        or ip_address.startswith("192.168.")
    ):
        return {"ok": False, "reason": "private_ip", "host": host, "ip": ip_address}

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}",
            params={"fields": "status,message,country,countryCode,city,lat,lon,query,isp"},
            timeout=timeout,
        )
        payload = response.json()
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"geo_lookup_failed:{exc}",
            "host": host,
            "ip": ip_address,
        }

    if payload.get("status") != "success":
        return {
            "ok": False,
            "reason": payload.get("message", "geo_lookup_error"),
            "host": host,
            "ip": ip_address,
        }

    return {
        "ok": True,
        "host": host,
        "ip": payload.get("query", ip_address),
        "country": payload.get("country"),
        "country_code": payload.get("countryCode", ""),
        "city": payload.get("city"),
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
        "isp": payload.get("isp"),
    }


def run_session_with_stop(
    config: Dict,
    emit: Optional[EventEmitter] = None,
    should_stop: Optional[StopChecker] = None,
) -> Dict:
    dorks = config.get("dorks") or default_dorks()
    proxy = config.get("proxy", "http://127.0.0.1:8118")
    per_dork_limit = config.get("per_dork_limit", 10)
    pause_min = config.get("pause_min", 1)
    pause_max = config.get("pause_max", 2)
    check_tor_enabled = config.get("check_tor", True)
    alert_threshold = config.get("alert_threshold", 60)

    summary = {
        "dorks_total": len(dorks),
        "targets_found": 0,
        "targets_validated": 0,
        "alive": 0,
        "dead": 0,
        "saved": 0,
        "stopped": False,
    }

    emit_event(
        emit,
        event="SESSION_START",
        message="Session Nour-Net initialisee",
        data={"config": config},
    )

    if callable(should_stop) and should_stop():
        summary["stopped"] = True
        emit_event(
            emit,
            event="SESSION_STOPPED",
            message="Session arretee avant execution",
            level="warning",
        )
        return summary

    # -- Verification Tor -------------------------------------------------
    if check_tor_enabled:
        emit_event(emit, event="TOR_CHECK_START", message="Verification Tor/Privoxy")
        try:
            if not check_connection(proxy=proxy):
                emit_event(
                    emit,
                    event="SESSION_ABORTED",
                    message="Anonymat Tor non confirme",
                    level="error",
                )
                return summary
        except Exception as exc:
            emit_event(
                emit,
                event="SESSION_ABORTED",
                message=f"Echec verification Tor/Privoxy: {exc}",
                level="error",
            )
            return summary
        emit_event(emit, event="TOR_CHECK_OK", message="Tunnel Tor valide", level="success")

    # -- Re-check des zombies anciens -------------------------------------
    try:
        recheck_stale_zombies(proxy=proxy, emit=emit)
    except Exception:
        pass  # Ne jamais bloquer la session pour un re-check

    scanner = NourScanner(proxy=proxy, emit=emit, verbose=False)
    validator = NourValidator(
        proxy=proxy, emit=emit, verbose=False, alert_threshold=alert_threshold
    )

    all_valid_results: List[Dict] = []

    # -- Boucle principale dork -------------------------------------------
    for index, dork in enumerate(dorks, start=1):
        if callable(should_stop) and should_stop():
            summary["stopped"] = True
            emit_event(
                emit,
                event="SESSION_STOPPED",
                message="Session arretee par l'utilisateur",
                level="warning",
            )
            break

        # Rotation Tor entre les dorks (sauf le premier)
        if index > 1:
            changed = tor_newnym()
            emit_event(
                emit,
                event="TOR_NEWNYM",
                message="Nouveau circuit Tor demande" if changed else "NEWNYM indisponible (controle Tor desactive ?)",
                level="info" if changed else "warning",
                data={"success": changed},
            )

        pause = random.randint(pause_min, pause_max)
        emit_event(
            emit,
            event="DORK_WAIT",
            message=f"Pause anti-blocage: {pause}s",
            data={"seconds": pause, "dork": dork},
        )
        for _ in range(pause):
            if callable(should_stop) and should_stop():
                summary["stopped"] = True
                break
            time.sleep(1)
        if summary["stopped"]:
            break

        emit_event(
            emit,
            event="DORK_START",
            message=f"Dork {index}/{len(dorks)}: {dork}",
            data={"dork": dork, "index": index, "total": len(dorks)},
        )

        targets = scanner.search_zombies(dork, limit=per_dork_limit)
        summary["targets_found"] += len(targets)

        if targets:
            if callable(should_stop) and should_stop():
                summary["stopped"] = True
                break

            # Validation asynchrone en lot
            batch_results = validator.validate_batch(targets, dork=dork)
            summary["targets_validated"] += len(batch_results)

            for r in batch_results:
                if r["alive"]:
                    all_valid_results.append(r)
                    summary["alive"] += 1

                    # Alerte Discord si score suffisant
                    if r.get("score", 0) >= alert_threshold:
                        _send_alert_async(r["url"], r["score"], r.get("dork", dork))
                else:
                    summary["dead"] += 1

        emit_event(
            emit,
            event="DORK_DONE",
            message=f"Dork termine: {dork}",
            data={
                "dork": dork,
                "progress": index / max(len(dorks), 1),
                "running_summary": summary.copy(),
            },
        )

    # -- Sauvegarde -------------------------------------------------------
    if all_valid_results:
        validator.save_zombies(all_valid_results)

    summary["saved"] = len(all_valid_results)

    if not summary["stopped"]:
        if summary["targets_found"] == 0:
            emit_event(
                emit,
                event="SESSION_EMPTY",
                message="Aucune cible trouvee. Le moteur a pu limiter ou bloquer les requetes.",
                level="warning",
                data={"summary": summary.copy(), "reason": "no_targets_found"},
            )
        elif summary["alive"] == 0:
            emit_event(
                emit,
                event="SESSION_EMPTY",
                message="Cibles trouvees mais aucune validee.",
                level="warning",
                data={"summary": summary.copy(), "reason": "no_alive_targets"},
            )

    emit_event(
        emit,
        event="SESSION_DONE",
        message="Session terminee" + (" (arret manuel)" if summary["stopped"] else ""),
        level="warning" if summary["stopped"] else "success",
        data={"summary": summary, "alive_targets": [r["url"] for r in all_valid_results]},
    )
    return summary


def _send_alert_async(url: str, score: int, dork: str) -> None:
    """Envoie l'alerte Discord dans un thread dedie pour ne pas bloquer le scan."""
    import threading
    from core.alerts import send_discord_alert

    threading.Thread(
        target=send_discord_alert,
        kwargs={"url": url, "score": score, "dork": dork},
        daemon=True,
    ).start()

