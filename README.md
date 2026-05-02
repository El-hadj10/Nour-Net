# Nour-Net

## Exploration, validation et supervision temps reel

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Command%20Center-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tor](https://img.shields.io/badge/Tor%20%2B%20Privoxy-Active-7D4698?style=for-the-badge&logo=tor-browser&logoColor=white)](https://www.torproject.org/)
[![BraveSearch](https://img.shields.io/badge/Brave%20Search-Moteur-FB542B?style=for-the-badge&logo=brave&logoColor=white)](https://search.brave.com/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com/El-hadj10/Nour-Net)

Nour-Net est un projet educatif centre sur l'automatisation reseau defensive : scan multi-dorks,
validation HTTP, persistance dedupliquee et supervision temps reel via un Command Center local.

---

## A propos

Le projet combine :

- un mode CLI direct et immediat
- un moteur de scan sur Brave Search (compatible Tor)
- une validation HTTP robuste avec filtre de pertinence
- une persistance dedupliquee sans bruit
- un Command Center web local avec stream WebSocket

Objectif : apprendre a structurer un workflow technique complet,
du traitement des cibles jusqu'au monitoring en temps reel.

---

## Fonctionnalites

### Core Engine

- Verification optionnelle de la connectivite Tor/Privoxy
- Scraping Brave Search via tunnel Tor (DuckDuckGo incompatible Tor)
- Rotation d'identite User-Agent
- Dorks configurables axes sur les proxies reels
- Filtre de pertinence : exclusion du bruit (GitHub, YouTube, Wikipedia...)
- Validation HEAD puis fallback GET si HEAD retourne 405
- Deduplication avant ecriture dans [botnet/zombies.txt](botnet/zombies.txt)

### Command Center (GUI)

- Creation et supervision de sessions depuis l'interface
- Stream WebSocket en temps reel (evenements, logs, compteurs)
- Arret manuel de session
- Cartographie Leaflet avec geolocalisation backend (ip-api.com)
- Export de session en JSON ou CSV
- Filtre de logs par niveau (info / success / warning / error)
- Historique des sessions recentes

---

## Architecture

```text
Nour-Net/
├── main.py                     # CLI
├── gui.py                      # Lance l'interface web
├── core/
│   ├── scanner.py              # Scraping Brave Search + filtre pertinence
│   ├── validator.py            # Validation HTTP et sauvegarde
│   └── engine.py               # Orchestration, geolocalisation, evenements
├── web/
│   ├── app.py                  # API FastAPI + WebSocket + export + stop
│   └── static/
│       ├── index.html          # Dashboard
│       ├── style.css           # Theme holographique sombre
│       ├── app.js              # Logique frontend (WS, carte, filtres)
│       └── assets/
│           ├── nour-eye.svg
│           └── grid.svg
└── botnet/
    └── zombies.txt             # Cibles validees (1 URL/ligne, sans doublon)
```

---

## Installation

Prerequis :

- Python 3.8+
- Tor actif
- Privoxy configure sur le port 8118

```bash
git clone https://github.com/El-hadj10/Nour-Net.git
cd Nour-Net
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Utilisation

### Mode CLI

```bash
python3 main.py
```

### Mode GUI

```bash
python3 gui.py
```

Ouvrir [http://127.0.0.1:8080](http://127.0.0.1:8080).

---

## Dorks par defaut

Les dorks sont axes sur les interfaces de proxy web publics :

```
"Simple PHP Proxy script"
"powered by PHProxy"
"open web proxy" "anonymous browsing"
"nph-proxy" "CGI Proxy"
```

Configurables dans l'interface GUI ou dans `core/engine.py`.

---

## API

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/health | Sante du service |
| POST | /api/sessions | Creer une session |
| GET | /api/sessions | Lister les sessions |
| GET | /api/sessions/{id} | Detail d'une session |
| POST | /api/sessions/{id}/stop | Arreter une session |
| GET | /api/sessions/{id}/export?format=json | Export JSON |
| GET | /api/sessions/{id}/export?format=csv | Export CSV |
| GET | /api/geolocate?target_url=... | Geolocaliser une cible |
| WS | /api/sessions/{id}/ws | Stream evenements |

---

## Stack

- Backend : Python, FastAPI, Uvicorn, Requests, websockets
- Parsing : BeautifulSoup4
- Frontend : HTML, CSS, JavaScript vanilla
- Cartographie : Leaflet + OpenStreetMap
- Moteur de recherche : Brave Search (via Tor/Privoxy)
- CLI UX : Colorama

---

## Legal

Projet fourni pour apprentissage et recherche defensive dans des environnements autorises.
Toute utilisation non autorisee est interdite et engage uniquement la responsabilite de l'utilisateur.


Nour-Net est un projet educatif centre sur l'automatisation reseau defensive: scan, validation, persistance et visualisation temps reel.

---

## A propos

Le projet combine:

- un mode CLI simple et direct
- un moteur de scan multi-dorks
- une validation HTTP robuste
- une persistance dedupee
- un Command Center web local

Objectif: apprendre a structurer un workflow technique complet, du traitement des cibles jusqu'au monitoring.

---

## Fonctionnalites

### Core Engine

- Verification optionnelle de la connectivite Tor/Privoxy
- Rotation d'identite User-Agent
- Dorks configurables
- Validation HEAD puis fallback GET si HEAD retourne 405
- Deduplication avant ecriture dans [botnet/zombies.txt](botnet/zombies.txt)

### Command Center

- Creation de sessions depuis l'interface
- Stream WebSocket en temps reel
- Arret manuel de session
- Cartographie reelle Leaflet avec geolocalisation backend
- Export de session en JSON ou CSV
- Historique des sessions recentes

---

## Architecture

```text
Nour-Net/
├── main.py                     # CLI
├── gui.py                      # Lance l'interface web
├── core/
│   ├── scanner.py              # Scan et extraction URL
│   ├── validator.py            # Validation et sauvegarde
│   └── engine.py               # Orchestration + geolocalisation
├── web/
│   ├── app.py                  # API + WS + export + stop
│   └── static/
│       ├── index.html          # Dashboard
│       ├── style.css           # Theme
│       ├── app.js              # Logique frontend
│       └── assets/
│           ├── nour-eye.svg
│           └── grid.svg
└── botnet/zombies.txt
```

---

## Installation

Prerequis:

- Python 3.8+
- Tor actif
- Privoxy configure sur le port 8118

```bash
git clone https://github.com/El-hadj10/Nour-Net.git
cd Nour-Net
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Utilisation

### Mode CLI

```bash
python3 main.py
```

### Mode GUI

```bash
python3 gui.py
```

Ensuite ouvrir [http://127.0.0.1:8080](http://127.0.0.1:8080).

---

## API rapide

- GET /api/health
- POST /api/sessions
- GET /api/sessions
- GET /api/sessions/{id}
- POST /api/sessions/{id}/stop
- GET /api/sessions/{id}/export?format=json
- GET /api/sessions/{id}/export?format=csv
- GET /api/geolocate?target_url=target-url
- WS /api/sessions/{id}/ws

---

## Stack

- Backend: Python, FastAPI, Uvicorn, Requests
- Parsing: BeautifulSoup4
- Frontend: HTML, CSS, JavaScript
- Cartographie: Leaflet + OpenStreetMap
- CLI UX: Colorama

---

## Legal

Projet fourni pour apprentissage et recherche defensive dans des environnements autorises.
Toute utilisation non autorisee est interdite et engage uniquement la responsabilite de l'utilisateur.
