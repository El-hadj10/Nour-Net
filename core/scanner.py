import requests # Importation de la bibliothèque pour effectuer des requêtes HTTP
from bs4 import BeautifulSoup # Importation de BeautifulSoup pour analyser le code HTML des pages
from colorama import Fore, Style # Importation de Colorama pour colorer les messages du terminal
from urllib.parse import quote_plus # Pour encoder les dorks dans l'URL de recherche
import random # Pour simuler un comportement humain par l'aléatoire

class NourScanner:
    def __init__(self, proxy="http://127.0.0.1:8118", emit=None, verbose=True):
        """Initialisation du scanner avec configuration du tunnel Tor/Privoxy et rotation d'identité"""
        # Configuration des proxys pour rediriger tout le trafic vers le port 8118 (Privoxy + Tor)
        self.proxies = {"http": proxy, "https": proxy}
        self.emit = emit
        self.verbose = verbose
        
        # Liste d'identités (User-Agents) pour éviter d'être marqué comme robot
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; rv:110.0) Gecko/20100101 Firefox/110.0"
        ]

    def _safe_emit(self, event, message, level="info", data=None):
        if callable(self.emit):
            self.emit(event=event, message=message, level=level, data=data or {})

    def _print(self, message):
        if self.verbose:
            print(message)

    def search_zombies(self, dork, limit=None):
        """Méthode principale optimisée pour scraper les résultats et contourner les filtres"""
        # Message d'information indiquant le début de la recherche
        self._print(f"{Fore.CYAN}[!] Nour-Net lance l'exploration pour : {dork}{Style.RESET_ALL}")
        self._safe_emit(
            event="SCAN_START",
            message=f"Exploration lancee pour: {dork}",
            data={"dork": dork}
        )
        
        # On prépare des en-têtes réalistes avec un User-Agent aléatoire et un Referer
        headers = {
            "User-Agent": random.choice(self.user_agents), # Choix d'une identité au hasard
            "Referer": "https://duckduckgo.com/", # Simulation d'une provenance réelle
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        # Construction de l'URL de recherche via Brave Search (compatible Tor)
        search_url = "https://search.brave.com/search?q=" + quote_plus(dork) + "&source=web"
        
        try:
            # Exécution de la requête avec un délai d'attente de 20 secondes
            response = requests.get(search_url, proxies=self.proxies, headers=headers, timeout=20)
            
            # Vérification du succès de la récupération
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                targets = []
                seen = set()
                
                # Extraction des liens de résultats Brave Search
                # On filtre les domaines internes Brave (brave.com, brave.app, etc.)
                BRAVE_INTERNAL = {"brave.com", "brave.app", "search.brave.com"}

                # Domaines de bruit connus (pas des proxies exploitables)
                NOISE_DOMAINS = {
                    "youtube.com", "wikipedia.org", "stackoverflow.com",
                    "reddit.com", "github.com", "packagist.org", "npmjs.com",
                    "pypi.org", "hackerone.com", "duckduckgo.com", "bing.com",
                    "google.com", "twitter.com", "facebook.com", "linkedin.com",
                    "medium.com", "dev.to", "docs.python.org", "ibm.com",
                    "microsoft.com", "learn.microsoft.com", "support.microsoft.com",
                    "kinsta.com", "geekflare.com", "wikihow.com",
                    "stackoverflow.com", "brightdata.com", "proxiesapi.com",
                    "sitepoint.com", "jonlabelle.com", "beamtic.com",
                    "benalman.com", "gist.github.com", "byteful.com",
                    "din-studio.com", "phpclasses.org",
                }

                # Mots-clés requis : au moins un doit apparaître dans l'URL
                PROXY_KEYWORDS = [
                    "proxy", "nph-", "cgi-bin", "phproxy", "glype",
                    "surrogafier", "anonymiz", "browse", "tunnel",
                ]

                def is_proxy_target(url: str) -> bool:
                    host = url.split('/')[2] if url.count('/') >= 2 else ''
                    # Rejeter les domaines de bruit
                    for noise in NOISE_DOMAINS:
                        if host == noise or host.endswith('.' + noise):
                            return False
                    # Rejeter les URLs sans mot-clé proxy
                    url_lower = url.lower()
                    return any(kw in url_lower for kw in PROXY_KEYWORDS)

                for link in soup.find_all('a', href=True):
                    url_trouvee = link['href']
                    if not url_trouvee.startswith('http'):
                        continue
                    # Exclure les pages internes de Brave
                    host = url_trouvee.split('/')[2] if url_trouvee.count('/') >= 2 else ''
                    if any(host == b or host.endswith('.' + b) for b in BRAVE_INTERNAL):
                        continue
                    clean_url = url_trouvee.split('?')[0] if '?' in url_trouvee else url_trouvee
                    # Filtre pertinence : garder uniquement les cibles proxy
                    if not is_proxy_target(clean_url):
                        continue
                    if clean_url not in seen:
                        seen.add(clean_url)
                        targets.append(clean_url)
                        self._safe_emit(
                            event="TARGET_FOUND",
                            message=f"Cible potentielle trouvee: {clean_url}",
                            data={"dork": dork, "url": clean_url}
                        )

                    if limit is not None and len(targets) >= limit:
                        break

                self._print(f"{Fore.GREEN}[+] {len(targets)} cibles potentielles extraites de la Lumière.{Style.RESET_ALL}")
                self._safe_emit(
                    event="SCAN_DONE",
                    message=f"{len(targets)} cibles potentielles extraites",
                    data={"dork": dork, "count": len(targets)}
                )
                return targets
            
            elif response.status_code == 403:
                self._print(f"{Fore.RED}[!] Acces refuse (403) par Brave Search — noeud Tor bloque.{Style.RESET_ALL}")
                self._safe_emit(
                    event="SCAN_BLOCKED",
                    message="Acces refuse (403) par Brave Search — change de circuit Tor",
                    level="warning",
                    data={"dork": dork, "status_code": 403}
                )
                
        except Exception as e:
            # Affichage de l'erreur en cas de problème technique
            self._print(f"{Fore.RED}[ERROR] Échec de l'exploration : {e}{Style.RESET_ALL}")
            self._safe_emit(
                event="SCAN_ERROR",
                message=f"Echec de l'exploration: {e}",
                level="error",
                data={"dork": dork}
            )
            
        return [] # Retourne une liste vide par défaut