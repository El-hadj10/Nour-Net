"""
core/scanner.py — Scraping multi-moteurs pour Nour-Net.

Moteurs supportes :
  - Brave Search (clearnet, compatible Tor)
  - Ahmia (moteur de recherche specialise Tor/proxy, clearnet frontend)

Le filtre de pertinence is_proxy_target() est applique avant d'emettre TARGET_FOUND.
"""

import random
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style

# ---------------------------------------------------------------------------
# Constantes de filtrage — niveau module pour etre testables
# ---------------------------------------------------------------------------

BRAVE_INTERNAL = {"brave.com", "brave.app", "search.brave.com"}

AHMIA_INTERNAL = {"ahmia.fi"}

NOISE_DOMAINS = {
    "youtube.com", "wikipedia.org", "stackoverflow.com",
    "reddit.com", "github.com", "packagist.org", "npmjs.com",
    "pypi.org", "hackerone.com", "duckduckgo.com", "bing.com",
    "google.com", "twitter.com", "facebook.com", "linkedin.com",
    "medium.com", "dev.to", "docs.python.org", "ibm.com",
    "microsoft.com", "learn.microsoft.com", "support.microsoft.com",
    "kinsta.com", "geekflare.com", "wikihow.com",
    "brightdata.com", "proxiesapi.com",
    "sitepoint.com", "jonlabelle.com", "beamtic.com",
    "benalman.com", "gist.github.com", "byteful.com",
    "din-studio.com", "phpclasses.org",
}

PROXY_KEYWORDS = [
    "proxy", "nph-", "cgi-bin", "phproxy", "glype",
    "surrogafier", "anonymiz", "browse", "tunnel",
]


def is_proxy_target(url: str) -> bool:
    """
    Retourne True si l'URL est une cible proxy pertinente :
    - n'appartient pas aux domaines de bruit
    - contient au moins un mot-cle proxy
    """
    if url.count("/") < 2:
        return False
    host = url.split("/")[2]
    for noise in NOISE_DOMAINS:
        if host == noise or host.endswith("." + noise):
            return False
    url_lower = url.lower()
    return any(kw in url_lower for kw in PROXY_KEYWORDS)


def _extract_host(url: str) -> str:
    return url.split("/")[2] if url.count("/") >= 2 else ""


# ---------------------------------------------------------------------------
# Scanner principal
# ---------------------------------------------------------------------------

class NourScanner:
    def __init__(self, proxy: str = "http://127.0.0.1:8118", emit=None, verbose: bool = True):
        self.proxies = {"http": proxy, "https": proxy}
        self.emit = emit
        self.verbose = verbose
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; rv:110.0) Gecko/20100101 Firefox/110.0",
        ]

    def _safe_emit(self, event: str, message: str, level: str = "info", data=None) -> None:
        if callable(self.emit):
            self.emit(event=event, message=message, level=level, data=data or {})

    def _print(self, message: str) -> None:
        if self.verbose:
            print(message)

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Referer": "https://search.brave.com/",
            "Accept-Language": "en-US,en;q=0.5",
        }

    # ------------------------------------------------------------------
    # Moteur 1 : Brave Search
    # ------------------------------------------------------------------

    def _search_brave(self, dork: str, limit: int) -> list:
        """Scrape Brave Search et retourne les URLs pertinentes."""
        search_url = "https://search.brave.com/search?q=" + quote_plus(dork) + "&source=web"
        try:
            response = requests.get(
                search_url, proxies=self.proxies, headers=self._headers(), timeout=20
            )
            if response.status_code == 403:
                self._safe_emit(
                    "SCAN_BLOCKED",
                    "Acces refuse (403) par Brave Search — circuit Tor bloque",
                    level="warning",
                    data={"dork": dork, "engine": "brave"},
                )
                return []
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            found = []
            seen: set = set()
            for link in soup.find_all("a", href=True):
                url = link["href"]
                if not url.startswith("http"):
                    continue
                host = _extract_host(url)
                if any(host == b or host.endswith("." + b) for b in BRAVE_INTERNAL):
                    continue
                clean = url.split("?")[0] if "?" in url else url
                if not is_proxy_target(clean) or clean in seen:
                    continue
                seen.add(clean)
                found.append(clean)
                if len(found) >= limit:
                    break
            return found
        except Exception as exc:
            self._safe_emit(
                "SCAN_ERROR",
                f"Brave Search — erreur: {exc}",
                level="error",
                data={"dork": dork, "engine": "brave"},
            )
            return []

    # ------------------------------------------------------------------
    # Moteur 2 : Ahmia (frontend clearnet, indexe les proxies Tor/web)
    # ------------------------------------------------------------------

    def _search_ahmia(self, dork: str, limit: int) -> list:
        """Scrape Ahmia et retourne les URLs pertinentes."""
        search_url = "https://ahmia.fi/search/?q=" + quote_plus(dork)
        try:
            response = requests.get(
                search_url, proxies=self.proxies, headers=self._headers(), timeout=20
            )
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            found = []
            seen: set = set()
            # Ahmia structure : <li class="result"> ... <h4><a href="...">
            for link in soup.select("li.result a[href]"):
                url = link["href"]
                if not url.startswith("http"):
                    continue
                host = _extract_host(url)
                if any(host == a or host.endswith("." + a) for a in AHMIA_INTERNAL):
                    continue
                clean = url.split("?")[0] if "?" in url else url
                if not is_proxy_target(clean) or clean in seen:
                    continue
                seen.add(clean)
                found.append(clean)
                if len(found) >= limit:
                    break
            return found
        except Exception as exc:
            self._safe_emit(
                "SCAN_ERROR",
                f"Ahmia — erreur: {exc}",
                level="error",
                data={"dork": dork, "engine": "ahmia"},
            )
            return []

    # ------------------------------------------------------------------
    # Point d'entree principal
    # ------------------------------------------------------------------

    def search_zombies(self, dork: str, limit: int = None) -> list:
        """
        Scrape Brave Search + Ahmia en parallele (sequentiel ici, fusionne les resultats).
        Les doublons inter-moteurs sont elimines.
        """
        effective_limit = limit or 20

        self._print(f"{Fore.CYAN}[!] Exploration : {dork}{Style.RESET_ALL}")
        self._safe_emit(
            "SCAN_START",
            f"Exploration lancee pour: {dork}",
            data={"dork": dork},
        )

        brave_results = self._search_brave(dork, effective_limit)
        self._safe_emit(
            "ENGINE_DONE",
            f"Brave Search : {len(brave_results)} cibles",
            data={"engine": "brave", "count": len(brave_results)},
        )

        ahmia_results = self._search_ahmia(dork, effective_limit)
        self._safe_emit(
            "ENGINE_DONE",
            f"Ahmia : {len(ahmia_results)} cibles",
            data={"engine": "ahmia", "count": len(ahmia_results)},
        )

        # Fusion sans doublons, priorite aux resultats Brave
        seen: set = set()
        targets = []
        for url in brave_results + ahmia_results:
            if url not in seen:
                seen.add(url)
                targets.append(url)
                self._safe_emit(
                    "TARGET_FOUND",
                    f"Cible potentielle: {url}",
                    data={"dork": dork, "url": url},
                )
            if limit is not None and len(targets) >= limit:
                break

        self._print(
            f"{Fore.GREEN}[+] {len(targets)} cibles extraites (Brave+Ahmia).{Style.RESET_ALL}"
        )
        self._safe_emit(
            "SCAN_DONE",
            f"{len(targets)} cibles potentielles extraites",
            data={"dork": dork, "count": len(targets)},
        )
        return targets


