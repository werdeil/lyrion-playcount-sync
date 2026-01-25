#!/usr/bin/env python3
"""
Lyrion Playcount Sync - Universal Launcher

Support Docker ET mode local (Python)

Usage:
    python3 scripts/launch.py /path/to/lyrion/prefs [options]

Examples:
    # Mode Docker (par défaut)
    python3 scripts/launch.py /volume1/docker/squeezebox-lms/prefs
    
    # Mode local (Python, pas de Docker)
    python3 scripts/launch.py /var/lib/squeezeboxserver/prefs --local
    
    # Options Docker
    python3 scripts/launch.py /path/to/prefs --stop
    python3 scripts/launch.py /path/to/prefs --logs --follow
    
    # Options local
    python3 scripts/launch.py /path/to/prefs --local --logs
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════════════════════════════

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

    @staticmethod
    def info(msg: str) -> None:
        print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

    @staticmethod
    def success(msg: str) -> None:
        print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

    @staticmethod
    def warning(msg: str) -> None:
        print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

    @staticmethod
    def error(msg: str) -> None:
        print(f"{Colors.RED}❌ {msg}{Colors.NC}")

    @staticmethod
    def debug(msg: str) -> None:
        print(f"{Colors.CYAN}🔍 {msg}{Colors.NC}")


# ═══════════════════════════════════════════════════════════════════════════
# LAUNCHER BASE CLASS
# ═══════════════════════════════════════════════════════════════════════════

class LauncherBase:
    """Base class for launchers."""
    
    def __init__(self, lyrion_path: str, verbose: bool = False):
        """Initialize launcher with Lyrion path."""
        self.lyrion_path = Path(lyrion_path).resolve()
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent.resolve()
        self.config_dir = self.project_root / 'config'
        
    def validate(self) -> bool:
        """Validate all prerequisites."""
        Colors.info("Vérification de la configuration...")
        
        # Check Lyrion path exists
        if not self.lyrion_path.exists():
            Colors.error(f"Répertoire Lyrion non trouvé: {self.lyrion_path}")
            return False
        
        # Check persist.db exists
        persist_db = self.lyrion_path / 'persist.db'
        if not persist_db.exists():
            Colors.error(f"persist.db non trouvé dans: {self.lyrion_path}")
            return False
        
        # Create logs directory if missing
        logs_dir = self.project_root / 'logs'
        if not logs_dir.exists():
            Colors.warning(f"Dossier logs non trouvé, création...")
            logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle config.yaml
        config_yaml = self.project_root / 'config.yaml'
        if not config_yaml.exists():
            Colors.warning("config.yaml non trouvé, création depuis le template...")
            config_example = self.config_dir / 'config.yaml.example'
            if not config_example.exists():
                Colors.error("config.yaml.example non trouvé")
                return False
            import shutil
            shutil.copy(str(config_example), str(config_yaml))
            Colors.success(f"config.yaml créé")
        
        Colors.success("Configuration validée")
        return True
    
    def print_config(self) -> None:
        """Print current configuration."""
        print()
        Colors.info("Configuration:")
        print(f"  📂 Projet       : {self.project_root}")
        print(f"  🎵 Lyrion DB    : {self.lyrion_path / 'persist.db'}")
        print()


# ═══════════════════════════════════════════════════════════════════════════
# DOCKER LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════

class DockerLauncher(LauncherBase):
    """Docker-based launcher."""
    
    def __init__(self, lyrion_path: str, verbose: bool = False):
        super().__init__(lyrion_path, verbose)
        self.compose_file = self.config_dir / 'docker-compose.yml'
        
    def validate(self) -> bool:
        """Validate all prerequisites."""
        if not super().validate():
            return False
        
        # Check docker-compose file
        if not self.compose_file.exists():
            Colors.error(f"docker-compose.yml non trouvé: {self.compose_file}")
            return False
        
        return True
    
    def print_config(self) -> None:
        """Print current configuration."""
        print()
        Colors.info("Configuration Docker:")
        print(f"  📂 Projet       : {self.project_root}")
        print(f"  🐳 Docker       : {self.compose_file}")
        print(f"  🎵 Lyrion DB    : {self.lyrion_path / 'persist.db'}")
        print()
    
    def run_command(self, cmd: list) -> bool:
        """Run docker-compose command."""
        try:
            env = os.environ.copy()
            env['PROJECT_ROOT'] = str(self.project_root)
            env['LYRION_DATA_PATH'] = str(self.lyrion_path)
            
            if self.verbose:
                Colors.debug(f"Exécution: {' '.join(cmd)}")
            
            os.chdir(str(self.project_root))
            result = subprocess.run(cmd, env=env, cwd=str(self.project_root))
            return result.returncode == 0
            
        except Exception as e:
            Colors.error(f"Erreur lors de l'exécution: {e}")
            return False
    
    def start(self) -> None:
        """Start the container."""
        Colors.info("🚀 Démarrage du conteneur Docker...")
        cmd = [
            'docker-compose',
            '-f', str(self.compose_file),
            'up', '-d'
        ]
        if self.run_command(cmd):
            Colors.success("Conteneur démarré")
            print()
            Colors.info("🌐 Accès:")
            print(f"  🖥️  VNC Client : vnc://localhost:5900")
            print(f"  🌐 Navigateur : http://localhost:6080/vnc.html")
            print()
            Colors.warning("⏳ Patientez 10-15 secondes pour que le service soit prêt...")
        else:
            Colors.error("Erreur lors du démarrage")
            sys.exit(1)
    
    def stop(self) -> None:
        """Stop the container."""
        Colors.info("🛑 Arrêt du conteneur Docker...")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'down']
        if self.run_command(cmd):
            Colors.success("Conteneur arrêté")
        else:
            Colors.error("Erreur lors de l'arrêt")
            sys.exit(1)
    
    def restart(self) -> None:
        """Restart the container."""
        Colors.info("🔄 Redémarrage du conteneur Docker...")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'restart']
        if self.run_command(cmd):
            Colors.success("Conteneur redémarré")
        else:
            Colors.error("Erreur lors du redémarrage")
            sys.exit(1)
    
    def logs(self, follow: bool = False) -> None:
        """Show container logs."""
        Colors.info("📜 Logs du conteneur Docker...")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'logs']
        if follow:
            cmd.append('-f')
        cmd.append('lyrion-sync')
        self.run_command(cmd)
    
    def status(self) -> None:
        """Show container status."""
        Colors.info("📊 Statut du conteneur Docker:")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'ps']
        self.run_command(cmd)


# ═══════════════════════════════════════════════════════════════════════════
# LOCAL LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════

class LocalLauncher(LauncherBase):
    """Local Python launcher (no Docker)."""
    
    def validate(self) -> bool:
        """Validate all prerequisites."""
        if not super().validate():
            return False
        
        # Check .env file
        env_file = self.project_root / '.env'
        if not env_file.exists():
            Colors.warning(".env non trouvé, création...")
            env_example = self.config_dir / '.env.example'
            if not env_example.exists():
                Colors.error(".env.example non trouvé")
                return False
            import shutil
            shutil.copy(str(env_example), str(env_file))
            Colors.success(f".env créé")
        
        # Check requirements
        if not self.check_requirements():
            return False
        
        return True
    
    def check_requirements(self) -> bool:
        """Check if all Python requirements are installed."""
        Colors.info("Vérification des dépendances Python...")
        
        try:
            import ttkbootstrap
            import rapidfuzz
            import yaml
            import dotenv
            Colors.success("Toutes les dépendances sont installées")
            return True
        except ImportError as e:
            Colors.warning(f"Dépendance manquante: {e}")
            Colors.info("Installation des dépendances...")
            
            # Try to install
            requirements_file = self.project_root / 'requirements.txt'
            if requirements_file.exists():
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    Colors.success("Dépendances installées")
                    return True
                else:
                    Colors.error("Erreur lors de l'installation des dépendances")
                    return False
            else:
                Colors.error("requirements.txt non trouvé")
                return False
    
    def print_config(self) -> None:
        """Print current configuration."""
        print()
        Colors.info("Configuration Local (Python):")
        print(f"  📂 Projet       : {self.project_root}")
        print(f"  🎵 Lyrion DB    : {self.lyrion_path / 'persist.db'}")
        print(f"  🐍 Python       : {sys.executable}")
        print()
    
    def start(self) -> None:
        """Start the application locally."""
        Colors.info("🚀 Lancement de l'application Python...")
        
        try:
            # Set environment variables
            os.environ['LYRION_DATA_PATH'] = str(self.lyrion_path)
            os.environ['PROJECT_ROOT'] = str(self.project_root)
            
            # Change to project root
            os.chdir(str(self.project_root))
            
            # Add project to path
            sys.path.insert(0, str(self.project_root))
            
            if self.verbose:
                Colors.debug(f"LYRION_DATA_PATH={self.lyrion_path}")
                Colors.debug(f"PROJECT_ROOT={self.project_root}")
                Colors.debug(f"Chemin Python: {sys.path[0]}")
            
            # Import and run application
            from src.main import Application
            
            Colors.success("Application lancée")
            print()
            Colors.info("🎯 Interface GUI:")
            print(f"  L'interface graphique s'ouvrira automatiquement")
            print()
            
            # Launch app
            app = Application()
            app.run()
            
        except ImportError as e:
            Colors.error(f"Erreur d'importation: {e}")
            Colors.info("Installer les dépendances: pip install -r requirements.txt")
            sys.exit(1)
        except Exception as e:
            Colors.error(f"Erreur lors du lancement: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def logs(self, follow: bool = False) -> None:
        """Show application logs."""
        Colors.info("📜 Logs de l'application...")
        logs_dir = self.project_root / 'logs'
        if not logs_dir.exists():
            Colors.error("Dossier logs non trouvé")
            return
        
        log_files = list(logs_dir.glob('*.log'))
        if not log_files:
            Colors.warning("Aucun fichier log trouvé")
            return
        
        # Show latest log file
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        Colors.info(f"Affichage: {latest_log.name}")
        
        try:
            if follow:
                subprocess.run(['tail', '-f', str(latest_log)])
            else:
                with open(latest_log, 'r') as f:
                    print(f.read())
        except Exception as e:
            Colors.error(f"Erreur lors de la lecture des logs: {e}")
    
    def status(self) -> None:
        """Show application status."""
        Colors.info("📊 Statut:")
        print(f"  📂 Projet       : {self.project_root}")
        print(f"  🎵 Lyrion DB    : {self.lyrion_path / 'persist.db'}")
        print(f"  📜 Logs         : {self.project_root / 'logs'}")
        print(f"  ⚙️  Config       : {self.project_root / 'config.yaml'}")
        print(f"  🐍 Python       : {sys.executable}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Lyrion Playcount Sync - Universal Launcher (Docker + Local)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DOCKER MODE (défaut):
  python3 scripts/launch.py /volume1/docker/squeezebox-lms/prefs
  python3 scripts/launch.py /path/to/prefs --stop
  python3 scripts/launch.py /path/to/prefs --logs --follow

LOCAL MODE (Python, pas de Docker):
  python3 scripts/launch.py /var/lib/squeezeboxserver/prefs --local
  python3 scripts/launch.py /path/to/prefs --local --logs
        """
    )
    
    parser.add_argument(
        'lyrion_path',
        help='Chemin vers le répertoire de données Lyrion (contenant persist.db)'
    )
    
    # Mode
    mode = parser.add_argument_group('Mode')
    mode.add_argument(
        '--local',
        action='store_true',
        help='Lancer en mode local (Python, pas de Docker)'
    )
    
    # Actions
    actions = parser.add_argument_group('Actions')
    actions.add_argument(
        '--start',
        action='store_true',
        default=True,
        help='Démarrer (action par défaut)'
    )
    actions.add_argument(
        '--stop',
        action='store_true',
        help='Arrêter (Docker seulement)'
    )
    actions.add_argument(
        '--restart',
        action='store_true',
        help='Redémarrer (Docker seulement)'
    )
    actions.add_argument(
        '--logs',
        action='store_true',
        help='Afficher les logs'
    )
    actions.add_argument(
        '--status',
        action='store_true',
        help='Afficher le statut'
    )
    
    # Options
    options = parser.add_argument_group('Options')
    options.add_argument(
        '--follow',
        action='store_true',
        help='Suivre les logs en temps réel (avec --logs)'
    )
    options.add_argument(
        '--verbose',
        action='store_true',
        help='Mode verbose'
    )
    
    args = parser.parse_args()
    
    # Create launcher
    if args.local:
        launcher = LocalLauncher(args.lyrion_path, args.verbose)
        mode_name = "LOCAL (Python)"
    else:
        launcher = DockerLauncher(args.lyrion_path, args.verbose)
        mode_name = "DOCKER"
    
    print()
    Colors.info(f"Mode: {mode_name}")
    
    # Validate
    if not launcher.validate():
        sys.exit(1)
    
    launcher.print_config()
    
    # Execute action
    if args.stop:
        if args.local:
            Colors.warning("Action --stop non disponible en mode local")
            sys.exit(1)
        launcher.stop()
    elif args.restart:
        if args.local:
            Colors.warning("Action --restart non disponible en mode local")
            sys.exit(1)
        launcher.restart()
    elif args.logs:
        launcher.logs(follow=args.follow)
    elif args.status:
        launcher.status()
    else:  # start (default)
        launcher.start()
    
    print()
    Colors.success("Opération terminée")


if __name__ == '__main__':
    main()
