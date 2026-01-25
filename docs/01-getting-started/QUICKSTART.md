# 🚀 Quick Start - 5 minutes

Démarrer Lyrion Playcount Sync en 5 minutes.

## ⚡ Installation Express (Docker)

```bash
# 1. Cloner et configurer
git clone https://github.com/ton-user/lyrion-playcount-sync.git
cd lyrion-playcount-sync
cp config/.env.example .env

# 2. Éditer .env
nano .env
# ➜ Changer LYRION_DATA_PATH selon votre système

# 3. Lancer
docker-compose -f config/docker-compose.yml up -d

# 4. Accéder
# Navigateur : http://localhost:6080/vnc.html
# Client VNC : vnc://localhost:5900
```

## 📋 Prérequis Avant de Commencer

⚠️ **CRITIQUE** : Arrêter Lyrion avant toute synchronisation

```bash
# Vérifier que Lyrion n'est pas en cours
ps aux | grep -i lyrion
ps aux | grep -i squeezebox

# Si en cours, l'arrêter
sudo killall squeezebox
sleep 5
```

## 🎯 Première Utilisation

### Étape 1 : Scanner
```
Cliquer "🔄 Scanner"
→ Détecte les incohérences
→ Affiche les statistiques
```

### Étape 2 : Analyser
```
Double-cliquer sur un morceau
→ Voir les matches proposés
→ Vérifier la qualité (couleur)
```

### Étape 3 : Synchroniser
```
Sélectionner un match
→ Choisir l'action (Copier/Fusionner)
→ Cliquer "Appliquer"
```

## 🔧 Configuration Minimale

Fichier `config.yaml` (auto-généré) :

```yaml
matching:
  auto_match_threshold: 90      # Score auto-sync
  suggestion_min_score: 50       # Score min affichage

sync:
  default_action: "COPY"         # COPY ou MERGE
  delete_after_sync: true        # Cleanup
```

## ❌ Ça ne marche pas ?

| Problème | Solution |
|----------|----------|
| "Database is locked" | Arrêter Lyrion complètement |
| "Permission denied" | `chmod 666 persist.db` |
| VNC ne répond pas | Attendre 10 sec après up |
| "No matches found" | Baisser `suggestion_min_score` |

## ✅ Vérifier que tout fonctionne

```bash
# Voir les logs
docker-compose -f config/docker-compose.yml logs lyrion-sync

# Tester la connexion
docker-compose -f config/docker-compose.yml exec lyrion-sync python3 scripts/run.py --check

# Redémarrer si besoin
docker-compose -f config/docker-compose.yml restart lyrion-sync
```

## 📚 Après les premiers pas

- [Installation complète](../02-installation/)
- [Guide utilisateur](../04-usage/USER_GUIDE.md)
- [Configuration avancée](../03-configuration/CONFIG.md)
- [Troubleshooting](../02-installation/TROUBLESHOOTING.md)

---

**Besoin d'aide ?** → Lire [TROUBLESHOOTING.md](../02-installation/TROUBLESHOOTING.md)
