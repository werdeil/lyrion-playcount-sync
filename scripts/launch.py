#!/usr/bin/env python3
"""
Lyrion Playcount Sync - Advanced Launcher

Usage:
    python3 scripts/launch.py /path/to/lyrion/prefs [options]

Examples:
    python3 scripts/launch.py /volume1/docker/squeezebox-lms/prefs
    python3 scripts/launch.py /var/lib/squeezeboxserver/prefs --start
    python3 scripts/launch.py /path/to/prefs --logs --follow
    python3 scripts/launch.py /path/to/prefs --status
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
# LAUNCHER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class DockerLauncher:
    def __init__(self, lyrion_path: str, verbose: bool = False):
        """Initialize launcher with Lyrion path."""
        self.lyrion_path = Path(lyrion_path)
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / 'config'
        self.compose_file = self.config_dir / 'docker-compose.yml'
        
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
        
        # Check docker-compose file
        if not self.compose_file.exists():
            Colors.error(f"docker-compose.yml non trouvé: {self.compose_file}")
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
                Colors.debug(f"PROJECT_ROOT={self.project_root}")
                Colors.debug(f"LYRION_DATA_PATH={self.lyrion_path}")
            
            os.chdir(str(self.project_root))
            result = subprocess.run(cmd, env=env, cwd=str(self.project_root))
            return result.returncode == 0
            
        except Exception as e:
            Colors.error(f"Erreur lors de l'exécution: {e}")
            return False
    
    def start(self) -> None:
        """Start the container."""
        Colors.info("🚀 Démarrage du conteneur...")
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
        Colors.info("🛑 Arrêt du conteneur...")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'down']
        if self.run_command(cmd):
            Colors.success("Conteneur arrêté")
        else:
            Colors.error("Erreur lors de l'arrêt")
            sys.exit(1)
    
    def restart(self) -> None:
        """Restart the container."""
        Colors.info("🔄 Redémarrage du conteneur...")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'restart']
        if self.run_command(cmd):
            Colors.success("Conteneur redémarré")
        else:
            Colors.error("Erreur lors du redémarrage")
            sys.exit(1)
    
    def logs(self, follow: bool = False) -> None:
        """Show container logs."""
        Colors.info("📜 Logs du conteneur...")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'logs']
        if follow:
            cmd.append('-f')
        cmd.append('lyrion-sync')
        self.run_command(cmd)
    
    def status(self) -> None:
        """Show container status."""
        Colors.info("📊 Statut du conteneur:")
        cmd = ['docker-compose', '-f', str(self.compose_file), 'ps']
        self.run_command(cmd)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Lyrion Playcount Sync - Advanced Docker Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/launch.py /volume1/docker/squeezebox-lms/prefs
  python3 scripts/launch.py /var/lib/squeezeboxserver/prefs --start
  python3 scripts/launch.py /path/to/prefs --logs --follow
  python3 scripts/launch.py /path/to/prefs --status
  python3 scripts/launch.py /path/to/prefs --verbose
        """
    )
    
    parser.add_argument(
        'lyrion_path',
        help='Chemin vers le répertoire de données Lyrion (contenant persist.db)'
    )
    
    # Actions
    actions = parser.add_argument_group('Actions')
    actions.add_argument(
        '--start',
        action='store_true',
        default=True,
        help='Démarrer le conteneur (action par défaut)'
    )
    actions.add_argument(
        '--stop',
        action='store_true',
        help='Arrêter le conteneur'
    )
    actions.add_argument(
        '--restart',
        action='store_true',
        help='Redémarrer le conteneur'
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
    launcher = DockerLauncher(args.lyrion_path, args.verbose)
    
    # Validate
    if not launcher.validate():
        sys.exit(1)
    
    launcher.print_config()
    
    # Execute action
    if args.stop:
        launcher.stop()
    elif args.restart:
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
