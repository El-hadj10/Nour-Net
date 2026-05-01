import requests # Importation de la bibliothèque pour effectuer des requêtes HTTP
from bs4 import BeautifulSoup # Importation de BeautifulSoup pour analyser le code HTML des pages
from colorama import Fore, Style # Importation de Colorama pour colorer les messages du terminal

class NourScanner:
    def __init__(self, proxy="http://127.0.0.1:8118"):
        """Initialisation du scanner avec configuration du tunnel Tor/Privoxy"""
        # Configuration des proxys pour rediriger tout le trafic vers le port 8118 (Privoxy + Tor)
        self.proxies = {"http": proxy, "https": proxy}
        # Définition d'un en-tête utilisateur (User-Agent) pour simuler un navigateur réel
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def search_zombies(self, dork):
        """Méthode principale pour scraper les résultats de recherche et trouver des cibles"""
        # Message d'information indiquant le début de la recherche pour le mot-clé (dork) choisi
        print(f"{Fore.CYAN}[!] Nour-Net lance l'exploration pour : {dork}{Style.RESET_ALL}")
        
        # Construction de l'URL de recherche via DuckDuckGo (version HTML sans JavaScript pour plus de stabilité)
        search_url = f"https://html.duckduckgo.com/html/?q={dork}"
        
        try:
            # Exécution de la requête de recherche en passant par le tunnel de protection
            response = requests.get(search_url, proxies=self.proxies, headers=self.headers, timeout=20)
            
            # Vérification si la page a bien été récupérée (Code 200 = OK)
            if response.status_code == 200:
                # Analyse du code source HTML de la page de résultats
                soup = BeautifulSoup(response.text, 'html.parser')
                # Création d'une liste pour stocker les URLs des cibles potentielles découvertes
                targets = []
                
                # Extraction de tous les liens (balises <a>) présents dans la page
                for link in soup.find_all('a', href=True):
                    url_trouvee = link['href']
                    # Filtrage : On garde uniquement les liens externes et on ignore les liens propres au moteur
                    if "http" in url_trouvee and "duckduckgo" not in url_trouvee:
                        targets.append(url_trouvee)
                
                # Affichage du nombre de résultats trouvés avec un message de succès
                print(f"{Fore.GREEN}[+] {len(targets)} cibles potentielles trouvées dans la Lumière.{Style.RESET_ALL}")
                return targets
                
        except Exception as e:
            # En cas d'erreur (proxy éteint, timeout, etc.), on affiche le problème dans le terminal
            print(f"{Fore.RED}[ERROR] Échec de l'exploration : {e}{Style.RESET_ALL}")
            
        return [] # Retourne une liste vide si aucune cible n'est trouvée ou en cas d'erreur