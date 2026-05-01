import requests # Pour effectuer les tests de connexion HTTP
from colorama import Fore, Style # Pour un affichage clair dans le terminal

class NourValidator:
    def __init__(self, proxy="http://127.0.0.1:8118"):
        """Initialisation du validateur avec le tunnel Tor/Privoxy"""
        # On utilise le même proxy que le scanner pour rester anonyme durant les tests
        self.proxies = {"http": proxy, "https": proxy}
        # Identité factice pour ne pas éveiller de soupçons sur les serveurs testés
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def validate_zombie(self, url):
        """Vérifie si une URL est un zombie exploitable via une requête HEAD"""
        try:
            # On utilise une requête HEAD (plus rapide que GET car elle ne télécharge pas le contenu)
            # On ajoute un timeout court (10s) pour ne pas rester bloqué sur un serveur lent
            response = requests.head(url, proxies=self.proxies, headers=self.headers, timeout=10)
            
            # Si le serveur répond avec un code 200 (OK) ou 302 (Redirection)
            if response.status_code in [200, 301, 302]:
                print(f"{Fore.GREEN}[ALIVE] {url} est valide !{Style.RESET_ALL}")
                return True
            else:
                # Le serveur existe mais ne répond pas comme on le souhaite
                print(f"{Fore.YELLOW}[DEAD] {url} (Code: {response.status_code}){Style.RESET_ALL}")
                return False
                
        except Exception:
            # Si le serveur ne répond pas du tout ou si le lien est mort
            print(f"{Fore.RED}[OFFLINE] {url}{Style.RESET_ALL}")
            return False

    def save_zombies(self, valid_zombies, filename="botnet/zombies.txt"):
        """Enregistre les zombies confirmés dans un fichier texte"""
        try:
            with open(filename, "a") as f: # Mode 'a' pour ajouter à la suite sans effacer
                for z in valid_zombies:
                    f.write(z + "\n")
            print(f"{Fore.BLUE}[INFO] {len(valid_zombies)} zombies ajoutés à ton armée ({filename}){Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Impossible de sauvegarder : {e}{Style.RESET_ALL}")