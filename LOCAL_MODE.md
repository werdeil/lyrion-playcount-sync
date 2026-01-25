# 🐍 MODE LOCAL PYTHON

**Nouveau!** Vous pouvez maintenant lancer l'application **sans Docker**, en Python pur.

---

## ⚡ Démarrage Rapide

```bash
# Mode Docker (par défaut)
python3 scripts/launch.py /path/to/lyrion/prefs

# Mode Local Python (nouveau)
python3 scripts/launch.py /path/to/lyrion/prefs --local
```

---

## 🎯 Mode Local - Caractéristiques

### Avantages
- ✅ **Pas de Docker requis** - Juste Python
- ✅ **Démarrage très rapide** - Pas de conteneur
- ✅ **GUI native** - Tkinter directement
- ✅ **Parfait pour développement** - Plus facile à déboguer
- ✅ **Moins de ressources** - Pas d'isolation OS
- ✅ **Même commande** - `--local` flag suffit

### Comment ça marche
1. Les dépendances Python sont **auto-installées**
2. L'app charge directement depuis `src/main.py`
3. La GUI Tkinter s'ouvre **automatiquement**
4. Accès direct à la base de données Lyrion

---

## 📋 Exemples Complets

### Docker vs Local (même commande!)
```bash
# DOCKER (VNC web + client)
python3 scripts/launch.py /path/to/lyrion/prefs

# LOCAL (GUI native)
python3 scripts/launch.py /path/to/lyrion/prefs --local
```

### Par Plateforme (Mode Local)
```bash
# Synology
python3 scripts/launch.py /volume1/docker/squeezebox-lms/prefs --local

# Linux
python3 scripts/launch.py /var/lib/squeezeboxserver/prefs --local

# macOS
python3 scripts/launch.py ~/Library/Application\ Support/Squeezebox/prefs --local

# Windows WSL
python3 scripts/launch.py /mnt/c/Users/YourName/AppData/Local/Squeezebox/prefs --local
```

---

## 🔧 Options Local

```bash
# Démarrer (défaut)
python3 scripts/launch.py /path/to/prefs --local

# Voir les logs
python3 scripts/launch.py /path/to/prefs --local --logs

# Vérifier le statut
python3 scripts/launch.py /path/to/prefs --local --status

# Mode verbose (déboguer)
python3 scripts/launch.py /path/to/prefs --local --verbose
```

---

## 📊 Comparaison

| Feature | Docker | Local |
|---------|--------|-------|
| Interface | VNC (web + client) | Tkinter (native) |
| Démarrage | 10-15 sec | < 2 sec |
| Dépendances | Docker requis | Python requis |
| Ressources | Plus lourd | Plus léger |
| Développement | Moins idéal | Parfait |
| Production | Idéal | Acceptable |
| Commande | `python3 scripts/launch.py /path` | `python3 scripts/launch.py /path --local` |

---

## ✅ Validation Automatique

Le launcher vérifie et crée automatiquement:
- ✅ Répertoire Lyrion existe
- ✅ `persist.db` existe
- ✅ Dossier `logs/` (création si nécessaire)
- ✅ `config.yaml` (copie depuis exemple si nécessaire)
- ✅ `.env` (copie depuis exemple si nécessaire)
- ✅ Dépendances Python (installation via pip si nécessaire)

---

## 🚀 Cas d'Usage

### Développement Local
```bash
python3 scripts/launch.py /path/to/local/lyrion/prefs --local
```

### Test Rapide
```bash
python3 scripts/launch.py /path/to/prefs --local
```

### Machine sans Docker
```bash
# Machine ne supportant pas Docker?
# Pas de problème:
python3 scripts/launch.py /path/to/prefs --local
```

### Production (Recommended)
```bash
# Docker pour isolation:
python3 scripts/launch.py /path/to/prefs
```

---

## 📋 Dépendances Python

```
ttkbootstrap>=1.10.0      # UI moderne
rapidfuzz>=3.0.0          # Fuzzy matching
pyyaml>=6.0               # Configuration YAML
python-dotenv>=1.0.0      # Variables d'environnement
```

**Installation automatique** si manquantes!

---

## 🔍 Debugging

### Verbose Mode
```bash
python3 scripts/launch.py /path/to/prefs --local --verbose
```

Affiche:
- Variables d'environnement
- Chemins Python
- État des validations
- Traceback complets en cas d'erreur

### Logs
```bash
# Voir les logs
python3 scripts/launch.py /path/to/prefs --local --logs

# Suivre en temps réel
python3 scripts/launch.py /path/to/prefs --local --logs --follow
```

---

## 💡 Notes

1. **Python 3.8+** requis
2. **macOS/Linux** optimisé
3. **Windows** supporté via WSL
4. **Tkinter** doit être disponible (`python3-tk` sur Linux)

---

**Version** : 1.0  
**Date** : 25 janvier 2026  
**Status** : Production-Ready ✅
