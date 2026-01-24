"""
Opérations de modification de la base de données.

Gère les synchronisations de playcounts avec transactions SQLite,
logging, et gestion d'erreurs robuste.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Callable
from src.models import SyncOperation


# Logger
logger = logging.getLogger(__name__)


class SyncOperations:
    """Gère les opérations de synchronisation sur la base de données."""
    
    def __init__(self, db_path: str | Path):
        """
        Initialiser le gestionnaire d'opérations.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), timeout=30)
        self.conn.row_factory = sqlite3.Row
        
        # Activer les contraintes FK
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Créer la table de log
        self._create_sync_log_table()
        
        logger.info(f"SyncOperations initialized with {self.db_path}")
    
    def __del__(self):
        """Fermer la connexion à la base de données."""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def _create_sync_log_table(self) -> None:
        """Créer la table de log de synchronisation si elle n'existe pas."""
        try:
            self.conn.execute("""
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
            self.conn.commit()
            logger.debug("sync_log table ready")
        except Exception as e:
            logger.error(f"Error creating sync_log table: {e}")
    
    def _get_alternative_value(self, urlmd5: str) -> Optional[Dict]:
        """
        Récupérer la valeur actuelle dans alternativeplaycount.
        
        Args:
            urlmd5: MD5 de l'URL
            
        Returns:
            Dict avec 'playcount' et 'lastplayed', ou None si absent
        """
        try:
            cursor = self.conn.execute(
                "SELECT playcount, lastplayed FROM alternativeplaycount WHERE urlmd5 = ?",
                (urlmd5,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'playcount': row['playcount'],
                    'lastplayed': row['lastplayed']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting alternative value for {urlmd5}: {e}")
            return None
    
    def _get_persistent_value(self, urlmd5: str) -> Optional[Dict]:
        """
        Récupérer la valeur actuelle dans tracks_persistent.
        
        Args:
            urlmd5: MD5 de l'URL
            
        Returns:
            Dict avec métadonnées, ou None si absent
        """
        try:
            cursor = self.conn.execute(
                "SELECT * FROM tracks_persistent WHERE urlmd5 = ? LIMIT 1",
                (urlmd5,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting persistent value for {urlmd5}: {e}")
            return None
    
    def update_alternative_playcount(
        self,
        urlmd5: str,
        new_playcount: int,
        new_lastplayed: Optional[int] = None,
        auto_commit: bool = True
    ) -> int:
        """
        Mettre à jour le playcount dans alternativeplaycount.
        
        Effectue un UPDATE si la ligne existe, INSERT sinon.
        
        Args:
            urlmd5: MD5 de l'URL
            new_playcount: Nouveau playcount
            new_lastplayed: Nouveau timestamp (optionnel)
            auto_commit: Valider automatiquement la transaction
            
        Returns:
            Nombre de lignes affectées
            
        Raises:
            Exception: Si erreur de base de données
        """
        try:
            # Vérifier si la ligne existe
            cursor = self.conn.execute(
                "SELECT id FROM alternativeplaycount WHERE urlmd5 = ? LIMIT 1",
                (urlmd5,)
            )
            exists = cursor.fetchone() is not None
            
            if exists:
                # UPDATE
                if new_lastplayed:
                    self.conn.execute(
                        """
                        UPDATE alternativeplaycount
                        SET playcount = ?,
                            lastplayed = ?
                        WHERE urlmd5 = ?
                        """,
                        (new_playcount, new_lastplayed, urlmd5)
                    )
                else:
                    self.conn.execute(
                        """
                        UPDATE alternativeplaycount
                        SET playcount = ?,
                            lastplayed = COALESCE(?, lastplayed)
                        WHERE urlmd5 = ?
                        """,
                        (new_playcount, new_lastplayed, urlmd5)
                    )
                logger.info(f"Updated alternativeplaycount for {urlmd5}: {new_playcount}")
            else:
                # INSERT
                self.conn.execute(
                    """
                    INSERT INTO alternativeplaycount
                    (urlmd5, playcount, lastplayed, source)
                    VALUES (?, ?, ?, 'manual_sync')
                    """,
                    (urlmd5, new_playcount, new_lastplayed)
                )
                logger.info(f"Inserted alternativeplaycount for {urlmd5}: {new_playcount}")
            
            if auto_commit:
                self.conn.commit()
            
            return 1
            
        except Exception as e:
            logger.error(f"Error updating playcount for {urlmd5}: {e}")
            raise
    
    def delete_from_tracks_persistent(
        self,
        urlmd5: str,
        auto_commit: bool = True
    ) -> int:
        """
        Supprimer un morceau de tracks_persistent.
        
        Log la suppression avant exécution pour audit.
        
        Args:
            urlmd5: MD5 de l'URL
            auto_commit: Valider automatiquement la transaction
            
        Returns:
            Nombre de lignes supprimées
            
        Raises:
            Exception: Si erreur de base de données
        """
        try:
            # Récupérer les infos avant suppression (audit)
            track_info = self._get_persistent_value(urlmd5)
            if track_info:
                logger.info(
                    f"Deleting track from persistent: {urlmd5} "
                    f"({track_info.get('artist')} - {track_info.get('title')})"
                )
            
            # Effectuer la suppression
            self.conn.execute(
                "DELETE FROM tracks_persistent WHERE urlmd5 = ?",
                (urlmd5,)
            )
            
            if auto_commit:
                self.conn.commit()
            
            logger.info(f"Deleted track from tracks_persistent")
            
            return 1
            
        except Exception as e:
            logger.error(f"Error deleting from tracks_persistent for {urlmd5}: {e}")
            raise
    
    def _log_sync_operation(
        self,
        operation: SyncOperation,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Logger une opération de synchronisation.
        
        Args:
            operation: L'opération effectuée
            status: 'success' ou 'failed'
            error_message: Message d'erreur si applicable
        """
        try:
            old_value = self._get_alternative_value(
                operation.selected_alternative_urlmd5
            )
            old_playcount = old_value['playcount'] if old_value else None
            
            self.conn.execute(
                """
                INSERT INTO sync_log
                (timestamp, operation_id, missing_urlmd5, target_urlmd5,
                 action, old_playcount, new_playcount, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(datetime.now().timestamp()),
                    str(operation.operation_id),
                    operation.missing_urlmd5,
                    operation.selected_alternative_urlmd5,
                    operation.action,
                    old_playcount,
                    operation.new_playcount,
                    status,
                    error_message
                )
            )
            self.conn.commit()
            logger.debug(f"Logged sync operation {operation.operation_id}")
            
        except Exception as e:
            logger.error(f"Error logging sync operation: {e}")
    
    def sync_track(self, operation: SyncOperation) -> bool:
        """
        Synchroniser un morceau (opération principale).
        
        Encapsule :
        1. Backup de l'ancienne valeur
        2. UPDATE alternativeplaycount (COPY ou MERGE)
        3. DELETE tracks_persistent
        
        Utilise une transaction SQLite : commit si succès, rollback si erreur.
        
        Args:
            operation: L'opération de synchronisation
            
        Returns:
            True si succès, False si erreur
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")
            logger.debug(f"Started transaction for {operation.operation_id}")
            
            # 1. Récupérer l'ancienne valeur (backup)
            old_value = self._get_alternative_value(
                operation.selected_alternative_urlmd5
            )
            
            # 2. Mettre à jour alternativeplaycount selon l'action
            if operation.action == 'COPY':
                self.update_alternative_playcount(
                    operation.selected_alternative_urlmd5,
                    operation.new_playcount
                )
                logger.info(
                    f"COPY: {operation.selected_alternative_urlmd5} → "
                    f"{operation.new_playcount}"
                )
            
            elif operation.action == 'MERGE':
                if old_value:
                    merged_playcount = old_value['playcount'] + operation.new_playcount
                    self.update_alternative_playcount(
                        operation.selected_alternative_urlmd5,
                        merged_playcount
                    )
                    logger.info(
                        f"MERGE: {operation.selected_alternative_urlmd5} → "
                        f"{old_value['playcount']} + {operation.new_playcount} = "
                        f"{merged_playcount}"
                    )
                else:
                    self.update_alternative_playcount(
                        operation.selected_alternative_urlmd5,
                        operation.new_playcount
                    )
                    logger.warning(
                        f"MERGE target not found, treating as COPY: "
                        f"{operation.selected_alternative_urlmd5}"
                    )
            
            # 3. Supprimer de tracks_persistent
            self.delete_from_tracks_persistent(operation.missing_urlmd5)
            
            # 4. Valider la transaction
            self.conn.commit()
            logger.info(f"✅ Sync successful: {operation.operation_id}")
            
            # 5. Logger l'opération
            self._log_sync_operation(operation, 'success')
            
            return True
            
        except Exception as e:
            # Rollback en cas d'erreur
            self.conn.rollback()
            logger.error(f"❌ Sync failed: {operation.operation_id} - {e}")
            
            # Logger l'erreur
            self._log_sync_operation(operation, 'failed', str(e))
            
            return False
    
    def bulk_sync(
        self,
        operations: List[SyncOperation],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        stop_on_failure: bool = False
    ) -> Dict:
        """
        Traiter une liste d'opérations de synchronisation.
        
        Args:
            operations: Liste des opérations SyncOperation
            progress_callback: Callback (index, total) pour barre de progression
            stop_on_failure: Arrêter au premier échec (défaut: continuer)
            
        Returns:
            Dict avec clés :
                - 'success': nombre d'opérations réussies
                - 'failed': nombre d'opérations échouées
                - 'errors': liste des erreurs détaillées
                - 'total': total des opérations
        """
        result = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'total': len(operations)
        }
        
        logger.info(f"Starting bulk_sync with {len(operations)} operations")
        
        for i, operation in enumerate(operations):
            # Callback de progression
            if progress_callback:
                progress_callback(i + 1, len(operations))
            
            # Exécuter l'opération
            try:
                success = self.sync_track(operation)
                
                if success:
                    result['success'] += 1
                else:
                    result['failed'] += 1
                    result['errors'].append({
                        'operation_id': str(operation.operation_id),
                        'message': 'Unknown error during sync'
                    })
                    
                    if stop_on_failure:
                        logger.warning("Stopping bulk_sync due to failure")
                        break
                        
            except Exception as e:
                result['failed'] += 1
                result['errors'].append({
                    'operation_id': str(operation.operation_id),
                    'message': str(e)
                })
                logger.error(f"Exception during bulk_sync: {e}")
                
                if stop_on_failure:
                    logger.warning("Stopping bulk_sync due to exception")
                    break
        
        logger.info(
            f"Bulk sync completed: {result['success']} success, "
            f"{result['failed']} failed"
        )
        
        return result
    
    def get_sync_history(self, limit: int = 50) -> List[Dict]:
        """
        Récupérer l'historique des synchronisations.
        
        Args:
            limit: Nombre maximum d'entrées (défaut: 50)
            
        Returns:
            Liste des opérations loggées (plus récentes d'abord)
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT id, timestamp, operation_id, missing_urlmd5, target_urlmd5,
                       action, old_playcount, new_playcount, status, error_message
                FROM sync_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                entry = dict(row)
                # Convertir timestamp en datetime
                entry['timestamp_iso'] = datetime.fromtimestamp(
                    entry['timestamp']
                ).isoformat()
                history.append(entry)
            
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving sync history: {e}")
            return []
    
    def get_sync_stats(self, hours: int = 24) -> Dict:
        """
        Obtenir les statistiques de synchronisation.
        
        Args:
            hours: Nombre d'heures à considérer (défaut: 24)
            
        Returns:
            Dict avec statistiques
        """
        try:
            cutoff_timestamp = int(
                datetime.now().timestamp() - (hours * 3600)
            )
            
            cursor = self.conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    action,
                    COUNT(DISTINCT DATE(timestamp, 'unixepoch')) as days
                FROM sync_log
                WHERE timestamp >= ?
                GROUP BY action
                """,
                (cutoff_timestamp,)
            )
            
            rows = cursor.fetchall()
            stats = {
                'period_hours': hours,
                'actions': {}
            }
            
            for row in rows:
                action = row['action']
                stats['actions'][action] = {
                    'total': row['total'],
                    'success': row['success'],
                    'failed': row['failed'],
                    'success_rate': (
                        f"{100 * row['success'] / row['total']:.1f}%"
                        if row['total'] > 0 else "N/A"
                    )
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving sync stats: {e}")
            return {}
    
    def clear_sync_log(self, older_than_days: int = 30) -> int:
        """
        Nettoyer l'historique de synchronisation.
        
        Args:
            older_than_days: Supprimer les entrées plus anciennes que (défaut: 30)
            
        Returns:
            Nombre de lignes supprimées
        """
        try:
            cutoff_timestamp = int(
                datetime.now().timestamp() - (older_than_days * 86400)
            )
            
            cursor = self.conn.execute(
                "DELETE FROM sync_log WHERE timestamp < ?",
                (cutoff_timestamp,)
            )
            
            deleted = self.conn.total_changes
            self.conn.commit()
            
            logger.info(f"Cleared {deleted} old sync log entries")
            return deleted
            
        except Exception as e:
            logger.error(f"Error clearing sync log: {e}")
            return 0
    
    def backup_database(self, backup_path: str | Path) -> bool:
        """
        Créer une sauvegarde de la base de données.
        
        Args:
            backup_path: Chemin de la sauvegarde
            
        Returns:
            True si succès, False si erreur
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Utiliser le module sqlite3 pour backup
            backup_conn = sqlite3.connect(str(backup_path))
            self.conn.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False


def create_sync_operations(db_path: str | Path) -> SyncOperations:
    """
    Créer une instance de SyncOperations.
    
    Args:
        db_path: Chemin vers la base de données
        
    Returns:
        Instance SyncOperations
    """
    return SyncOperations(db_path)
