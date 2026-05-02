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


def emit_event(emit: Optional[EventEmitter], event: str, message: str, level: str = "info", data: Optional[Dict] = None) -> None:
    if callable(emit):
        emit(event=event, message=message, level=level, data=data or {})


def check_connection(proxy: str = "http://127.0.0.1:8118", timeout: int = 15) -> bool:
    proxies = {"http": proxy, "https": proxy}
    response = requests.get("https://check.torproject.org/", proxies=proxies, timeout=timeout)
    return "Congratulations" in response.text


def run_session(config: Dict, emit: Optional[EventEmitter] = None) -> Dict:
    dorks = config.get("dorks") or default_dorks()
    proxy = config.get("proxy", "http://127.0.0.1:8118")
    per_dork_limit = config.get("per_dork_limit", 10)
    pause_min = config.get("pause_min", 1)
    pause_max = config.get("pause_max", 2)
    check_tor_enabled = config.get("check_tor", True)

    summary = {
        "dorks_total": len(dorks),
        "targets_found": 0,
        "targets_validated": 0,
        "alive": 0,
        "dead": 0,
        "saved": 0,
    }

    emit_event(
        emit,
        event="SESSION_START",
        message="Session Nour-Net initialisee",
        data={"config": config},
    )

    if check_tor_enabled:
        emit_event(
            emit,
            event="TOR_CHECK_START",
            message="Verification de la protection Tor/Privoxy",
        )
        try:
            if not check_connection(proxy=proxy):
                emit_event(
                    emit,
                    event="SESSION_ABORTED",
                    message="Connexion etablie mais anonymat Tor non confirme",
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
        emit_event(
            emit,
            event="TOR_CHECK_OK",
            message="Tunnel Tor valide",
            level="success",
        )

    scanner = NourScanner(proxy=proxy, emit=emit, verbose=False)
    validator = NourValidator(proxy=proxy, emit=emit, verbose=False)

    all_valid_zombies: List[str] = []

    for index, dork in enumerate(dorks, start=1):
        pause = random.randint(pause_min, pause_max)
        emit_event(
            emit,
            event="DORK_WAIT",
            message=f"Pause anti-blocage: {pause}s",
            data={"seconds": pause, "dork": dork},
        )
        time.sleep(pause)

        emit_event(
            emit,
            event="DORK_START",
            message=f"Analyse du dork {index}/{len(dorks)}: {dork}",
            data={"dork": dork, "index": index, "total": len(dorks)},
        )

        targets = scanner.search_zombies(dork, limit=per_dork_limit)
        summary["targets_found"] += len(targets)

        for target in targets:
            is_alive = validator.validate_zombie(target)
            summary["targets_validated"] += 1
            if is_alive:
                all_valid_zombies.append(target)
                summary["alive"] += 1
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

    if all_valid_zombies:
        validator.save_zombies(all_valid_zombies)

    summary["saved"] = len(all_valid_zombies)

    if summary["targets_found"] == 0:
        emit_event(
            emit,
            event="SESSION_EMPTY",
            message="Aucune cible trouvee. Le moteur peut avoir limite ou bloque la recherche.",
            level="warning",
            data={"summary": summary.copy()},
        )

    emit_event(
        emit,
        event="SESSION_DONE",
        message="Session terminee",
        level="success",
        data={"summary": summary, "alive_targets": all_valid_zombies},
    )
    return summary


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

    if ip_address.startswith("127.") or ip_address.startswith("10.") or ip_address.startswith("192.168."):
        return {"ok": False, "reason": "private_ip", "host": host, "ip": ip_address}

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}",
            params={"fields": "status,message,country,city,lat,lon,query,isp"},
            timeout=timeout,
        )
        payload = response.json()
    except Exception as exc:
        return {"ok": False, "reason": f"geo_lookup_failed:{exc}", "host": host, "ip": ip_address}

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
        "city": payload.get("city"),
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
        "isp": payload.get("isp"),
    }


def run_session_with_stop(config: Dict, emit: Optional[EventEmitter] = None, should_stop: Optional[StopChecker] = None) -> Dict:
    dorks = config.get("dorks") or default_dorks()
    proxy = config.get("proxy", "http://127.0.0.1:8118")
    per_dork_limit = config.get("per_dork_limit", 10)
    pause_min = config.get("pause_min", 1)
    pause_max = config.get("pause_max", 2)
    check_tor_enabled = config.get("check_tor", True)

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
        emit_event(emit, event="SESSION_STOPPED", message="Session arretee avant execution", level="warning")
        return summary

    if check_tor_enabled:
        emit_event(
            emit,
            event="TOR_CHECK_START",
            message="Verification de la protection Tor/Privoxy",
        )
        try:
            if not check_connection(proxy=proxy):
                emit_event(
                    emit,
                    event="SESSION_ABORTED",
                    message="Connexion etablie mais anonymat Tor non confirme",
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
        emit_event(
            emit,
            event="TOR_CHECK_OK",
            message="Tunnel Tor valide",
            level="success",
        )

    scanner = NourScanner(proxy=proxy, emit=emit, verbose=False)
    validator = NourValidator(proxy=proxy, emit=emit, verbose=False)

    all_valid_zombies: List[str] = []

    for index, dork in enumerate(dorks, start=1):
        if callable(should_stop) and should_stop():
            summary["stopped"] = True
            emit_event(emit, event="SESSION_STOPPED", message="Session arretee par l'utilisateur", level="warning")
            break

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
                emit_event(emit, event="SESSION_STOPPED", message="Session arretee pendant la pause", level="warning")
                break
            time.sleep(1)
        if summary["stopped"]:
            break

        emit_event(
            emit,
            event="DORK_START",
            message=f"Analyse du dork {index}/{len(dorks)}: {dork}",
            data={"dork": dork, "index": index, "total": len(dorks)},
        )

        targets = scanner.search_zombies(dork, limit=per_dork_limit)
        summary["targets_found"] += len(targets)

        for target in targets:
            if callable(should_stop) and should_stop():
                summary["stopped"] = True
                emit_event(emit, event="SESSION_STOPPED", message="Session arretee pendant la validation", level="warning")
                break
            is_alive = validator.validate_zombie(target)
            summary["targets_validated"] += 1
            if is_alive:
                all_valid_zombies.append(target)
                summary["alive"] += 1
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
        if summary["stopped"]:
            break

    if all_valid_zombies:
        validator.save_zombies(all_valid_zombies)

    summary["saved"] = len(all_valid_zombies)

    if not summary["stopped"]:
        if summary["targets_found"] == 0:
            emit_event(
                emit,
                event="SESSION_EMPTY",
                message="Session terminee sans resultat: le moteur de recherche a pu limiter ou bloquer les requetes.",
                level="warning",
                data={"summary": summary.copy(), "reason": "no_targets_found"},
            )
        elif summary["alive"] == 0:
            emit_event(
                emit,
                event="SESSION_EMPTY",
                message="Session terminee: des cibles ont ete trouvees mais aucune n'a ete validee.",
                level="warning",
                data={"summary": summary.copy(), "reason": "no_alive_targets"},
            )

    if summary["stopped"]:
        emit_event(
            emit,
            event="SESSION_DONE",
            message="Session terminee (arret manuel)",
            level="warning",
            data={"summary": summary, "alive_targets": all_valid_zombies},
        )
    else:
        emit_event(
            emit,
            event="SESSION_DONE",
            message="Session terminee",
            level="success",
            data={"summary": summary, "alive_targets": all_valid_zombies},
        )

    return summary
