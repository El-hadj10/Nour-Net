# 🌌 Nour-Net : Exploration & Validation Engine

**Nour-Net** est un outil de recherche et de validation automatisé conçu pour explorer les réseaux et identifier des vecteurs de redirection (zombies) via le réseau sécurisé Tor. Alliant spiritualité et technique, ce projet vise à cartographier la "Lumière" dans l'ombre du web.

---

## 🚀 Fonctionnalités
- **Anonymat Total** : Intégration native avec Tor et Privoxy.
- **Moteur Multi-Dorks** : Rotation intelligente de requêtes pour maximiser les résultats.
- **Anti-Blocking** : Système de pauses aléatoires et rotation de User-Agents pour contourner les erreurs 403.
- **Validation en Temps Réel** : Module de vérification du statut HTTP des cibles trouvées.
- **Sauvegarde Automatisée** : Archivage structuré des cibles valides dans `botnet/zombies.txt`.

## 🛠️ Architecture du Projet
- `main.py` : Chef d'orchestre de la session d'exploration.
- `core/scanner.py` : Moteur de scraping avec camouflage (Referer/User-Agent).
- `core/validator.py` : Cerveau de validation des cibles.
- `botnet/` : Répertoire de stockage des résultats.

## ⚙️ Installation & Utilisation
1. S'assurer que **Tor** et **Privoxy** sont actifs.
2. Créer et activer un environnement virtuel :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancer le programme :
   ```bash
   python main.py
   ```

## 📋 Prérequis
- **Tor** installé et actif (`sudo systemctl start tor`)
- **Privoxy** configuré pour forwarder vers Tor (port 9050 → 8118)
- Python 3.8+

## ⚠️ Avertissement
Cet outil est fourni à des fins de recherche et d'éducation uniquement. Toute utilisation à des fins malveillantes ou non autorisées est strictement interdite et engage la seule responsabilité de l'utilisateur.