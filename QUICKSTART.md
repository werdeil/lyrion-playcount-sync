# Guide de Démarrage Rapide

## 🚀 Installation en 5 minutes

### Sur macOS/Linux

```bash
# 1. Se placer dans le répertoire
cd lyrion-playcount-sync

# 2. Lancer le script d'installation
chmod +x setup.sh
./setup.sh

# 3. Configurer l'application
nano config.yaml
# Adapter le chemin database.path selon votre installation

# 4. Lancer l'application
source venv/bin/activate
python -m src.main
```

### Sur Windows

```bash
# 1. Se placer dans le répertoire
cd lyrion-playcount-sync

# 2. Lancer le script d'installation
setup.bat

# 3. Configurer l'application
# Éditer config.yaml avec votre éditeur préféré

# 4. Lancer l'application
venv\Scripts\activate.bat
python -m src.main
```

### Docker

```bash
# 1. Éditer config.yaml
cp config.yaml.example config.yaml
nano config.yaml

# 2. Lancer avec docker-compose
docker-compose up -d

# 3. Se connecter via VNC sur localhost:5901
# Mot de passe: password
```

## 📍 Chemins par OS

Adapter `config.yaml` selon votre OS :

### Linux
```yaml
database:
  path: "/var/lib/squeezeboxserver/prefs/server.prefs"
```

### macOS
```yaml
database:
  path: "~/Library/Application Support/Squeezebox/prefs/server.prefs"
```

### Windows
```yaml
database:
  path: "C:\\ProgramData\\Squeezebox\\prefs\\server.prefs"
```

## 🎯 Utilisation basique

1. **Lancer l'application** : `python -m src.main`
2. **Charger les données** : Cliquer sur "Charger les données"
3. **Trouver correspondances** : Cliquer sur "Trouver correspondances"
4. **Synchroniser** : Cliquer sur "Synchroniser"

## ⚙️ Configuration avancée

### Réduire les faux positifs

Si vous avez trop de correspondances incorrectes :

```yaml
matching:
  similarity_threshold: 90  # Augmenter de 85 à 90
```

### Améliorer la détection

Si vous manquez des correspondances :

```yaml
matching:
  ratio_method: "token_set_ratio"  # Permet plus de variations
  similarity_threshold: 80  # Réduire le seuil
```

### Modes de synchronisation

```yaml
sync:
  # Option 1: Copier les playcounts de tracks_persistent
  direction: "from_tracks"
  
  # Option 2: Copier de alternativeplaycount
  direction: "from_alternative"
  
  # Option 3: Garder le maximum des deux tables
  direction: "merge"
```

## 🐛 Dépannage

### "Base de données non trouvée"
1. Vérifier le chemin dans `config.yaml`
2. S'assurer que Lyrion est arrêté
3. Vérifier les permissions d'accès

### Pas de correspondances
1. Réduire `similarity_threshold` à 75-80
2. Essayer `token_set_ratio` comme méthode
3. Vérifier que les noms d'artistes sont cohérents

### Problèmes Docker
```bash
# Voir les logs
docker logs lyrion-playcount-sync

# Reconnecter le VNC
# Port: 5901
# Password: password
```

## 📚 Documentation complète

Voir [README.md](README.md) pour la documentation complète.

## 💡 Conseils d'usage

1. **Toujours faire une sauvegarde** : Activer `backup_before_sync: true`
2. **Tester d'abord** : Lancer en mode "non-auto-apply"
3. **Vérifier les résultats** : Examiner les correspondances avant de synchroniser
4. **Consulter les logs** : Fichier `playcount_sync.log` pour le débogage

## 🔗 Ressources

- [Documentation Lyrion](https://www.lyrion.org/)
- [Logitech Media Server](https://github.com/LMS-Community/slimserver)
- [ttkbootstrap](https://ttkbootstrap.readthedocs.io/)
- [rapidfuzz](https://maxbachmann.github.io/RapidFuzz/)
