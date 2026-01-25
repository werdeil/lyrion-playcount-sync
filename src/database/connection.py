"""Gestion avancée de la connexion à la base de données Lyrion."""

import sqlite3
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from contextlib import contextmanager
from datetime import datetime

from src.utils import setup_logger

logger = setup_logger(__name__)


class DatabaseConnectionError(Exception):
    """Exception personnalisée pour les erreurs de base de données."""
    pass


class DatabaseManager:
    """Gestionnaire complet de connexion SQLite pour Lyrion."""
    
    # Tables requises dans la BD Lyrion
    # Note: Les noms de colonnes sont case-insensitive (Lyrion utilise parfois playCount vs playcount)
    REQUIRED_TABLES = {
        'tracks_persistent': ['urlmd5', 'playcount'],  # Colonnes minimales requises
        'alternativeplaycount': ['urlmd5', 'playcount'],  # Colonne minimal (lastplayed et source sont optionnels)
    }
    
    # Tables optionnelles qui peuvent exister
    OPTIONAL_TABLES = {
        'tracks': ['url', 'urlmd5']
    }
    
    # Chemins typiques par OS
    DEFAULT_PATHS = [
        # Linux/Docker
        Path('/config/prefs/persist.db'),
        Path('/var/lib/squeezeboxserver/cache/persist.db'),
        Path('/var/lib/squeezeboxserver/prefs/persist.db'),
        # macOS
        Path('~/Library/Application Support/Squeezebox/prefs/persist.db').expanduser(),
        Path('~/Library/Application Support/Logitech/Squeezebox/prefs/persist.db').expanduser(),
        # Windows
        Path('C:\\ProgramData\\Squeezebox\\cache\\persist.db'),
        Path('C:\\ProgramData\\Squeezebox\\prefs\\persist.db'),
    ]
    
    def __init__(self, db_path: Optional[str] = None, auto_detect: bool = True):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path: Chemin vers la base de données (optionnel)
            auto_detect: Déterminer automatiquement le chemin si non fourni
            
        Raises:
            DatabaseConnectionError: Si le chemin n'est pas trouvé
        """
        self.db_path: Optional[Path] = None
        self.connection: Optional[sqlite3.Connection] = None
        self.readonly: bool = False
        self.backup_dir: Path = Path('backups')
        
        # Créer le répertoire des backups
        self.backup_dir.mkdir(exist_ok=True)
        
        if db_path:
            self.db_path = Path(db_path).expanduser().resolve()
        elif auto_detect:
            self.db_path = self._auto_detect_path()
        
        if not self.db_path or not self.db_path.exists():
            raise DatabaseConnectionError(
                f"Base de données Lyrion non trouvée. "
                f"Chemin : {self.db_path or 'non détecté'}"
            )
        
        logger.info(f"DatabaseManager initialisé : {self.db_path}")
    
    @staticmethod
    def _auto_detect_path() -> Optional[Path]:
        """
        Détecte automatiquement le chemin de la base de données Lyrion.
        
        Returns:
            Chemin vers persist.db ou None
        """
        for path in DatabaseManager.DEFAULT_PATHS:
            if path.exists():
                logger.info(f"Base de données Lyrion détectée : {path}")
                return path
        
        logger.warning("Impossible de détecter la base de données Lyrion")
        return None
    
    def connect(self, readonly: bool = False) -> None:
        """
        Établit la connexion à la base de données.
        
        Args:
            readonly: Mode lecture seule
            
        Raises:
            DatabaseConnectionError: Si la connexion échoue
        """
        if self.connection:
            logger.warning("Connexion déjà établie")
            return
        
        try:
            # Mode lecture/écriture ou lecture seule
            if readonly:
                uri = f"file:{self.db_path}?mode=ro"
                self.connection = sqlite3.connect(uri, uri=True)
                logger.info(f"Connexion établie (lecture seule) : {self.db_path}")
            else:
                self.connection = sqlite3.connect(str(self.db_path), timeout=10)
                logger.info(f"Connexion établie (lecture/écriture) : {self.db_path}")
            
            # Configurer la fabrique de lignes
            self.connection.row_factory = sqlite3.Row
            self.readonly = readonly
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                raise DatabaseConnectionError(
                    "Erreur : Base de données verrouillée. "
                    "Assurez-vous que Lyrion est arrêté."
                )
            raise DatabaseConnectionError(f"Erreur de connexion : {e}")
        except Exception as e:
            raise DatabaseConnectionError(f"Erreur inattendue : {e}")
    
    def backup_database(self) -> str:
        """
        Crée une sauvegarde de la base de données.
        
        Returns:
            Chemin du fichier de sauvegarde
            
        Raises:
            DatabaseConnectionError: Si la sauvegarde échoue
        """
        if not self.db_path or not self.db_path.exists():
            raise DatabaseConnectionError("Base de données non accessible")
        
        try:
            # Créer le nom du backup avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.db_path.stem}.backup_{timestamp}{self.db_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Copier le fichier
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Backup créé : {backup_path}")
            return str(backup_path)
            
        except IOError as e:
            raise DatabaseConnectionError(f"Erreur lors du backup : {e}")
        except Exception as e:
            raise DatabaseConnectionError(f"Erreur inattendue : {e}")
    
    def verify_schema(self) -> bool:
        """
        Vérifie que le schéma est valide pour Lyrion.
        
        Returns:
            True si le schéma est valide
            
        Raises:
            DatabaseConnectionError: Si le schéma est invalide
        """
        if not self.connection:
            raise DatabaseConnectionError("Pas de connexion établie")
        
        try:
            cursor = self.connection.cursor()
            
            # Vérifier chaque table requise
            for table_name, required_columns in self.REQUIRED_TABLES.items():
                # Vérifier l'existence de la table
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                
                if not cursor.fetchone():
                    raise DatabaseConnectionError(
                        f"Table manquante : {table_name}"
                    )
                
                # Vérifier les colonnes (insensible à la casse)
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row[1].lower() for row in cursor.fetchall()}
                
                for column in required_columns:
                    if column.lower() not in existing_columns:
                        raise DatabaseConnectionError(
                            f"Colonne manquante : {table_name}.{column}"
                        )
            
            logger.info("✓ Schéma Lyrion validé")
            return True
            
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Erreur de vérification : {e}")
    
    def get_table_stats(self) -> Dict[str, Dict[str, any]]:
        """
        Récupère les statistiques des tables Lyrion.
        
        Returns:
            Dictionnaire avec stats par table
            
        Raises:
            DatabaseConnectionError: Si l'opération échoue
        """
        if not self.connection:
            raise DatabaseConnectionError("Pas de connexion établie")
        
        try:
            cursor = self.connection.cursor()
            stats = {}
            
            for table_name in self.REQUIRED_TABLES.keys():
                # Nombre de lignes
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = cursor.fetchone()['count']
                
                # Taille en bytes
                cursor.execute(f"SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size() WHERE 1=1")
                db_size = cursor.fetchone()['size'] if cursor.fetchone() else 0
                
                stats[table_name] = {
                    'rows': row_count,
                    'db_size_bytes': db_size
                }
                
                # Stat spécifique pour tracks_persistent
                if table_name == 'tracks_persistent':
                    cursor.execute(
                        f"SELECT COUNT(*) as count FROM {table_name} WHERE playcount > 0"
                    )
                    with_plays = cursor.fetchone()['count']
                    stats[table_name]['with_plays'] = with_plays
                
                # Stat spécifique pour alternativeplaycount
                if table_name == 'alternativeplaycount':
                    cursor.execute(
                        f"SELECT DISTINCT source FROM {table_name}"
                    )
                    sources = [row[0] for row in cursor.fetchall()]
                    stats[table_name]['sources'] = sources
            
            logger.debug(f"Stats récupérées : {stats}")
            return stats
            
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Erreur lors de la lecture des stats : {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Récupère la connexion SQLite.
        
        Returns:
            Connexion SQLite
            
        Raises:
            DatabaseConnectionError: Si pas de connexion
        """
        if not self.connection:
            raise DatabaseConnectionError("Pas de connexion établie. Appelez connect() d'abord.")
        return self.connection
    
    @contextmanager
    def cursor(self, commit: bool = True):
        """
        Context manager pour obtenir un curseur.
        
        Args:
            commit: Commiter les changements à la sortie
            
        Yields:
            Curseur SQLite
            
        Raises:
            DatabaseConnectionError: Si pas de connexion
        """
        if not self.connection:
            raise DatabaseConnectionError("Pas de connexion établie")
        
        cursor = self.connection.cursor()
        try:
            yield cursor
            if commit and not self.readonly:
                self.connection.commit()
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Erreur lors de la requête : {e}")
            raise DatabaseConnectionError(f"Erreur SQL : {e}")
        finally:
            cursor.close()
    
    @contextmanager
    def transaction(self):
        """
        Context manager pour une transaction complète.
        
        Yields:
            Curseur SQLite
            
        Raises:
            DatabaseConnectionError: Si pas de connexion
        """
        if not self.connection:
            raise DatabaseConnectionError("Pas de connexion établie")
        
        if self.readonly:
            raise DatabaseConnectionError("Impossible de faire une transaction en lecture seule")
        
        cursor = self.connection.cursor()
        try:
            self.connection.execute('BEGIN TRANSACTION')
            yield cursor
            self.connection.commit()
            logger.debug("Transaction commitée")
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Erreur de transaction : {e}")
            raise DatabaseConnectionError(f"Erreur de transaction : {e}")
        finally:
            cursor.close()
    
    def close(self) -> None:
        """Ferme la connexion à la base de données."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Connexion fermée")
    
    def __enter__(self):
        """Support du context manager."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager."""
        self.close()
        return False
    
    def __repr__(self) -> str:
        """Représentation textuelle."""
        status = "connectée" if self.connection else "fermée"
        mode = "lecture seule" if self.readonly else "lecture/écriture"
        return f"DatabaseManager({self.db_path}, {status}, {mode})"
