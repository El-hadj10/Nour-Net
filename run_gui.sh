#!/usr/bin/env bash
set -euo pipefail

# Lance Nour-Net en mode GUI avec pre-sequence Tor recommandee.
cd "$(dirname "$0")"

source venv/bin/activate
sudo service tor restart
python3 gui.py
