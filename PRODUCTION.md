# Guide de Production - Lyrion Playcount Synchronizer

## 🚀 Déploiement en Production

Ce guide explique comment déployer et maintenir l'application en environnement de production.

## 📋 Checklist Pre-Production

### 1. Vérification du Code

```bash
# Vérifier la syntaxe
python3 -m py_compile src/**/*.py

# Vérifier le style
python3 -m flake8 src/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports

# Tous les tests DOIVENT passer
python3 -m pytest tests/ -v --tb=short
```

### 2. Sauvegarde de Base

```bash
# Créer une sauvegarde complète AVANT de commencer
sqlite3 /path/to/persist.db ".backup '/path/to/backup_pre_deployment.db'"

# Vérifier l'intégrité
sqlite3 /path/to/persist.db "PRAGMA integrity_check;"
# Résultat attendu: "ok"
```

### 3. Configuration

```bash
# Créer un fichier de configuration pour la production
cat > config_production.json << 'EOF'
{
  "database_path": "/var/lib/lyrion/persist.db",
  "backup_directory": "/var/backups/lyrion",
  "logging": {
    "level": "INFO",
    "file": "/var/log/lyrion/sync.log",
    "max_bytes": 10485760,
    "backup_count": 5
  },
  "matching": {
    "min_score": 75.0,
    "title_weight": 0.7,
    "artist_weight": 0.2,
    "album_weight": 0.1
  },
  "sync": {
    "auto_backup": true,
    "stop_on_failure": false,
    "max_batch_size": 100
  }
}
EOF
```

## 🔧 Installation Production

### 1. Préparation du Serveur

```bash
# Créer un utilisateur dédié
sudo useradd -r -s /bin/bash lyrion_sync

# Créer les répertoires
sudo mkdir -p /opt/lyrion-sync
sudo mkdir -p /var/log/lyrion
sudo mkdir -p /var/backups/lyrion
sudo mkdir -p /var/lib/lyrion

# Définir les permissions
sudo chown -R lyrion_sync:lyrion_sync /opt/lyrion-sync
sudo chown -R lyrion_sync:lyrion_sync /var/log/lyrion
sudo chown -R lyrion_sync:lyrion_sync /var/backups/lyrion
sudo chmod 755 /opt/lyrion-sync
sudo chmod 755 /var/log/lyrion
sudo chmod 755 /var/backups/lyrion
```

### 2. Déployer le Code

```bash
# Cloner ou copier le code
sudo cp -r lyrion-playcount-sync /opt/lyrion-sync

# Installer en mode production
cd /opt/lyrion-sync
sudo -u lyrion_sync python3 -m venv venv
sudo -u lyrion_sync venv/bin/pip install --no-cache-dir -r requirements.txt

# Vérifier l'installation
sudo -u lyrion_sync venv/bin/python3 -c "import src; print('✅ Installation OK')"
```

### 3. Configurer le Logging

```bash
# Créer un fichier logrotate
sudo tee /etc/logrotate.d/lyrion-sync << 'EOF'
/var/log/lyrion/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 lyrion_sync lyrion_sync
    sharedscripts
    postrotate
        systemctl reload lyrion-sync > /dev/null 2>&1 || true
    endscript
}
EOF
```

## 🔄 Exécution en Mode Service (Systemd)

### 1. Créer un Service Systemd

```bash
sudo tee /etc/systemd/system/lyrion-sync.service << 'EOF'
[Unit]
Description=Lyrion Playcount Synchronizer
After=network.target

[Service]
Type=simple
User=lyrion_sync
WorkingDirectory=/opt/lyrion-sync
Environment="PATH=/opt/lyrion-sync/venv/bin"
ExecStart=/opt/lyrion-sync/venv/bin/python3 /opt/lyrion-sync/main.py

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lyrion-sync

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/lyrion /var/log/lyrion /var/backups/lyrion

# Restart policy
Restart=on-failure
RestartSec=30s
StartLimitInterval=300s
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd
sudo systemctl daemon-reload
```

### 2. Démarrer le Service

```bash
# Démarrer
sudo systemctl start lyrion-sync

# Vérifier le statut
sudo systemctl status lyrion-sync

# Activer au démarrage
sudo systemctl enable lyrion-sync

# Voir les logs
sudo journalctl -u lyrion-sync -f
```

## 🔍 Monitoring

### 1. Vérifier la Santé

```bash
#!/bin/bash
# health_check.sh

DB_PATH="/var/lib/lyrion/persist.db"

# Vérifier que le fichier existe
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    exit 1
fi

# Vérifier l'intégrité
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "❌ Database integrity check failed: $INTEGRITY"
    exit 1
fi

# Vérifier les tables
TABLES=$(sqlite3 "$DB_PATH" "SELECT count(*) FROM sqlite_master WHERE type='table';")
if [ "$TABLES" -lt 2 ]; then
    echo "❌ Not enough tables: $TABLES"
    exit 1
fi

echo "✅ Health check passed"
echo "  Tables: $TABLES"
echo "  Integrity: OK"
exit 0
```

### 2. Monitoring des Ressources

```bash
#!/bin/bash
# monitor.sh

# CPU et Memory
ps aux | grep "[p]ython3.*main.py" | awk '{print "CPU: " $3 "%, MEM: " $6 "KB"}'

# Disk space
df -h /var/lib/lyrion | tail -1

# Database size
ls -lh /var/lib/lyrion/persist.db | awk '{print "DB size: " $5}'

# Backup size
du -sh /var/backups/lyrion | awk '{print "Backups: " $1}'

# Recent errors
journalctl -u lyrion-sync -n 10 --no-pager | grep ERROR
```

## 🔐 Sécurité

### 1. File Permissions

```bash
# Fichiers
sudo chmod 640 /var/lib/lyrion/persist.db
sudo chmod 640 /etc/lyrion/config_production.json

# Répertoires
sudo chmod 750 /opt/lyrion-sync
sudo chmod 750 /var/lib/lyrion
sudo chmod 750 /var/backups/lyrion
sudo chmod 750 /var/log/lyrion
```

### 2. Firewall

```bash
# Si l'app expose une API (futur):
sudo ufw allow 8080/tcp  # Exemple

# SSH pour administration
sudo ufw allow 22/tcp
```

### 3. Selinux (si applicable)

```bash
# Vérifier le contexte
ls -Z /opt/lyrion-sync

# Ajouter une politique personnalisée si nécessaire
```

## 📊 Backups

### 1. Backup Automatique

```bash
#!/bin/bash
# backup.sh

DB_PATH="/var/lib/lyrion/persist.db"
BACKUP_DIR="/var/backups/lyrion"
RETENTION_DAYS=30

# Créer un backup
BACKUP_FILE="$BACKUP_DIR/persist_$(date +%Y%m%d_%H%M%S).db"
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

echo "✅ Backup created: $BACKUP_FILE"

# Nettoyer les vieux backups
find "$BACKUP_DIR" -type f -name "persist_*.db" -mtime +$RETENTION_DAYS -delete

echo "✅ Old backups cleaned"
```

### 2. Backup Programmé (Cron)

```bash
# Ajouter au crontab
sudo -u lyrion_sync crontab -e

# Ajouter ces lignes:
# Daily backup at 2:00 AM
0 2 * * * /opt/lyrion-sync/scripts/backup.sh >> /var/log/lyrion/backup.log 2>&1

# Weekly full check on Sunday at 3:00 AM
0 3 * * 0 /opt/lyrion-sync/scripts/health_check.sh >> /var/log/lyrion/health.log 2>&1
```

## 🔄 Mise à Jour

### 1. Avant la Mise à Jour

```bash
# 1. Créer un backup
sudo -u lyrion_sync sqlite3 /var/lib/lyrion/persist.db ".backup '/var/backups/lyrion/backup_pre_update.db'"

# 2. Arrêter le service
sudo systemctl stop lyrion-sync

# 3. Vérifier l'intégrité
sqlite3 /var/lib/lyrion/persist.db "PRAGMA integrity_check;"
```

### 2. Mettre à Jour le Code

```bash
cd /opt/lyrion-sync

# Mettre à jour les fichiers
sudo -u lyrion_sync git pull origin main
# ou
sudo cp -r lyrion-playcount-sync/* .

# Installer les nouvelles dépendances
sudo -u lyrion_sync venv/bin/pip install -r requirements.txt

# Exécuter les migrations si nécessaire
sudo -u lyrion_sync venv/bin/python3 scripts/migrate.py
```

### 3. Après la Mise à Jour

```bash
# 1. Tester l'application
sudo -u lyrion_sync venv/bin/python3 -m pytest tests/ -v

# 2. Redémarrer le service
sudo systemctl start lyrion-sync

# 3. Vérifier le statut
sudo systemctl status lyrion-sync

# 4. Monitorer les logs
sudo journalctl -u lyrion-sync -f
```

## 🚨 Dépannage Production

### 1. Service ne démarre pas

```bash
# Vérifier les erreurs
sudo systemctl status lyrion-sync
sudo journalctl -u lyrion-sync -n 50 --no-pager

# Redémarrer proprement
sudo systemctl restart lyrion-sync

# Vérifier les permissions
ls -la /var/lib/lyrion/persist.db
sudo chown lyrion_sync:lyrion_sync /var/lib/lyrion/persist.db
```

### 2. Base de données verrouillée

```bash
# Vérifier les processus
lsof | grep persist.db

# Vérifier les connexions SQLite
sqlite3 /var/lib/lyrion/persist.db "PRAGMA busy_timeout = 5000;"

# Si vraiment bloqué, créer une nouvelle DB à partir du backup
cp /var/backups/lyrion/backup_recent.db /var/lib/lyrion/persist.db
```

### 3. Espace disque faible

```bash
# Vérifier l'utilisation
df -h

# Nettoyer les vieux backups
find /var/backups/lyrion -mtime +30 -delete

# Compacter la DB
sqlite3 /var/lib/lyrion/persist.db "VACUUM;"

# Vérifier la taille
du -sh /var/lib/lyrion/persist.db
```

## 📈 Performance Production

### 1. Tuning SQLite

```python
# Dans src/database/operations.py

def __init__(self, db_path):
    self.conn = sqlite3.connect(
        db_path,
        timeout=30,
        check_same_thread=False
    )
    
    # Pour production
    self.conn.execute("PRAGMA journal_mode = WAL")      # Write-Ahead Logging
    self.conn.execute("PRAGMA synchronous = NORMAL")    # Plus rapide
    self.conn.execute("PRAGMA cache_size = 10000")      # Augmente le cache
    self.conn.execute("PRAGMA temp_store = MEMORY")     # Temp en RAM
    self.conn.execute("PRAGMA foreign_keys = ON")       # Intégrité
```

### 2. Indexation

```sql
-- Créer des index sur les colonnes fréquemment requêtées
CREATE INDEX IF NOT EXISTS idx_tracks_persistent_urlmd5
    ON tracks_persistent(urlmd5);

CREATE INDEX IF NOT EXISTS idx_alternativeplaycount_urlmd5
    ON alternativeplaycount(urlmd5);

CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp
    ON sync_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_sync_log_operation_id
    ON sync_log(operation_id);
```

## 📊 Logs et Métriques

### 1. Configurer le Logging

```python
import logging
import logging.handlers

# Créer un logger formaté
logger = logging.getLogger('lyrion.sync')
logger.setLevel(logging.INFO)

# File handler avec rotation
fh = logging.handlers.RotatingFileHandler(
    '/var/log/lyrion/sync.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
fh.setFormatter(formatter)
logger.addHandler(fh)
```

### 2. Collecter les Métriques

```python
# Exemple de métriques à tracker
metrics = {
    'missing_tracks': 1234,
    'matches_found': 1000,
    'sync_success': 950,
    'sync_failed': 50,
    'avg_match_score': 87.5,
    'sync_duration_ms': 450,
    'db_size_bytes': 5242880
}

# Envoyer à un système de monitoring (Prometheus, etc.)
```

## ✅ Checklist de Lancement

- [ ] Tests: `python3 -m pytest tests/ -v`
- [ ] Backup: `sqlite3 db ".backup backup.db"`
- [ ] Intégrité: `PRAGMA integrity_check;` → OK
- [ ] Permissions: `ls -la /var/lib/lyrion/`
- [ ] Config: `config_production.json` créé
- [ ] Service: `systemctl status lyrion-sync`
- [ ] Logs: `journalctl -u lyrion-sync`
- [ ] Health check: `./health_check.sh` → OK
- [ ] Monitoring: Dashboards configurés
- [ ] Documentation: Équipe informée

## 📞 Support et Escalade

### Contacts d'Escalade

1. **Erreur de Database** → DBA
2. **Erreur de Performance** → DevOps
3. **Erreur de Code** → Development
4. **Erreur de Permission** → Sysadmin

### Procedure d'Incident

1. Page → Check `systemctl status`
2. Vérifier les logs → `journalctl -u lyrion-sync`
3. Vérifier DB → `PRAGMA integrity_check;`
4. Restaurer à partir du backup si nécessaire
5. Ouvrir une issue / ticket
6. Post-mortem après résolution

---

**Version** : 1.0  
**Date** : 24/01/2026  
**Statut** : Production ✅
