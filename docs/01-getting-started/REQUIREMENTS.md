# 📋 Requirements - Prérequis et Dépendances

## 🖥️ Prérequis Système

### Tous les Systèmes

- **Python 3.9+** (testé avec 3.9, 3.10, 3.11)
- **Accès à persist.db** de Lyrion (lecture + écriture)
- **Lyrion/Squeezebox installé** (arrêté pendant l'utilisation)

### macOS

- Xcode Command Line Tools (pour installer Python si nécessaire)
- Tkinter (inclus avec Python)

### Linux

```bash
# Debian/Ubuntu
sudo apt-get install python3 python3-tk python3-venv

# Fedora/RHEL
sudo dnf install python3 python3-tkinter python3-venv

# Arch
sudo pacman -S python tk
```

### Windows

- Python 3.9+ depuis [python.org](https://www.python.org)
- Cocher "Install tcl/tk and IDLE" lors de l'installation

## 🐳 Docker

Pour le déploiement Docker :

- **Docker** 20.10+
- **Docker Compose** 1.29+

Installer depuis : https://docs.docker.com/get-docker/

## 📦 Dépendances Python

### Installation Standard

```bash
pip install -r requirements.txt
```

### Packages Inclus

| Package | Version | Utilisé Pour |
|---------|---------|--------------|
| **PyYAML** | ^6.0 | Configuration YAML |
| **rapidfuzz** | ^3.0 | Matching fuzzy |
| **ttkbootstrap** | ^1.6 | Interface GUI moderne |
| **python-dotenv** | ^1.0 | Variables d'environnement |

### Dépendances Dev (Tests)

```bash
pip install -r requirements-dev.txt
```

| Package | Utilisé Pour |
|---------|--------------|
| **pytest** | Framework de tests |
| **pytest-cov** | Coverage des tests |
| **black** | Formatage code |
| **flake8** | Linting |
| **mypy** | Type checking |

## 🗄️ Base de Données Lyrion

### Fichier Principal

**Chemin selon l'OS** :

| OS | Chemin |
|-------|--------|
| **Linux** | `/var/lib/squeezeboxserver/prefs/` |
| **macOS** | `~/Library/Application Support/Squeezebox/prefs/` |
| **Windows** | `C:\ProgramData\Squeezebox\prefs\` |
| **Synology NAS** | `/volume1/docker/squeezebox-lms/prefs/` |

### Fichier Base de Données

```
persist.db          # Base SQLite principale
```

**Permissions requises** :
- Lecture : OUI (obligatoire)
- Écriture : OUI (obligatoire)

Pour vérifier/corriger :

```bash
# Linux/macOS
ls -la /path/to/persist.db
chmod 666 /path/to/persist.db

# Windows (propriétés → Sécurité)
```

## 🔍 Vérifier les Prérequis

### Python

```bash
python3 --version
# Résultat attendu: Python 3.9.x ou supérieur

python3 -c "import tkinter; print('✓ Tkinter disponible')"
```

### Lyrion

```bash
# Vérifier Lyrion est ARRÊTÉ
ps aux | grep -i lyrion
ps aux | grep -i squeezebox

# Vérifier l'accès à la BD
ls -la /path/to/lyrion/persist.db
```

### Docker

```bash
docker --version
# Résultat attendu: Docker version 20.10+

docker-compose --version
# Résultat attendu: Docker Compose version 1.29+
```

### Accès BD

```bash
# Tester l'accès
sqlite3 /path/to/persist.db ".tables"

# Résultat attendu: affiche les tables
```

## 🚨 Problèmes Courants

### Python 3 non disponible

**Solution** :
```bash
# macOS
brew install python3

# Linux (Debian)
sudo apt-get install python3

# Windows
Télécharger depuis python.org
```

### Tkinter manquant

**Solution** :
```bash
# Linux (Debian)
sudo apt-get install python3-tk

# Linux (Fedora)
sudo dnf install python3-tkinter

# macOS (Homebrew)
brew install python-tk
```

### Permissions persist.db

**Solution** :
```bash
chmod 666 /path/to/persist.db
chmod 755 /path/to/lyrion/
```

### Docker Compose manquant

**Solution** :
```bash
# Installation
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Vérifier
docker-compose --version
```

## ✅ Checklist Pré-Installation

Avant de commencer, vérifier :

- [ ] Python 3.9+ installé
- [ ] Tkinter disponible (`python3 -c "import tkinter"`)
- [ ] Lyrion **complètement arrêté**
- [ ] Accès lecture/écriture à persist.db
- [ ] Docker & Compose installés (si utilisant Docker)
- [ ] Port 5900 disponible (VNC)
- [ ] Port 6080 disponible (noVNC)

## 📚 Ressources

- [Python Official](https://www.python.org)
- [Docker Docs](https://docs.docker.com)
- [Lyrion Documentation](https://lyrion.org)
- [RapidFuzz Docs](https://maxbachmann.github.io/RapidFuzz)

---

**Prêt ?** → [Installation Docker](../02-installation/DOCKER.md) ou [Installation Locale](../02-installation/LOCAL.md)
