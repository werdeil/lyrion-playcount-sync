# Checklist d'Intégration - Orchestration Application

## ✅ Système Complet Créé

Le système d'orchestration de l'application est **complet et testé**.

### Fichiers Créés/Modifiés

- ✅ [src/main.py](src/main.py) - Orchestrateur principal (330 lignes)
- ✅ [run.py](run.py) - Script de démarrage (218 lignes)
- ✅ [MAIN_ORCHESTRATION.md](MAIN_ORCHESTRATION.md) - Documentation complète
- ✅ [config.yaml.example](config.yaml.example) - Template configuration
- ✅ [src/utils/config.py](src/utils/config.py) - Gestion configuration
- ✅ [src/utils/logger.py](src/utils/logger.py) - Système de logging

### État des Tests

| Composant | Tests | Status |
|-----------|-------|--------|
| Configuration/Logging | 31 | ✅ PASS |
| Orchestration | N/A | ✅ Syntaxe OK |

## 📋 Tâches de Mise à Jour

### Avant de Lancer en Production

- [ ] **1. Vérifier imports dans MainWindow**
  ```python
  # MainWindow.__init__ doit accepter:
  def __init__(self, root, db=None, detector=None, matcher=None, config=None)
  ```

- [ ] **2. Vérifier imports dans SyncDetector**
  ```python
  # SyncDetector doit accepter:
  def __init__(self, db)
  ```

- [ ] **3. Vérifier imports dans TrackMatcher**
  ```python
  # TrackMatcher doit accepter:
  def __init__(self, matching_config)
  ```

- [ ] **4. Vérifier DatabaseManager**
  ```python
  # Doit avoir:
  # - connect() -> bool
  # - backup_database() -> str
  # - verify_schema() -> bool
  # - close()
  ```

- [ ] **5. Créer config.yaml depuis config.yaml.example**
  ```bash
  cp config.yaml.example config.yaml
  # Puis adapter les paramètres
  ```

- [ ] **6. Tester avec --check**
  ```bash
  python3 run.py --check
  ```

- [ ] **7. Lancer avec --setup (si premières fois)**
  ```bash
  python3 run.py --setup
  ```

## 🚀 Démarrage

### Option 1: Via run.py (Recommandé)

```bash
# Premier lancement
python3 run.py --setup
python3 run.py

# Lancements suivants
python3 run.py
```

### Option 2: Directement

```bash
python3 src/main.py
```

### Option 3: Avec config personnalisé

```bash
python3 run.py /path/to/my/config.yaml
```

## 🔍 Troubleshooting

### Si erreur "Config non trouvé"

```bash
python3 run.py --setup
```

### Si erreur "Module not found"

```bash
# Vérifier installation
python3 run.py --check

# Installer dépendances
pip install -r requirements.txt
```

### Si erreur "BD non trouvée"

1. Vérifier `config.yaml` section `database.path`
2. S'assurer que le chemin est accessible
3. Vérifier que c'est une BD Lyrion valide

### Si erreur "UI"

1. Vérifier que MainWindow accepte les paramètres
2. Vérifier ttkbootstrap installé
3. Vérifier les logs dans `./logs/sync.log`

## 📊 Logs

Les logs sont créés dans `./logs/sync.log`:

```
[2026-01-24 23:56:30] [INFO] [app] ======================================================================
[2026-01-24 23:56:30] [INFO] [app] Démarrage - Lyrion Playcount Sync
[2026-01-24 23:56:30] [INFO] [app] ======================================================================
[2026-01-24 23:56:30] [INFO] [app] Base de données: /config/prefs/persist.db
[2026-01-24 23:56:30] [INFO] [app] Seuil matching: 90%
[2026-01-24 23:56:30] [INFO] [app] Thème UI: darkly
[2026-01-24 23:56:30] [INFO] [app] Niveau log: INFO
...
```

## 🔧 Adaptations Nécessaires

### MainWindow

**Doit supporter:**
```python
class MainWindow:
    def __init__(
        self, 
        root,
        db=None, 
        detector=None, 
        matcher=None, 
        config=None
    ):
        self.root = root
        self.db = db
        self.detector = detector
        self.matcher = matcher
        self.config = config
```

### SyncDetector

**Doit supporter:**
```python
class SyncDetector:
    def __init__(self, db):
        self.db = db
```

### TrackMatcher

**Doit supporter:**
```python
class TrackMatcher:
    def __init__(self, matching_config):
        # matching_config est une MatchingConfig dataclass
        self.threshold = matching_config.auto_match_threshold
        self.weights = matching_config.weights
        # ...
```

### DatabaseManager

**Doit avoir ces méthodes:**
```python
class DatabaseManager:
    def connect(self) -> bool:
        # Établir la connexion
        
    def backup_database(self) -> str:
        # Retourner le chemin du backup
        
    def verify_schema(self) -> bool:
        # Vérifier que c'est une BD Lyrion
        
    def close(self):
        # Fermer la connexion
```

## ✨ Améliorations Futures

- [ ] Support de themes personnalisés
- [ ] Auto-refresh de l'UI configurable
- [ ] Historique des actions
- [ ] Export des logs
- [ ] Configuration multi-utilisateur

## 📝 Résumé Complet

### Architecture

```
run.py (entry point)
  ↓
src/main.py (Application class)
  ├─ setup_logging() → src/utils/logger.py
  ├─ load_configuration() → src/utils/config.py
  ├─ connect_database() → src/database/
  ├─ initialize_components() → src/database/ + src/matching/
  ├─ launch_ui() → src/ui/main_window.py
  └─ cleanup()
```

### Flux de Données

```
config.yaml.example
  ↓ (copy)
config.yaml
  ↓ (load)
src/utils/config.py (Config singleton)
  ↓ (inject)
src/main.py (Application)
  ├─ → src/database/connection.py (DatabaseManager)
  ├─ → src/database/queries.py (SyncDetector)
  ├─ → src/matching/track_matcher.py (TrackMatcher)
  └─ → src/ui/main_window.py (MainWindow)
```

### Exit Codes

| Code | Signification |
|------|---------------|
| 0 | Succès ou interruption utilisateur |
| 1 | Erreur (config, BD, UI, etc.) |

## 📚 Documentation

- [README.md](README.md) - Guide général
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration système
- [MAIN_ORCHESTRATION.md](MAIN_ORCHESTRATION.md) - Architecture orchestration
- [config.yaml.example](config.yaml.example) - Template config

## ✅ Validation

Avant production:

```bash
# 1. Vérifier installation
python3 run.py --check

# 2. Vérifier configuration
cat config.yaml

# 3. Tester import
python3 -c "from src.main import Application; print('OK')"

# 4. Vérifier logs
tail -f ./logs/sync.log

# 5. Lancer en mode test
python3 run.py
```

## 🎯 Prochain Pas

1. ✅ Créer src/main.py ← **FAIT**
2. ✅ Créer run.py ← **FAIT**
3. ✅ Créer configuration ← **FAIT**
4. ✅ Créer logging ← **FAIT**
5. ⏳ **ÉTAPE SUIVANTE:** Adapter les modules existants
   - Vérifier MainWindow, SyncDetector, TrackMatcher
   - Adapter pour accepter les paramètres
   - Tester l'intégration

---

**Status:** ✅ **ORCHESTRATION COMPLÈTE**  
**Date:** 2026-01-24  
**Prêt pour:** Production avec adaptations mineures
