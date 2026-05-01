import requests # Importation de la bibliothèque pour effectuer des requêtes HTTP
from bs4 import BeautifulSoup # Importation de BeautifulSoup pour analyser le code HTML des pages
from colorama import Fore, Style # Importation de Colorama pour colorer les messages du terminal
import random # Pour simuler un comportement humain par l'aléatoire

class NourScanner:
    def __init__(self, proxy="http://127.0.0.1:8118"):
        """Initialisation du scanner avec configuration du tunnel Tor/Privoxy et rotation d'identité"""
        # Configuration des proxys pour rediriger tout le trafic vers le port 8118 (Privoxy + Tor)
        self.proxies = {"http": proxy, "https": proxy}
        
        # Liste d'identités (User-Agents) pour éviter d'être marqué comme robot
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; rv:110.0) Gecko/20100101 Firefox/110.0"
        ]

    def search_zombies(self, dork):
        """Méthode principale optimisée pour scraper les résultats et contourner les filtres"""
        # Message d'information indiquant le début de la recherche
        print(f"{Fore.CYAN}[!] Nour-Net lance l'exploration pour : {dork}{Style.RESET_ALL}")
        
        # On prépare des en-têtes réalistes avec un User-Agent aléatoire et un Referer
        headers = {
            "User-Agent": random.choice(self.user_agents), # Choix d'une identité au hasard
            "Referer": "https://duckduckgo.com/", # Simulation d'une provenance réelle
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        # Construction de l'URL de recherche via DuckDuckGo (version HTML)
        search_url = f"https://html.duckduckgo.com/html/?q={dork}"
        
        try:
            # Exécution de la requête avec un délai d'attente de 20 secondes
            response = requests.get(search_url, proxies=self.proxies, headers=headers, timeout=20)
            
            # Vérification du succès de la récupération
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                targets = []
                
                # Extraction de tous les liens en filtrant les résultats internes
                for link in soup.find_all('a', href=True):
                    url_trouvee = link['href']
                    if "http" in url_trouvee and "duckduckgo" not in url_trouvee:
                        # Nettoyage basique pour éviter les doublons avec paramètres
                        clean_url = url_trouvee.split('&')[0] if 'uddg=' not in url_trouvee else url_trouvee
                        targets.append(clean_url)
                
                # Suppression des doublons pour une liste propre
                targets = list(set(targets))
                
                print(f"{Fore.GREEN}[+] {len(targets)} cibles potentielles extraites de la Lumière.{Style.RESET_ALL}")
                return targets
            
            elif response.status_code == 403:
                print(f"{Fore.RED}[!] Accès refusé (403). Le moteur bloque ton nœud Tor actuel.{Style.RESET_ALL}")
                
        except Exception as e:
            # Affichage de l'erreur en cas de problème technique
            print(f"{Fore.RED}[ERROR] Échec de l'exploration : {e}{Style.RESET_ALL}")
            
        return [] # Retourne une liste vide par défaut