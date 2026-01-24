#!/usr/bin/env python3
"""
Lyrion Playcount Synchronizer - Deployment & Migration Script

Ce script facilite le déploiement et la migration de l'application.
"""

import os
import sys
import json
import argparse
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('deploy')


class Deployer:
    """Gère le déploiement et la migration de l'application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialiser le deployer.
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                self.config = json.load(f)
        
        self.db_path = self.config.get('database_path', './persist.db')
        self.backup_dir = self.config.get('backup_directory', './backups')
        self.log_file = self.config.get('log_file', './deploy.log')
    
    def verify_environment(self) -> bool:
        """Vérifier que l'environnement est prêt."""
        logger.info("Vérification de l'environnement...")
        
        # Vérifier Python
        if sys.version_info < (3, 11):
            logger.error(f"Python 3.11+ requis (actuellement {sys.version})")
            return False
        logger.info(f"✅ Python {sys.version.split()[0]} OK")
        
        # Vérifier les dépendances
        try:
            import rapidfuzz
            logger.info("✅ rapidfuzz installé")
        except ImportError:
            logger.error("❌ rapidfuzz non installé (pip install -r requirements.txt)")
            return False
        
        # Vérifier la DB
        if not os.path.exists(self.db_path):
            logger.warning(f"⚠️ Base de données introuvable: {self.db_path}")
            logger.info("   Elle sera créée lors de la première utilisation")
        else:
            logger.info(f"✅ Base de données trouvée: {self.db_path}")
        
        return True
    
    def backup_database(self) -> bool:
        """Créer une sauvegarde de la base de données."""
        if not os.path.exists(self.db_path):
            logger.warning("Pas de base de données à sauvegarder")
            return True
        
        logger.info(f"Sauvegarde de la base de données: {self.db_path}")
        
        # Créer le répertoire de backup
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Nommer le backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(
            self.backup_dir,
            f"persist_backup_{timestamp}.db"
        )
        
        try:
            # Effectuer le backup
            conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            with backup_conn:
                conn.backup(backup_conn)
            
            backup_conn.close()
            conn.close()
            
            # Vérifier la taille
            size_bytes = os.path.getsize(backup_path)
            size_mb = size_bytes / (1024 * 1024)
            
            logger.info(f"✅ Backup créé: {backup_path}")
            logger.info(f"   Taille: {size_mb:.2f} MB")
            
            # Garder seulement les 10 derniers backups
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Supprimer les anciens backups."""
        backups = sorted(
            Path(self.backup_dir).glob('persist_backup_*.db'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[keep_count:]:
            try:
                old_backup.unlink()
                logger.info(f"Suppression du vieux backup: {old_backup.name}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer {old_backup}: {e}")
    
    def verify_database(self) -> bool:
        """Vérifier l'intégrité de la base de données."""
        if not os.path.exists(self.db_path):
            logger.warning("Base de données introuvable (sera créée)")
            return True
        
        logger.info("Vérification de l'intégrité de la base de données...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier l'intégrité
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
            
            if result == "ok":
                logger.info("✅ Intégrité OK")
            else:
                logger.error(f"❌ Problème d'intégrité: {result}")
                conn.close()
                return False
            
            # Vérifier les tables
            cursor.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table';"
            )
            table_count = cursor.fetchone()[0]
            logger.info(f"✅ Tables trouvées: {table_count}")
            
            # Vérifier les données
            try:
                cursor.execute("SELECT count(*) FROM tracks_persistent;")
                track_count = cursor.fetchone()[0]
                logger.info(f"✅ Morceaux: {track_count}")
            except sqlite3.OperationalError:
                logger.warning("⚠️ Table tracks_persistent non trouvée")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification: {e}")
            return False
    
    def create_sync_log_table(self) -> bool:
        """Créer la table sync_log si elle n'existe pas."""
        if not os.path.exists(self.db_path):
            logger.warning("Base de données introuvable")
            return False
        
        logger.info("Vérification de la table sync_log...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            
            # Créer la table si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    operation_id TEXT UNIQUE NOT NULL,
                    missing_urlmd5 TEXT NOT NULL,
                    target_urlmd5 TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_playcount INTEGER,
                    new_playcount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            
            # Créer l'index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp
                ON sync_log(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_log_operation_id
                ON sync_log(operation_id)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Table sync_log vérifiée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """Créer les index pour la performance."""
        if not os.path.exists(self.db_path):
            logger.warning("Base de données introuvable")
            return False
        
        logger.info("Création des index...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            indexes = [
                ("idx_tracks_persistent_urlmd5",
                 "CREATE INDEX IF NOT EXISTS idx_tracks_persistent_urlmd5 "
                 "ON tracks_persistent(urlmd5)"),
                ("idx_alternativeplaycount_urlmd5",
                 "CREATE INDEX IF NOT EXISTS idx_alternativeplaycount_urlmd5 "
                 "ON alternativeplaycount(urlmd5)"),
            ]
            
            for name, sql in indexes:
                try:
                    cursor.execute(sql)
                    logger.info(f"  ✅ {name}")
                except sqlite3.OperationalError as e:
                    logger.warning(f"  ⚠️ {name}: {e}")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des index: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Exécuter les tests."""
        logger.info("Exécution des tests...")
        
        import subprocess
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                logger.info("✅ Tous les tests passent")
                return True
            else:
                logger.error("❌ Certains tests ont échoué")
                logger.error(result.stdout)
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'exécuter les tests: {e}")
            return False
    
    def deploy_full(self, run_tests: bool = True) -> bool:
        """Déployer complètement l'application."""
        logger.info("=" * 60)
        logger.info("DÉPLOIEMENT COMPLET")
        logger.info("=" * 60)
        
        steps = [
            ("Vérification de l'environnement", self.verify_environment),
            ("Sauvegarde de la base de données", self.backup_database),
            ("Vérification de l'intégrité", self.verify_database),
            ("Création de la table sync_log", self.create_sync_log_table),
            ("Création des index", self.create_indexes),
        ]
        
        if run_tests:
            steps.append(("Exécution des tests", self.run_tests))
        
        all_passed = True
        
        for step_name, step_func in steps:
            logger.info(f"\n{'─' * 60}")
            logger.info(f"▶ {step_name}")
            logger.info(f"{'─' * 60}")
            
            if not step_func():
                logger.error(f"✗ {step_name} ÉCHOUÉE")
                all_passed = False
                break
            
            logger.info(f"✓ {step_name} OK")
        
        logger.info(f"\n{'=' * 60}")
        if all_passed:
            logger.info("✅ DÉPLOIEMENT RÉUSSI")
        else:
            logger.error("❌ DÉPLOIEMENT ÉCHOUÉ")
        logger.info(f"{'=' * 60}\n")
        
        return all_passed
    
    def upgrade_from_backup(self, backup_path: str) -> bool:
        """Restaurer depuis une sauvegarde."""
        logger.info(f"Restauration depuis: {backup_path}")
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup introuvable: {backup_path}")
            return False
        
        try:
            # Créer un backup du fichier actuel
            if os.path.exists(self.db_path):
                self.backup_database()
            
            # Copier le backup
            import shutil
            shutil.copy(backup_path, self.db_path)
            logger.info(f"✅ Base de données restaurée: {self.db_path}")
            
            # Vérifier
            return self.verify_database()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la restauration: {e}")
            return False


def main():
    """Entrée principale."""
    parser = argparse.ArgumentParser(
        description="Déployer ou mettre à jour Lyrion Playcount Synchronizer"
    )
    
    parser.add_argument(
        'action',
        choices=['deploy', 'backup', 'verify', 'upgrade'],
        help="Action à effectuer"
    )
    
    parser.add_argument(
        '--config',
        help="Chemin vers le fichier de configuration"
    )
    
    parser.add_argument(
        '--db',
        help="Chemin vers la base de données",
        dest='db_path'
    )
    
    parser.add_argument(
        '--backup-dir',
        help="Répertoire des sauvegardes",
        dest='backup_dir'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help="Ignorer les tests"
    )
    
    parser.add_argument(
        '--from-backup',
        help="Restaurer depuis ce backup (pour l'action 'upgrade')"
    )
    
    args = parser.parse_args()
    
    # Initialiser le deployer
    deployer = Deployer(args.config)
    
    # Appliquer les options de ligne de commande
    if args.db_path:
        deployer.db_path = args.db_path
    if args.backup_dir:
        deployer.backup_dir = args.backup_dir
    
    # Exécuter l'action
    if args.action == 'deploy':
        success = deployer.deploy_full(run_tests=not args.skip_tests)
        
    elif args.action == 'backup':
        success = deployer.backup_database()
        
    elif args.action == 'verify':
        logger.info("Vérification...")
        success = (
            deployer.verify_environment() and
            deployer.verify_database()
        )
        
    elif args.action == 'upgrade':
        if not args.from_backup:
            logger.error("--from-backup requis pour l'action upgrade")
            success = False
        else:
            success = deployer.upgrade_from_backup(args.from_backup)
    
    # Retourner le code de sortie
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
