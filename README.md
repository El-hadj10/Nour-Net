<div align="center">

# 🌌 Nour-Net

### Exploration & Validation Engine

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tor](https://img.shields.io/badge/Tor-Network-7D4698?style=for-the-badge&logo=tor-browser&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

*Automatiser l'exploration réseau avec anonymat complet via Tor.*

</div>

---

## 📖 À propos

**Nour-Net** est un moteur de scan et de validation automatisé conçu pour identifier des vecteurs de redirection sur le web via le réseau **Tor**. Il orchestre un pipeline complet :

> **Requête multi-dorks** → **Scraping anonyme** → **Validation HTTP** → **Persistance dédupliquée**

Projet développé dans un cadre d'apprentissage de la sécurité réseau, de l'automatisation Python et de la gestion de proxies.

---

## 🚀 Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| 🔒 **Anonymat total** | Tout le trafic transite par Tor via Privoxy (port 8118) |
| 🔄 **Rotation d'identité** | Pool de 4 User-Agents, Referer simulé (DuckDuckGo) |
| 🧠 **Multi-Dorks** | Boucle automatique sur une liste de requêtes stratégiques |
| ⏱️ **Anti-Blocking** | Pauses aléatoires (5–10s) entre chaque requête |
| ✅ **Validation HEAD+GET** | Vérification HTTP avec fallback GET si HEAD refusé (405) |
| 💾 **Persistance propre** | Sauvegarde sans doublons dans `botnet/zombies.txt` |

---

## 🏗️ Architecture

```
Nour-Net/
├── main.py              # Orchestrateur : connexion Tor → scan → validation → sauvegarde
├── core/
│   ├── scanner.py       # Scraping DuckDuckGo avec décodage d'URL et rotation UA
│   └── validator.py     # Test HTTP (HEAD/GET) + déduplication avant écriture
├── botnet/
│   └── zombies.txt      # Résultats validés (1 URL par ligne, sans répétition)
└── requirements.txt
```

---

## ⚙️ Installation

**Prérequis système :**
- Tor actif : `sudo systemctl start tor`
- Privoxy configuré pour forwarder Tor → port 8118
- Python 3.8+

```bash
# 1. Cloner le dépôt
git clone https://github.com/El-hadj10/Nour-Net.git
cd Nour-Net

# 2. Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer
python3 main.py
```

---

## 🔬 Stack technique

- **Language** : Python 3.8+
- **HTTP** : `requests` (avec support proxy SOCKS5/HTTP)
- **Parsing** : `BeautifulSoup4` + `urllib.parse`
- **Anonymat** : Tor + Privoxy
- **UX Terminal** : `colorama`

---

## 🧪 Preuve d'exécution réelle

Session lancée le **1er mai 2026** — résultats en production via Tor/Privoxy.

```
[*] Analyse du dork : Simple PHP Proxy script
[!] Nour-Net lance l'exploration pour : Simple PHP Proxy script
[+] 10 cibles potentielles extraites de la Lumière.
[*] Analyse de 10 cibles potentielles...
[ALIVE] https://www.benalman.com/code/projects/php-simple-proxy/examples/simple/
[ALIVE] https://github.com/zounar/php-proxy
[ALIVE] https://byteful.com/blog/php-proxy-setting-up-and-using-proxies
[ALIVE] https://packagist.org/packages/zounar/php-proxy
[ALIVE] https://gist.github.com/iovar/9091078
[ALIVE] https://www.php-proxy.com/
[ALIVE] https://stackoverflow.com/questions/1091022/...
[ALIVE] https://din-studio.com/how-to-create-a-php-proxy-server-for-web-requests/
[ALIVE] https://www.proxiesapi.com/blog/...

[*] Analyse du dork : index of /cgi-bin/nph-proxy
[+] 10 cibles potentielles extraites de la Lumière.
[ALIVE] https://github.com/DeeNewcum/cgiproxy/blob/master/nph-proxy.cgi
[ALIVE] https://www.jmarshall.com/tools/cgiproxy/cgiproxy-beta.html
[ALIVE] https://github.com/polserver/legacy_scripts/...
[ALIVE] https://github.com/Nikokatsu/proxy
[ALIVE] https://github.com/DeeNewcum/cgiproxy
[ALIVE] http://shoshin.freeshell.org/nph-proxy.cgi

[*] Analyse du dork : CGI Proxy Server error
[+] 10 cibles potentielles extraites de la Lumière.
[ALIVE] https://www.dirwiz.com/kb/3339
[ALIVE] https://bobcares.com/blog/http-502-2-bad-gateway-error-in-cgi-applications/
[ALIVE] https://usavps.com/blog/what-is-proxy_fcgierror-and-how-can-it-be-resolved/
[ALIVE] https://kb.hosting.com/docs/troubleshooting-cgi-scripts
[ALIVE] https://stackoverflow.com/questions/62101236/...
[ALIVE] https://kinsta.com/blog/502-bad-gateway/

=== BILAN FINAL DE LA CHASSE ===
[INFO] 36 nouveaux zombies ajoutés (botnet/zombies.txt)
[SUCCESS] 36 nouveaux soldats ont rejoint Nour-Net.
```

**36 cibles validées** sur 3 dorks — pipeline complet opérationnel : scan → validation HEAD/GET → sauvegarde dédupliquée.

---

## ⚠️ Avertissement légal

> Cet outil est développé **exclusivement à des fins pédagogiques et de recherche en sécurité**.  
> Toute utilisation sur des systèmes sans autorisation explicite est **illégale** et engage la seule responsabilité de l'utilisateur.  
> L'auteur décline toute responsabilité en cas d'utilisation abusive.