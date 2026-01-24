# Lyrion Playcount Sync

Application desktop Python pour synchroniser les playcounts entre `tracks_persistent` et `alternativeplaycount` dans Lyrion (Logitech Media Server).

## Fonctionnalités

- 🔄 Synchronisation bidirectionnelle des playcounts
- 🎯 Matching intelligent des tracks via algorithme de similarité
- 💾 Sauvegarde automatique de la base de données avant synchronisation
- 🎨 Interface moderne avec Tkinter/ttkbootstrap
- 📊 Affichage des correspondances trouvées
- 🐳 Déploiement Docker avec VNC pour accès à distance
- 📝 Logging détaillé des opérations

## Prérequis

- Python 3.11 ou supérieur
- Accès à la base de données `persist.db` de Lyrion
- (Optionnel) Docker et Docker Compose pour le déploiement

## Installation locale

### 1. Cloner le projet

```bash
git clone https://github.com/yourusername/lyrion-playcount-sync.git
cd lyrion-playcount-sync
```

### 2. Créer un environnement virtuel

```bash
python3.11 -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou
venv\Scripts\activate  # Sur Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer l'application

Copier `config.yaml.example` vers `config.yaml` et adapter les chemins :

```bash
cp config.yaml.example config.yaml
```

Éditer `config.yaml` selon votre configuration Lyrion :

```yaml
database:
  # Chemin vers la base de données (adapter selon votre OS)
  path: "/var/lib/squeezeboxserver/prefs/server.prefs"

matching:
  similarity_threshold: 85
  ratio_method: "token_sort_ratio"

sync:
  direction: "merge"
  auto_apply: false
```

### 5. Lancer l'application

```bash
python -m src.main
```

## Configuration

### config.yaml

#### database
- `path`: Chemin vers la base de données Lyrion
- `backup`: Créer une sauvegarde avant synchronisation

#### matching
- `similarity_threshold`: Seuil de correspondance (0-100)
- `ratio_method`: Algorithme de matching
  - `ratio`: Comparaison simple
  - `partial_ratio`: Comparaison partielle
  - `token_sort_ratio`: Ignore l'ordre des mots
  - `token_set_ratio`: Combine ordre et ensemble

#### sync
- `direction`: 
  - `from_tracks`: Copier de tracks_persistent vers alternativeplaycount
  - `from_alternative`: Copier de alternativeplaycount vers tracks_persistent
  - `merge`: Utiliser la valeur maximale
- `auto_apply`: Appliquer automatiquement sans confirmation
- `backup_before_sync`: Sauvegarder avant synchronisation

#### logging
- `level`: Niveau de logging (DEBUG, INFO, WARNING, ERROR)
- `file`: Fichier de log

## Déploiement Docker

### Avec docker-compose

```bash
docker-compose up -d
```

L'application sera accessible via VNC sur `localhost:5901`

### Manuellement

```bash
docker build -t lyrion-playcount-sync .
docker run -d \
  -p 5901:5901 \
  -v /var/lib/squeezeboxserver:/squeezeboxserver:ro \
  -v ./config.yaml:/app/config.yaml:ro \
  lyrion-playcount-sync
```

### Accès VNC

1. Utiliser un client VNC (TightVNC, RealVNC, etc.)
2. Se connecter à `localhost:5901` (ou IP du serveur)
3. Mot de passe par défaut : `password`

## Chemins par OS

### Linux
```
/var/lib/squeezeboxserver/prefs/server.prefs
```

### macOS
```
~/Library/Application Support/Squeezebox/prefs/server.prefs
```

### Windows
```
C:\ProgramData\Squeezebox\prefs\server.prefs
```

## Architecture

```
lyrion-playcount-sync/
├── src/
│   ├── main.py                 # Point d'entrée
│   ├── database/
│   │   ├── connection.py       # Gestion connexion SQLite
│   │   └── queries.py          # Requêtes de base de données
│   ├── matching/
│   │   └── fuzzy_matcher.py    # Algorithme de matching
│   ├── ui/
│   │   ├── main_window.py      # Interface principale
│   │   └── match_dialog.py     # Dialog de résultats (à implémen)
│   ├── models/
│   │   └── track.py            # Modèles de données
│   └── utils/
│       └── logger.py           # Configuration logging
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.yaml.example
└── README.md
```

## Utilisation

### Workflow standard

1. **Charger les données**
   - Clique sur "Charger les données"
   - L'app lit les deux tables et affiche le nombre de tracks

2. **Trouver correspondances**
   - Clique sur "Trouver correspondances"
   - L'app applique l'algorithme de matching
   - Affiche les résultats dans un tableau

3. **Réviser les correspondances**
   - Vérifier les matches proposés
   - Corriger ou supprimer les mauvaises correspondances si nécessaire

4. **Synchroniser**
   - Clique sur "Synchroniser"
   - Choisir la direction de synchronisation
   - Confirmer la sauvegarde
   - L'app met à jour la base de données

## Développement

### Structure des modules

- **database/**: Gestion de la base de données Lyrion
- **matching/**: Algorithmes d'appariement des tracks
- **ui/**: Interface utilisateur Tkinter
- **models/**: Modèles de données (Track, TrackMatch)
- **utils/**: Utilitaires (logging, etc.)

### Ajouter des fonctionnalités

1. Implémenter la logique dans le module approprié
2. Ajouter les tests correspondants
3. Intégrer dans l'UI via `main_window.py`

## Dépannage

### "Base de données non trouvée"
- Vérifier le chemin dans `config.yaml`
- Assurez-vous que Lyrion est installé et arrêté avant la synchronisation

### "Aucune correspondance trouvée"
- Réduire le seuil de similarité dans `config.yaml`
- Changer la méthode de matching

### Problèmes Docker
- Vérifier les logs : `docker logs lyrion-playcount-sync`
- Vérifier les montages de volumes
- Adapter le chemin vers la base de données selon votre système

## Contribution

Les contributions sont bienvenues ! Veuillez :
1. Fork le projet
2. Créer une branche pour votre feature
3. Commiter vos changements
4. Pousser vers la branche
5. Créer une Pull Request

## Licence

MIT

## Support

Pour les issues, veuillez créer une issue sur GitHub avec :
- Description du problème
- Étapes pour reproduire
- Logs pertinents
- Environnement (OS, version Lyrion, etc.)

## Roadmap

- [ ] Implémentation complète de la UI
- [ ] Export/Import des résultats (CSV, JSON)
- [ ] Historique des synchronisations
- [ ] Annulation des synchronisations
- [ ] Support de plugins Lyrion additionnels
- [ ] Tests unitaires complets
- [ ] Interface web alternative
