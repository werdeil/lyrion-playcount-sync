# Configuration et Logging

## Guide de Configuration

Le système de configuration permet de personnaliser l'application sans modifier le code.

### Démarrage Rapide

1. Copiez `config.yaml.example` en `config.yaml` :
   ```bash
   cp config.yaml.example config.yaml
   ```

2. Adaptez les paramètres selon vos besoins

3. L'application chargera `config.yaml` au démarrage

### Structure de Configuration

#### Base de Données

```yaml
database:
  path: "/config/prefs/persist.db"           # Chemin de la base de données
  auto_backup: true                          # Sauvegarde automatique
  backup_on_startup: true                    # Sauvegarder au démarrage
  backup_retention_days: 7                   # Jours de rétention
```

#### Matching (Fuzzy Matching)

```yaml
matching:
  auto_match_threshold: 90                   # Seuil auto-matching (0-100)
  suggestion_min_score: 50                   # Score min suggestions (0-100)
  max_suggestions: 5                         # Nombre max suggestions
  weights:
    title: 70                                # Poids du titre (0-100)
    artist: 20                               # Poids artiste (0-100)
    album: 10                                # Poids album (0-100)
    # Note: Les poids doivent sommer à 100
```

#### Synchronisation

```yaml
sync:
  default_action: "COPY"                     # COPY, MERGE ou SKIP
  delete_after_sync: true                    # Supprimer après sync
  confirm_below_score: 70                    # Score pour auto-confirm
```

#### Interface Utilisateur

```yaml
ui:
  theme: "darkly"                            # Thème (darkly, bootstrap, etc.)
  window_size: "1200x800"                    # Taille fenêtre
  auto_refresh_seconds: 0                    # Auto-refresh en secondes (0=off)
  show_tooltips: true                        # Afficher les infobulles
```

#### Logging

```yaml
logging:
  level: "INFO"                              # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "./logs/sync.log"                    # Fichier de log
```

### Niveaux de Logging

| Niveau    | Description                          |
|-----------|--------------------------------------|
| DEBUG     | Messages détaillés pour débogage     |
| INFO      | Messages généraux (défaut)           |
| WARNING   | Avertissements et erreurs possibles  |
| ERROR     | Erreurs seulement                    |
| CRITICAL  | Erreurs graves seulement             |

### Utilisation en Python

#### Charger la Configuration

```python
from src.utils.config import Config

# Instance singleton
config = Config.instance()

# Charger depuis fichier
config.load_from_file('config.yaml')

# Accéder aux valeurs
print(config.database.path)
print(config.matching.auto_match_threshold)
```

#### Accès par Notation Pointée

```python
# Getter
threshold = config.get('matching.auto_match_threshold')

# Setter
config.set('matching.auto_match_threshold', 85)
```

#### Valider la Configuration

```python
# Valider tous les paramètres
config.validate()

# Ou valider une section
config.matching.validate()
```

#### Sauvegarder les Changements

```python
# Sauvegarder dans le fichier d'origine
config.save_to_file()

# Sauvegarder dans un nouveau fichier
config.save_to_file('new_config.yaml')
```

#### Conversion en Dictionnaire

```python
# Obtenir toute la config en dict
config_dict = config.to_dict()
```

### Utilisation du Logging

#### Configurer un Logger

```python
from src.utils.logger import setup_logger, get_logger, LEVEL_NAMES

# Créer un nouveau logger
logger = setup_logger(
    'myapp',
    log_level='INFO',
    log_file='./logs/myapp.log'
)

# Utiliser le logger
logger.info("Message informatif")
logger.error("Une erreur est survenue")
```

#### Récupérer un Logger Existant

```python
logger = get_logger('myapp')
```

#### Niveaux Disponibles

```python
from src.utils.logger import LEVEL_NAMES

# Accès aux niveaux
LEVEL_NAMES['DEBUG']      # logging.DEBUG
LEVEL_NAMES['INFO']       # logging.INFO
LEVEL_NAMES['WARNING']    # logging.WARNING
LEVEL_NAMES['ERROR']      # logging.ERROR
LEVEL_NAMES['CRITICAL']   # logging.CRITICAL
```

### Fichiers de Log

Les logs sont sauvegardés dans le répertoire spécifié (défaut: `./logs/`):

```
logs/
├── sync.log          # Log principal (jusqu'à 10MB)
├── sync.log.1        # Premier fichier de rotation
├── sync.log.2        # Deuxième fichier de rotation
└── ...
```

**Configuration de Rotation:**
- Taille max par fichier: 10 MB
- Nombre de fichiers conservés: 5
- Format: `[TIMESTAMP] [LEVEL] [logger_name] message`

### Exemple Complet

```yaml
# config.yaml

database:
  path: "~/.local/share/Lyrion/prefs/persist.db"
  auto_backup: true
  backup_on_startup: true
  backup_retention_days: 14

matching:
  auto_match_threshold: 85
  suggestion_min_score: 60
  max_suggestions: 10
  weights:
    title: 70
    artist: 25
    album: 5

sync:
  default_action: "COPY"
  delete_after_sync: false
  confirm_below_score: 75

ui:
  theme: "flatly"
  window_size: "1400x900"
  auto_refresh_seconds: 30
  show_tooltips: true

logging:
  level: "DEBUG"
  file: "./logs/sync.log"
```

### Validation Automatique

La configuration est automatiquement validée au chargement:

- **Poids du Matching:** Normalisés à 100 si nécessaire
- **Action par Défaut:** Corrigée à "COPY" si invalide
- **Niveau de Log:** Corrigé à "INFO" si invalide

Les corrections sont enregistrées dans les logs avec des avertissements.

### Variables d'Environnement

Vous pouvez utiliser des variables d'environnement dans la configuration YAML:

```yaml
database:
  path: "${DATABASE_PATH:-/config/prefs/persist.db}"

logging:
  level: "${LOG_LEVEL:-INFO}"
```

Utilisez le module `python-dotenv` pour charger les variables depuis `.env`:

```python
from dotenv import load_dotenv

load_dotenv()
```

### Dépannage

#### Configuration non chargée

```python
# Vérifier le chemin du fichier
print(config._config_file)

# Recharger explicitement
config.load_from_file('config.yaml')
```

#### Poids non valides

Les poids sont automatiquement normalisés. Vérifiez les logs:

```
WARNING Weights sum to 95, should be 100. Normalizing...
```

#### Logging non visible

- Vérifiez le niveau de logging
- Vérifiez que le répertoire `logs/` est accessible
- Vérifiez les permissions en écriture

### Architecture Interne

Le système de configuration utilise le pattern **Singleton**:

- Une seule instance `Config` pour toute l'application
- Accès via `Config.instance()`
- Validations automatiques au chargement et à la modification

### Fichiers Connexes

- [config.yaml.example](config.yaml.example) - Fichier d'exemple
- [src/utils/config.py](src/utils/config.py) - Implémentation
- [src/utils/logger.py](src/utils/logger.py) - Système de logging
- [tests/test_config_logging.py](tests/test_config_logging.py) - Tests (31 tests)
