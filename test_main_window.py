#!/usr/bin/env python3
"""
Test de la fenêtre principale.

Pour tester l'interface:
python3 test_main_window.py
"""

from src.ui.main_window import MainWindow


def main():
    """Tester la fenêtre principale."""
    print("Démarrage de l'interface Lyrion Playcount Sync...")
    print("Utilisez la fenêtre pour tester les différentes fonctionnalités.")
    print("Fermez la fenêtre pour quitter.\n")
    
    app = MainWindow(
        db_path="/config/prefs/persist.db",
        on_sync_callback=lambda: print("Sync callback called!")
    )
    
    app.mainloop()


if __name__ == "__main__":
    main()
