"""Gestion avancée de la connexion à la base de données Lyrion."""

import sqlite3
from pathlib import Path
from typing import Optional
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
    
    def _handle_wal(self) -> None:
        """
        Détecte le mode WAL et fait un checkpoint si possible.

        En mode WAL, SQLite maintient un fichier -wal séparé.  Si Lyrion
        s'est arrêté anormalement, ce fichier peut contenir des données non
        encore fusionnées dans le .db principal.  Un PRAGMA wal_checkpoint
        force la fusion avant toute lecture ou écriture.
        """
        wal_path = Path(str(self.db_path) + '-wal')
        shm_path = Path(str(self.db_path) + '-shm')

        if wal_path.exists() or shm_path.exists():
            logger.warning(
                "Fichiers WAL/SHM détectés aux côtés de la base de données. "
                "Cela peut indiquer que Lyrion est encore en cours d'exécution "
                "ou s'est arrêté anormalement."
            )

        cur = self.connection.cursor()
        try:
            cur.execute("PRAGMA journal_mode")
            mode = cur.fetchone()[0]
        finally:
            cur.close()

        if mode != 'wal':
            return

        logger.info("Mode WAL détecté — checkpoint en cours...")

        if self.readonly:
            # En lecture seule on ne peut pas écrire le checkpoint ; SQLite
            # applique quand même le WAL en lecture, donc les données sont
            # cohérentes, mais on prévient si le fichier est présent.
            if wal_path.exists():
                logger.warning(
                    "Connexion en lecture seule : le checkpoint WAL ne peut pas "
                    "être effectué. Les données lues sont cohérentes mais le "
                    "fichier -wal reste sur disque."
                )
            return

        cur = self.connection.cursor()
        try:
            cur.execute("PRAGMA wal_checkpoint(FULL)")
            row = cur.fetchone()
        finally:
            cur.close()

        # row = (busy, log_pages, checkpointed_pages)
        if row and row[0]:
            logger.warning(
                "Checkpoint WAL incomplet (busy) : un autre processus utilise "
                "peut-être encore la base de données."
            )
        elif row:
            logger.info(
                f"Checkpoint WAL terminé : {row[2]}/{row[1]} pages fusionnées."
            )

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

            # Vérifier la présence de fichiers WAL/SHM et faire un checkpoint
            self._handle_wal()

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                raise DatabaseConnectionError(
                    "Erreur : Base de données verrouillée. "
                    "Assurez-vous que Lyrion est arrêté."
                )
            raise DatabaseConnectionError(f"Erreur de connexion : {e}")
        except Exception as e:
            raise DatabaseConnectionError(f"Erreur inattendue : {e}")
    
    def export_consolidated(self, dest_path: str) -> None:
        """
        Exporte une copie consolidée de la base vers dest_path via l'API SQLite.

        Garantit que les pages WAL en attente sont fusionnées dans la copie,
        contrairement à une simple copie de fichier.  Utilisé par backup_database()
        et par l'envoi vers le serveur distant.

        Args:
            dest_path: Chemin du fichier destination (sera créé ou écrasé)

        Raises:
            DatabaseConnectionError: Si l'export échoue
        """
        try:
            dest = sqlite3.connect(dest_path)
            try:
                if self.connection:
                    self.connection.backup(dest)
                else:
                    src = sqlite3.connect(str(self.db_path))
                    try:
                        src.backup(dest)
                    finally:
                        src.close()
            finally:
                dest.close()
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Erreur export SQLite : {e}")

    def backup_database(self) -> str:
        """
        Crée une sauvegarde cohérente de la base de données.

        Utilise export_consolidated() pour garantir que les données WAL sont
        incluses, contrairement à une copie de fichier ordinaire.

        Returns:
            Chemin du fichier de sauvegarde

        Raises:
            DatabaseConnectionError: Si la sauvegarde échoue
        """
        if not self.db_path or not self.db_path.exists():
            raise DatabaseConnectionError("Base de données non accessible")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.db_path.stem}.backup_{timestamp}{self.db_path.suffix}"
            backup_path = self.backup_dir / backup_name

            self.export_consolidated(str(backup_path))

            logger.info(f"Backup créé (WAL inclus) : {backup_path}")
            return str(backup_path)

        except DatabaseConnectionError:
            raise
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
