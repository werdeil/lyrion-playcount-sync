"""
Tests pour le système de configuration et logging.
"""

import pytest
import tempfile
import logging
from pathlib import Path
import yaml

from src.utils.config import (
    Config, DatabaseConfig, MatchingConfig, SyncConfig, 
    UIConfig, LoggingConfig
)
from src.utils.logger import setup_logger, get_logger, LEVEL_NAMES


class TestLogger:
    """Tests du système de logging."""
    
    def test_setup_logger_basic(self):
        """Test création d'un logger basique."""
        logger = setup_logger('test', logging.DEBUG)
        
        assert logger is not None
        assert logger.name == 'test'
        assert logger.level == logging.DEBUG
    
    def test_logger_console_output(self, capsys):
        """Test que les logs s'affichent en console."""
        logger = setup_logger('test_console', logging.INFO)
        logger.info("Test message")
        
        captured = capsys.readouterr()
        assert "Test message" in captured.err  # Les logs vont à stderr
    
    def test_logger_file_output(self):
        """Test que les logs s'écrivent dans le fichier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            logger = setup_logger('test_file', logging.INFO, str(log_file))
            
            logger.info("Test file message")
            
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test file message" in content
    
    def test_get_logger(self):
        """Test récupération d'un logger existant."""
        setup_logger('mylogger', logging.INFO)
        logger = get_logger('mylogger')
        
        assert logger is not None
        assert logger.name == 'mylogger'
    
    def test_level_names(self):
        """Test que les constantes de niveau sont correctes."""
        assert LEVEL_NAMES['DEBUG'] == logging.DEBUG
        assert LEVEL_NAMES['INFO'] == logging.INFO
        assert LEVEL_NAMES['WARNING'] == logging.WARNING
        assert LEVEL_NAMES['ERROR'] == logging.ERROR
        assert LEVEL_NAMES['CRITICAL'] == logging.CRITICAL


class TestDatabaseConfig:
    """Tests de la configuration de base de données."""
    
    def test_default_values(self):
        """Test les valeurs par défaut."""
        config = DatabaseConfig()
        
        assert config.path == "/config/prefs/persist.db"
        assert config.auto_backup is True
        assert config.backup_on_startup is True
        assert config.backup_retention_days == 7
    
    def test_custom_values(self):
        """Test les valeurs personnalisées."""
        config = DatabaseConfig(
            path="/custom/path.db",
            auto_backup=False,
            backup_retention_days=14
        )
        
        assert config.path == "/custom/path.db"
        assert config.auto_backup is False
        assert config.backup_retention_days == 14


class TestMatchingConfig:
    """Tests de la configuration de matching."""
    
    def test_default_values(self):
        """Test les valeurs par défaut."""
        config = MatchingConfig()
        
        assert config.auto_match_threshold == 90
        assert config.suggestion_min_score == 50
        assert config.max_suggestions == 5
        assert config.weights['title'] == 70
        assert config.weights['artist'] == 20
        assert config.weights['album'] == 10
    
    def test_weights_validation_sum_100(self):
        """Test que les poids somment à 100."""
        config = MatchingConfig()
        assert config.validate() is True
        assert sum(config.weights.values()) == 100
    
    def test_weights_validation_normalization(self):
        """Test la normalisation des poids."""
        config = MatchingConfig(
            weights={'title': 70, 'artist': 10, 'album': 10}  # Total: 90
        )
        
        valid = config.validate()
        assert valid is False  # Pas valide initialement
        assert sum(config.weights.values()) == 100  # Normalisé


class TestSyncConfig:
    """Tests de la configuration de sync."""
    
    def test_default_values(self):
        """Test les valeurs par défaut."""
        config = SyncConfig()
        
        assert config.default_action == "COPY"
        assert config.delete_after_sync is True
        assert config.confirm_below_score == 70
    
    def test_validate_valid_action(self):
        """Test validation d'une action valide."""
        for action in ["COPY", "MERGE", "SKIP"]:
            config = SyncConfig(default_action=action)
            assert config.validate() is True
    
    def test_validate_invalid_action(self):
        """Test validation d'une action invalide."""
        config = SyncConfig(default_action="INVALID")
        assert config.validate() is False
        assert config.default_action == "COPY"


class TestLoggingConfig:
    """Tests de la configuration de logging."""
    
    def test_default_values(self):
        """Test les valeurs par défaut."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.file == "./logs/sync.log"
    
    def test_validate_valid_levels(self):
        """Test validation des niveaux valides."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.validate() is True
            assert config.level == level
    
    def test_validate_invalid_level(self):
        """Test validation d'un niveau invalide."""
        config = LoggingConfig(level="INVALID")
        assert config.validate() is False
        assert config.level == "INFO"


class TestConfigSingleton:
    """Tests du pattern singleton de Config."""
    
    def test_singleton_instance(self):
        """Test que Config est un singleton."""
        config1 = Config.instance()
        config2 = Config.instance()
        
        assert config1 is config2
    
    def test_default_values(self):
        """Test les valeurs par défaut."""
        config = Config.instance()
        
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.matching, MatchingConfig)
        assert isinstance(config.sync, SyncConfig)
        assert isinstance(config.ui, UIConfig)
        assert isinstance(config.logging, LoggingConfig)


class TestConfigLoading:
    """Tests du chargement de configuration."""
    
    def test_load_from_yaml_file(self):
        """Test chargement depuis fichier YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'config.yaml'
            
            yaml_data = {
                'database': {
                    'path': '/custom/persist.db',
                    'auto_backup': False
                },
                'matching': {
                    'auto_match_threshold': 85,
                    'weights': {
                        'title': 60,
                        'artist': 30,
                        'album': 10
                    }
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(yaml_data, f)
            
            config = Config()
            assert config.load_from_file(str(config_file)) is True
            
            assert config.database.path == '/custom/persist.db'
            assert config.database.auto_backup is False
            assert config.matching.auto_match_threshold == 85
    
    def test_load_nonexistent_file(self):
        """Test chargement d'un fichier inexistant."""
        config = Config()
        assert config.load_from_file('/nonexistent/config.yaml') is False
    
    def test_load_invalid_yaml(self):
        """Test chargement d'un fichier YAML invalide."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'invalid.yaml'
            config_file.write_text("invalid: yaml: content: [")
            
            config = Config()
            assert config.load_from_file(str(config_file)) is False
    
    def test_load_empty_file(self):
        """Test chargement d'un fichier vide."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'empty.yaml'
            config_file.write_text("")
            
            config = Config()
            assert config.load_from_file(str(config_file)) is True


class TestConfigSaving:
    """Tests de la sauvegarde de configuration."""
    
    def test_save_to_file(self):
        """Test sauvegarde dans un fichier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'config.yaml'
            
            config = Config()
            config.database.path = '/custom/path.db'
            config.matching.auto_match_threshold = 85
            
            assert config.save_to_file(str(config_file)) is True
            assert config_file.exists()
            
            # Vérifier le contenu
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            assert data['database']['path'] == '/custom/path.db'
            assert data['matching']['auto_match_threshold'] == 85
    
    def test_save_uses_loaded_file_path(self):
        """Test que save utilise le chemin du fichier chargé."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'config.yaml'
            config_file.write_text("database:\n  path: /original/path.db")
            
            config = Config()
            config.load_from_file(str(config_file))
            config.database.path = '/new/path.db'
            
            # Sauvegarder sans spécifier le chemin
            assert config.save_to_file() is True
            
            # Vérifier que le fichier original a été mis à jour
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            assert data['database']['path'] == '/new/path.db'


class TestConfigGetSet:
    """Tests des méthodes get/set."""
    
    def test_get_dot_notation(self):
        """Test récupération avec notation pointée."""
        config = Config()
        
        value = config.get('matching.auto_match_threshold')
        assert value == 90
        
        value = config.get('database.path')
        assert value == "/config/prefs/persist.db"
    
    def test_get_with_default(self):
        """Test get avec valeur par défaut."""
        config = Config()
        
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_set_dot_notation(self):
        """Test modification avec notation pointée."""
        config = Config()
        
        assert config.set('matching.auto_match_threshold', 85) is True
        assert config.matching.auto_match_threshold == 85
        
        assert config.set('database.path', '/new/path.db') is True
        assert config.database.path == '/new/path.db'
    
    def test_set_invalid_key(self):
        """Test set avec clé invalide."""
        config = Config()
        
        assert config.set('invalid.key.path', 'value') is False
        assert config.set('matching.nonexistent_field', 'value') is False


class TestConfigConversion:
    """Tests de conversion de configuration."""
    
    def test_to_dict(self):
        """Test conversion en dictionnaire."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'database' in config_dict
        assert 'matching' in config_dict
        assert 'sync' in config_dict
        assert 'ui' in config_dict
        assert 'logging' in config_dict
        
        assert config_dict['database']['path'] == "/config/prefs/persist.db"
        assert config_dict['matching']['auto_match_threshold'] == 90


class TestConfigIntegration:
    """Tests d'intégration du système de configuration."""
    
    def test_full_workflow(self):
        """Test le workflow complet: load -> modify -> save -> load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'test_config.yaml'
            
            # 1. Créer et configurer
            config1 = Config()
            config1.database.path = '/test/path.db'
            config1.matching.auto_match_threshold = 88
            
            # 2. Sauvegarder
            assert config1.save_to_file(str(config_file)) is True
            
            # 3. Charger dans une nouvelle instance
            config2 = Config()
            assert config2.load_from_file(str(config_file)) is True
            
            # 4. Vérifier les valeurs
            assert config2.database.path == '/test/path.db'
            assert config2.matching.auto_match_threshold == 88
    
    def test_validation_on_load(self):
        """Test que la validation s'exécute au chargement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'config.yaml'
            
            yaml_data = {
                'matching': {
                    'weights': {
                        'title': 80,
                        'artist': 10,
                        'album': 5  # Total: 95 (invalide)
                    }
                },
                'sync': {
                    'default_action': 'INVALID'  # Invalide
                },
                'logging': {
                    'level': 'UNKNOWN'  # Invalide
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(yaml_data, f)
            
            config = Config()
            assert config.load_from_file(str(config_file)) is True
            
            # Les configurations invalides doivent être corrigées
            assert sum(config.matching.weights.values()) == 100
            assert config.sync.default_action == 'COPY'
            assert config.logging.level == 'INFO'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
