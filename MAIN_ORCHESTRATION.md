# Orchestration d'Application - Fichier Main.py

## 📋 Résumé Complet

Le fichier `src/main.py` a été créé/mis à jour pour orchestrer complètement l'application avec une **architecture modulaire, robuste et bien testée**.

### ✅ Fichiers Créés/Modifiés

| Fichier | Status | Description |
|---------|--------|-------------|
| [src/main.py](src/main.py) | ✅ CRÉÉ | Orchestrateur principal (330 lignes) |
| [run.py](run.py) | ✅ MIS À JOUR | Script de démarrage amélioré (218 lignes) |

## 🎯 Architecture Principale

### Classe Application (src/main.py)

**Responsabilités:**
1. **Setup Logging** - Configuration du système de logging
2. **Load Configuration** - Chargement depuis YAML avec fallback
3. **Connect Database** - Connexion BD + backup + vérification schéma
4. **Initialize Components** - Créer détecteur sync + matcher de pistes
5. **Launch UI** - Lancer l'interface tkinter
6. **Cleanup** - Fermeture propre et sécurisée

**Méthodes:**

```python
class Application:
    def __init__(config_file: Optional[str])
    def setup_logging() -> bool
    def load_configuration() -> bool
    def connect_database() -> bool
    def initialize_components() -> bool
    def launch_ui() -> bool
    def cleanup()
    def run() -> int  # Orchestre tout
```

## 🔄 Flux d'Exécution

```
main()
  └─ Application(config_file)
      ├─ setup_logging()
      │  └─ setup_logger('app', 'INFO', './logs/sync.log')
      │
      ├─ load_configuration()
      │  ├─ Config.instance()
      │  ├─ load_from_file('config.yaml')
      │  ├─ ou load_from_file('config.yaml.example')
      │  └─ validate()
      │
      ├─ connect_database()
      │  ├─ DatabaseManager(db_path)
      │  ├─ db.connect()
      │  ├─ db.backup_database() [si configuré]
      │  └─ db.verify_schema()
      │
      ├─ initialize_components()
      │  ├─ SyncDetector(db)
      │  └─ TrackMatcher(config.matching)
      │
      ├─ launch_ui()
      │  ├─ tk.Tk()
      │  ├─ MainWindow(...)
      │  └─ root.mainloop()
      │
      └─ finally: cleanup()
         └─ db.close()
```

## 🛡️ Gestion des Erreurs

### Try/Except Autour de Chaque Étape

```python
# Chaque étape critique:
try:
    # Opération
    return True
except Exception as e:
    self.logger.error(f"Erreur {etape}: {e}", exc_info=True)
    return False
```

### Cleanup Garanti

```python
try:
    # ... exécution ...
except KeyboardInterrupt:
    logger.info("Interruption utilisateur")
except Exception as e:
    logger.error(f"Erreur non gérée: {e}", exc_info=True)
finally:
    # TOUJOURS appelé
    cleanup()
```

### Exit Codes Appropriés

- `0` = Succès ou interruption utilisateur
- `1` = Erreur (config, BD, UI, etc.)

## 📝 Logging Détaillé

### Messages Principaux

```
=== Démarrage - Lyrion Playcount Sync ===
Connexion à la base de données: /config/prefs/persist.db
✓ Connexion établie
✓ Sauvegarde créée: /path/to/backup.db.20260124T235900Z
✓ Schéma vérifié
Initialisation des composants...
✓ Détecteur de sync initialisé
✓ Matcher de pistes initialisé
Lancement de l'interface utilisateur...
✓ Interface chargée
Démarrage de la boucle événementielle...
... (application en cours d'exécution) ...
✓ Base de données fermée
=== Arrêt propre ===
```

## 🚀 Utilisation

### Lancer l'application

```bash
# Méthode 1: Via le script run.py
python3 run.py

# Méthode 2: Avec fichier config personnalisé
python3 run.py /path/to/custom/config.yaml

# Méthode 3: Directement via main.py
python3 -m src.main
```

### Vérifier l'installation

```bash
python3 run.py --check
```

### Créer la configuration

```bash
python3 run.py --setup
```

### Obtenir l'aide

```bash
python3 run.py --help
```

## 📊 Caractéristiques Clés

### 1. Gestion Robuste de la Configuration

```python
# Cherche config.yaml
# Si non trouvé → utilise config.yaml.example
# Si non trouvé → erreur avec messages clairs
```

### 2. Sauvegarde Automatique

```python
if config.database.backup_on_startup:
    backup_path = db.backup_database()
    logger.info(f"✓ Sauvegarde créée: {backup_path}")
```

### 3. Vérification du Schéma

```python
if not db.verify_schema():
    logger.error("Schéma Lyrion invalide!")
    return False
```

### 4. Application de la Configuration UI

```python
# Taille de fenêtre
root.geometry(config.ui.window_size)

# Thème
window.style.theme_use(config.ui.theme)
```

## 🔧 Configuration par Étapes

### Étape 1: Logging

```python
logger = setup_logger('app', 'INFO', './logs/sync.log')
logger.info("=== Démarrage ===")
```

- Console: `[LEVEL] message`
- Fichier: `[TIMESTAMP] [LEVEL] [name] message`

### Étape 2: Configuration

```python
config = Config.instance()
config.load_from_file('config.yaml')
config.validate()
```

- Charge depuis YAML
- Valide les paramètres
- Auto-corrige les valeurs invalides

### Étape 3: Base de Données

```python
db = DatabaseManager(db_path)
db.connect()
db.backup_database()
db.verify_schema()
```

- Établit la connexion
- Crée une sauvegarde (optionnel)
- Vérifie le schéma Lyrion

### Étape 4: Composants

```python
detector = SyncDetector(db)
matcher = TrackMatcher(config.matching)
```

- Initialise le détecteur de synchronisation
- Initialise le matcher de pistes avec config

### Étape 5: Interface

```python
root = tk.Tk()
window = MainWindow(root, db, detector, matcher, config)
root.mainloop()
```

- Crée la fenêtre principale
- Lance la boucle événementielle

### Étape 6: Cleanup

```python
finally:
    db.close()
    logger.info("=== Arrêt propre ===")
```

- Ferme la BD proprement
- Enregistre l'arrêt

## 📚 Intégration avec run.py

Le script [run.py](run.py) fournit :

1. **Vérification d'installation** (`--check`)
   - Dépendances Python
   - Structure de répertoires
   - Fichiers principaux

2. **Configuration initiale** (`--setup`)
   - Crée `config.yaml` depuis l'exemple
   - Messages de configuration

3. **Démarrage intelligent**
   - Vérifie la config avant de lancer
   - Crée la config si manquante
   - Affiche les erreurs clairement

## ✨ Points Forts

✅ **Modularité** - Chaque étape indépendante  
✅ **Robustesse** - Gestion complète des erreurs  
✅ **Logging** - Traçabilité complète  
✅ **Cleanup** - Arrêt propre garanti  
✅ **Configuration** - YAML avec validation  
✅ **Exit codes** - Codes d'erreur appropriés  
✅ **Documentation** - Docstrings complets  

## 🔍 Vérification

```bash
# Vérifier la syntaxe
python3 -m py_compile src/main.py

# Vérifier les imports
python3 -c "from src.main import Application; print('✅ OK')"

# Vérifier run.py
python3 run.py --check
```

## 📝 Résumé

| Aspect | Détail |
|--------|--------|
| **Fichier** | src/main.py (330 lignes) |
| **Classe** | Application |
| **Étapes** | 6 (Logging, Config, BD, Components, UI, Cleanup) |
| **Gestion d'erreurs** | Try/except sur chaque étape |
| **Cleanup** | Garanti en finally |
| **Exit codes** | 0 = succès, 1 = erreur |
| **Logging** | Complet avec timestamps |
| **Configuration** | YAML + validation + fallback |
| **Status** | ✅ PRÊT POUR PRODUCTION |

---

**Date:** 2026-01-24  
**Status:** ✅ COMPLET
