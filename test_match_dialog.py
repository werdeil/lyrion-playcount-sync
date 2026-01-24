#!/usr/bin/env python3
"""
Test du dialogue MatchDialog.
"""

import tkinter as tk
from src.models import Track, SyncOperation
from src.ui.match_dialog import MatchDialog


def test_match_dialog():
    """Test le dialogue avec des données d'exemple."""
    
    # Créer la fenêtre principale
    root = tk.Tk()
    root.title("Test MatchDialog")
    root.geometry("800x200")
    
    # Données d'exemple
    missing_track = Track(
        urlmd5="abc123def456",
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        url="file:///music/Queen/Bohemian.mp3",
        playcount=42,
        lastplayed=1705334400,  # 15/01/2024 14:00
        rating=5,
        source="tracks_persistent"
    )
    
    # Suggestions
    suggestion1 = Track(
        urlmd5="xyz789uvw456",
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        url="file:///alternative/Queen/Bohemian.mp3",
        playcount=38,
        lastplayed=1705334400,
        rating=5,
        source="alternativeplaycount"
    )
    
    suggestion2 = Track(
        urlmd5="pqr123stu456",
        title="Bohemian Rhap...",
        artist="Queen",
        album="Greatest Hits",
        url="file:///alternative/Queen/Bohemian2.mp3",
        playcount=40,
        lastplayed=1705334400,
        rating=4,
        source="alternativeplaycount"
    )
    
    suggestion3 = Track(
        urlmd5="mno789xyz456",
        title="The Show Must Go On",
        artist="Queen",
        album="Innuendo",
        url="file:///alternative/Queen/ShowMustGo.mp3",
        playcount=5,
        lastplayed=1705334400,
        rating=3,
        source="alternativeplaycount"
    )
    
    suggested_matches = [
        (suggestion1, 95.0),
        (suggestion2, 68.0),
        (suggestion3, 45.0),
    ]
    
    def on_apply(operation: SyncOperation) -> bool:
        """Callback d'application."""
        print(f"\n✅ Opération appliquée:")
        print(f"   Action: {operation.action}")
        print(f"   Missing: {operation.missing_urlmd5}")
        print(f"   Alternative: {operation.selected_alternative_urlmd5}")
        print(f"   Nouveau playcount: {operation.new_playcount}")
        update_sql, delete_sql = operation.to_sql()
        print(f"   UPDATE: {update_sql}")
        print(f"   DELETE: {delete_sql}")
        return True
    
    def on_next():
        """Callback pour passer au suivant."""
        print("\n⏭️  Passage au suivant")
    
    # Bouton pour ouvrir le dialogue
    def open_dialog():
        dialog = MatchDialog(
            root,
            missing_track,
            suggested_matches,
            on_apply=on_apply,
            on_next=on_next
        )
        root.wait_window(dialog)
    
    button = tk.Button(
        root,
        text="Ouvrir MatchDialog",
        command=open_dialog,
        height=3,
        font=("Arial", 14, "bold")
    )
    button.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    info_label = tk.Label(
        root,
        text="Cliquez pour tester le dialogue de correspondance",
        foreground="#95a5a6"
    )
    info_label.pack(pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    test_match_dialog()
