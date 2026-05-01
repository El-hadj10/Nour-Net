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
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt