# Nour-Net

## Exploration, validation et supervision temps reel

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Command%20Center-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tor](https://img.shields.io/badge/Tor%20%2B%20Privoxy-Active-7D4698?style=for-the-badge&logo=tor-browser&logoColor=white)](https://www.torproject.org/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com/El-hadj10/Nour-Net)

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
