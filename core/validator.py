"""
core/validator.py — Validation HTTP asynchrone avec scoring pour Nour-Net.

Utilise aiohttp pour valider plusieurs cibles en parallele (jusqu'a 10 concurrentes).
Chaque cible recoit un score 0-100 base sur : status HTTP, latence, profondeur des mots-cles proxy.
"""

import asyncio
import time
from typing import Dict, List, Optional

import aiohttp
from colorama import Fore, Style

# Mots-cles proxy utilises pour le scoring et le filtre pertinence
PROXY_KEYWORDS = [
    "proxy", "nph-", "cgi-bin", "phproxy", "glype",
    "surrogafier", "anonymiz", "browse", "tunnel",
]

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)


def compute_score(
    status_code: Optional[int],
    latency_ms: Optional[int],
    url: str,
) -> int:
    """
    Calcule un score de qualite 0-100 pour une cible :
    - Status HTTP  : 200 = 50pts, 301/302 = 30pts
    - Latence      : uniquement si alive — <2s = 30pts, <5s = 15pts, <10s = 5pts
    - Mots-cles    : chaque mot-cle proxy dans l'URL = 4pts (max 20)
    """
    score = 0
    alive = status_code in (200, 301, 302)

    if status_code == 200:
        score += 50
    elif status_code in (301, 302):
        score += 30

    if alive and latency_ms is not None:
        if latency_ms < 2000:
            score += 30
        elif latency_ms < 5000:
            score += 15
        elif latency_ms < 10000:
            score += 5

    url_lower = url.lower()
    kw_count = sum(1 for kw in PROXY_KEYWORDS if kw in url_lower)
    score += min(kw_count * 4, 20)

    return min(score, 100)


class NourValidator:
    def __init__(
        self,
        proxy: str = "http://127.0.0.1:8118",
        emit=None,
        verbose: bool = True,
        concurrency: int = 10,
        alert_threshold: int = 60,
    ):
        self.proxy = proxy
        self.emit = emit
        self.verbose = verbose
        self.concurrency = concurrency
        self.alert_threshold = alert_threshold
        self.headers = {"User-Agent": _USER_AGENT}

    def _safe_emit(self, event: str, message: str, level: str = "info", data: Optional[Dict] = None) -> None:
        if callable(self.emit):
            self.emit(event=event, message=message, level=level, data=data or {})

    def _print(self, message: str) -> None:
        if self.verbose:
            print(message)

    async def _validate_one(
        self,
        session: aiohttp.ClientSession,
        url: str,
        dork: str = "",
    ) -> Dict:
        """Valide une URL de facon asynchrone via HEAD puis fallback GET."""
        result: Dict = {
            "url": url,
            "alive": False,
            "status_code": None,
            "latency_ms": None,
            "score": 0,
            "dork": dork,
        }
        self._safe_emit("VALIDATION_START", f"Validation: {url}", data={"url": url})
        start = time.time()
        try:
            async with session.head(
                url,
                proxy=self.proxy,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                code = resp.status
                if code == 405:
                    async with session.get(
                        url,
                        proxy=self.proxy,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp2:
                        code = resp2.status
                latency = int((time.time() - start) * 1000)
                result["status_code"] = code
                result["latency_ms"] = latency
                result["alive"] = code in (200, 301, 302)
                result["score"] = compute_score(code, latency, url)
        except Exception:
            result["alive"] = False
        return result

    async def _run_batch(self, urls: List[str], dork: str = "") -> List[Dict]:
        sem = asyncio.Semaphore(self.concurrency)
        connector = aiohttp.TCPConnector(limit=self.concurrency, ssl=False)

        async def bounded(url: str) -> Dict:
            async with sem:
                return await self._validate_one(session, url, dork)

        async with aiohttp.ClientSession(connector=connector, headers=self.headers) as session:
            return list(await asyncio.gather(*[bounded(u) for u in urls]))

    def validate_batch(self, urls: List[str], dork: str = "") -> List[Dict]:
        """
        Valide une liste d'URLs en parallele (mode async dans un event loop dedie).
        Retourne une liste de dicts {url, alive, status_code, latency_ms, score, dork}.
        """
        if not urls:
            return []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self._run_batch(urls, dork))
        finally:
            loop.close()
            asyncio.set_event_loop(None)

        for r in results:
            if r["alive"]:
                self._print(
                    f"{Fore.GREEN}[ALIVE] {r['url']} "
                    f"(score={r['score']}, {r['latency_ms']}ms){Style.RESET_ALL}"
                )
                self._safe_emit(
                    "TARGET_VALIDATED",
                    f"[ALIVE] {r['url']} score={r['score']}",
                    level="success",
                    data=r,
                )
            else:
                self._print(f"{Fore.YELLOW}[DEAD] {r['url']}{Style.RESET_ALL}")
                self._safe_emit(
                    "TARGET_VALIDATED",
                    f"[DEAD] {r['url']}",
                    level="warning",
                    data=r,
                )
        return results

    def validate_zombie(self, url: str) -> bool:
        """Retrocompatibilite CLI : validation unitaire, retourne un booleen."""
        results = self.validate_batch([url])
        return results[0]["alive"] if results else False

    def save_zombies(self, valid_results, filename: str = "botnet/zombies.txt") -> None:
        """Persiste les zombies valides en SQLite puis exporte zombies.txt."""
        from core.db import export_to_txt, init_db, upsert_zombie

        init_db()
        added = 0
        for item in valid_results:
            if isinstance(item, dict):
                is_new = upsert_zombie(
                    url=item["url"],
                    score=item.get("score", 0),
                    status="alive",
                    status_code=item.get("status_code"),
                    latency_ms=item.get("latency_ms"),
                    dork_source=item.get("dork", ""),
                )
            else:
                is_new = upsert_zombie(
                    url=item,
                    score=0,
                    status="alive",
                    status_code=None,
                    latency_ms=None,
                )
            if is_new:
                added += 1

        export_to_txt(filename)
        self._print(
            f"{Fore.BLUE}[INFO] {added} nouveaux zombies sauvegardes en DB{Style.RESET_ALL}"
        )
        self._safe_emit(
            "SAVE_DONE",
            f"{added} nouveaux zombies sauvegardes",
            data={"added": added, "total_session": len(valid_results)},
        )