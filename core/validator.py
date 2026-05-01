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
        """Vérifie si une URL est un zombie exploitable via HEAD avec fallback GET"""
        try:
            # Tentative HEAD (rapide, ne télécharge pas le corps)
            response = requests.head(url, proxies=self.proxies, headers=self.headers,
                                     timeout=10, allow_redirects=True)

            # Fallback GET si le serveur n'accepte pas HEAD (405 Method Not Allowed)
            if response.status_code == 405:
                response = requests.get(url, proxies=self.proxies, headers=self.headers,
                                        timeout=10, stream=True)
                response.close()

            if response.status_code in [200, 301, 302]:
                print(f"{Fore.GREEN}[ALIVE] {url} est valide !{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}[DEAD] {url} (Code: {response.status_code}){Style.RESET_ALL}")
                return False

        except Exception:
            print(f"{Fore.RED}[OFFLINE] {url}{Style.RESET_ALL}")
            return False

    def save_zombies(self, valid_zombies, filename="botnet/zombies.txt"):
        """Enregistre les zombies confirmés sans doublons"""
        try:
            # Chargement des URLs déjà présentes pour éviter les répétitions
            existing = set()
            try:
                with open(filename, "r") as f:
                    existing = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass

            nouveaux = [z for z in valid_zombies if z not in existing]
            with open(filename, "a") as f:
                for z in nouveaux:
                    f.write(z + "\n")
            print(f"{Fore.BLUE}[INFO] {len(nouveaux)} nouveaux zombies ajoutés ({filename}){Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Impossible de sauvegarder : {e}{Style.RESET_ALL}")