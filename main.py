import requests # Bibliothèque pour les requêtes HTTP simples
import sys # Pour la gestion du système et de l'arrêt du script
from core.scanner import NourScanner # Importation de ton moteur de recherche
from core.validator import NourValidator # Importation de ton moteur de validation
from colorama import Fore, Style # Pour un terminal en couleur et lisible

def check_connection():
    """Vérifie si le tunnel Tor/Privoxy est bien actif avant de commencer"""
    proxy = "http://127.0.0.1:8118"
    proxies = {"http": proxy, "https": proxy}
    print(f"{Fore.BLUE}[+] Initialisation de Nour-Net...{Style.RESET_ALL}")
    
    try:
        # Test de l'IP via le site officiel de Tor
        response = requests.get("https://check.torproject.org/", proxies=proxies, timeout=10)
        if "Congratulations" in response.text:
            print(f"{Fore.GREEN}[SUCCESS] Nour-Net est masqué derrière le réseau Tor.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}[WARNING] Connexion établie mais IP réelle peut-être exposée !{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Échec de la connexion au proxy : {e}{Style.RESET_ALL}")
        return False

def start_nour_net():
    """Lance la séquence complète : Test -> Scan -> Validation"""
    # 1. On vérifie la sécurité d'abord
    if not check_connection():
        print(f"{Fore.RED}[!] Sécurité non garantie. Arrêt par précaution.{Style.RESET_ALL}")
        sys.exit()

    print(f"\n{Fore.MAGENTA}=== DÉBUT DE LA MISSION ==={Style.RESET_ALL}")
    
    # 2. Initialisation des outils
    scanner = NourScanner()
    validator = NourValidator()
    
    # 3. Recherche (Scan)
    dork = "redirect.php?url=" # Tu peux changer ce dork selon tes besoins
    targets = scanner.search_zombies(dork)
    
    # 4. Validation et stockage
    if targets:
        print(f"{Fore.CYAN}[*] Analyse de la viabilité des cibles...{Style.RESET_ALL}")
        army = []
        for t in targets:
            if validator.validate_zombie(t): # On teste chaque cible une par une
                army.append(t)
        
        if army:
            validator.save_zombies(army) # On enregistre les survivants
            print(f"{Fore.GREEN}[FINISH] Mission accomplie. Armée mise à jour.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] Aucune cible valide trouvée dans cette session.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        start_nour_net()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interruption par l'utilisateur. Salam.{Style.RESET_ALL}")