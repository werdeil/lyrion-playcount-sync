# Instructions d'installation complètes

## Prérequis

- **Python 3.11+** (vérifier avec `python3 --version`)
- **pip** (gestionnaire de paquets Python)
- **Accès à la base de données Lyrion** (fichier `server.prefs` ou `persist.db`)
- **(Optionnel) Docker et Docker Compose** pour le déploiement conteneurisé

## Installation locale

### Étape 1 : Récupérer le code

```bash
# Cloner le dépôt (ou télécharger le ZIP)
git clone https://github.com/yourusername/lyrion-playcount-sync.git
cd lyrion-playcount-sync
```

### Étape 2 : Créer un environnement virtuel

L'environnement virtuel isole les dépendances du projet.

**macOS/Linux :**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows :**
```bash
python -m venv venv
venv\Scripts\activate.bat
```

### Étape 3 : Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 4 : Configuration

#### Option A : Utiliser le script automatisé (recommandé)

**macOS/Linux :**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows :**
```bash
setup.bat
```

#### Option B : Configuration manuelle

1. **Copier le fichier exemple :**
```bash
cp config.yaml.example config.yaml
```

2. **Éditer `config.yaml` :**
   - Adapter `database.path` selon votre OS et installation Lyrion
   - (Optionnel) Ajuster les paramètres de matching et synchronisation

3. **Copier le fichier d'environnement (optionnel) :**
```bash
cp .env.example .env
# Éditer .env selon vos besoins
```

## Localiser la base de données Lyrion

### Linux
```bash
# Trouver le fichier
find / -name "server.prefs" 2>/dev/null
find / -name "persist.db" 2>/dev/null

# Chemin typique
/var/lib/squeezeboxserver/prefs/server.prefs
/var/lib/squeezeboxserver/prefs/persist.db
```

### macOS
```bash
# Chemin typique
~/Library/Application Support/Squeezebox/prefs/server.prefs
~/Library/Application Support/Squeezebox/prefs/persist.db

# Ou selon la version
~/Library/Application\ Support/Logitech/Squeezebox/prefs/server.prefs
```

### Windows
```bash
# Chemin typique
C:\ProgramData\Squeezebox\prefs\server.prefs
C:\ProgramData\Squeezebox\prefs\persist.db

# Ou
C:\Users\[YourUsername]\AppData\Roaming\Squeezebox\prefs\server.prefs
```

## Configuration détaillée

### config.yaml

```yaml
database:
  # Chemin vers la base de données (OBLIGATOIRE)
  path: "/var/lib/squeezeboxserver/prefs/server.prefs"
  # Créer une sauvegarde avant modification
  backup: true

matching:
  # Seuil de similarité (0-100)
  # Plus élevé = plus strict (moins de faux positifs)
  # Plus bas = plus permissif (plus de correspondances)
  similarity_threshold: 85
  
  # Méthode de comparaison
  # - ratio: Comparaison simple (0-100)
  # - partial_ratio: Cherche les substrings
  # - token_sort_ratio: Ignore l'ordre des mots
  # - token_set_ratio: Combine ordre et ensemble (moins de doublons)
  ratio_method: "token_sort_ratio"

sync:
  # Direction de synchronisation
  # - "from_tracks": Copier de tracks_persistent vers alternativeplaycount
  # - "from_alternative": Copier de alternativeplaycount vers tracks_persistent
  # - "merge": Prendre la valeur maximale des deux
  direction: "merge"
  
  # Appliquer automatiquement sans confirmation
  auto_apply: false
  
  # Sauvegarder la BD avant de synchroniser
  backup_before_sync: true

logging:
  # Niveau de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  # Fichier de log (optionnel)
  file: "playcount_sync.log"
```

### Variables d'environnement (.env)

Optionnellement, vous pouvez utiliser un fichier `.env` :

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer .env
nano .env
```

Les variables d'environnement surchargent les valeurs de `config.yaml`.

## Lancer l'application

### Mode développement

```bash
# S'assurer que l'environnement virtuel est activé
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate.bat  # Windows

# Lancer l'application
python -m src.main
```

### Avec logs détaillés

```bash
# DEBUG level
export LOG_LEVEL=DEBUG
python -m src.main
```

## Installation Docker

### Option 1 : Docker Compose (recommandé)

```bash
# 1. Éditer docker-compose.yml pour adapter les volumes
nano docker-compose.yml
# Adapter le chemin vers la BD Lyrion

# 2. Lancer les conteneurs
docker-compose up -d

# 3. Vérifier le statut
docker-compose ps

# 4. Voir les logs
docker-compose logs -f lyrion-playcount-sync
```

### Option 2 : Docker manuel

```bash
# 1. Construire l'image
docker build -t lyrion-playcount-sync:latest .

# 2. Lancer le conteneur
docker run -d \
  --name lyrion-sync \
  -p 5901:5901 \
  -v /var/lib/squeezeboxserver:/squeezeboxserver:ro \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  lyrion-playcount-sync:latest

# 3. Accéder via VNC
# Client VNC -> localhost:5901
# Mot de passe: password
```

### Accès VNC

1. **Installer un client VNC** :
   - Linux : `sudo apt install vinagre` ou `vncviewer`
   - macOS : `brew install vnc-viewer`
   - Windows : TightVNC, RealVNC, UltraVNC

2. **Se connecter** :
   - Hôte : `localhost` ou IP du serveur
   - Port : `5901`
   - Mot de passe : `password`

3. **Changer le mot de passe** (dans le conteneur) :
   ```bash
   docker exec -it lyrion-sync vncpasswd
   ```

## Dépannage

### "Module not found" lors du lancement

```bash
# S'assurer que l'environnement virtuel est activé
source venv/bin/activate  # macOS/Linux

# Réinstaller les dépendances
pip install -r requirements.txt
```

### "Base de données non trouvée"

1. Vérifier le chemin dans `config.yaml` :
```bash
# Tester l'accès au fichier
ls -la /chemin/vers/server.prefs
file /chemin/vers/server.prefs
```

2. S'assurer que Lyrion est **arrêté** avant la synchronisation

3. Vérifier les permissions :
```bash
# Lire : OK
# Écrire : Nécessaire pour la synchronisation
```

### "Aucune correspondance trouvée"

1. **Réduire le seuil de similarité** :
```yaml
matching:
  similarity_threshold: 75  # Au lieu de 85
```

2. **Essayer une autre méthode** :
```yaml
matching:
  ratio_method: "token_set_ratio"
```

3. **Vérifier les données** :
   - Les titres/artistes sont-ils bien remplies dans les deux tables ?
   - Y a-t-il des différences (majuscules, accents, tirets) ?

### Problèmes de connexion Docker

```bash
# Vérifier les logs
docker logs lyrion-playcount-sync

# Vérifier la configuration du volume
docker exec lyrion-playcount-sync ls -la /squeezeboxserver/

# Reconstruire l'image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### "Permission denied" sur fichiers/répertoires

```bash
# Vérifier les permissions
ls -l config.yaml logs/

# Corriger si nécessaire
chmod 644 config.yaml
chmod 755 logs/
```

## Vérification de l'installation

```bash
# 1. Vérifier Python
python3 --version

# 2. Vérifier l'environnement virtuel
source venv/bin/activate
which python

# 3. Vérifier les dépendances
pip list | grep -E "ttkbootstrap|rapidfuzz|pyyaml|python-dotenv"

# 4. Vérifier la structure du projet
ls -la src/
ls -la requirements.txt config.yaml.example

# 5. Tester l'import
python -c "from src.ui import MainWindow; print('✓ Imports OK')"
```

## Prochaines étapes

1. **Lire la documentation** : [README.md](README.md)
2. **Guide de démarrage rapide** : [QUICKSTART.md](QUICKSTART.md)
3. **Lancer l'application** : `python -m src.main`
4. **Consulter les logs** : `playcount_sync.log`

## Support

Pour les problèmes :
1. Consulter [QUICKSTART.md](QUICKSTART.md) - section Dépannage
2. Vérifier les logs : `cat playcount_sync.log`
3. Ouvrir une issue sur GitHub avec logs et configuration
