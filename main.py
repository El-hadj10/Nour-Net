import requests

def check_connection():
    proxy = "http://127.0.0.1:8118"
    proxies = {"http": proxy, "https": proxy}
    print("[+] Initialisation de Nour-Net...")
    try:
        response = requests.get("https://check.torproject.org/", proxies=proxies, timeout=10)
        if "Congratulations" in response.text:
            print("[SUCCESS] Nour-Net est masqué derrière le réseau Tor.")
        else:
            print("[WARNING] Connexion établie mais IP réelle peut-être exposée.")
    except Exception as e:
        print(f"[ERROR] Échec de la connexion au proxy : {e}")

if __name__ == "__main__":
    check_connection()