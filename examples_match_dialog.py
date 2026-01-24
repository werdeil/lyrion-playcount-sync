#!/usr/bin/env python3
"""
Exemples d'utilisation de MatchDialog.

Démonstrations pratiques du dialogue de sélection et correction du match.
"""

from src.models import Track, SyncOperation


def example_1_basic_usage():
    """Exemple 1 : Utilisation basique du dialogue."""
    print("\n" + "="*60)
    print("EXEMPLE 1 : Utilisation basique du dialogue")
    print("="*60)
    
    # Créer un morceau manquant
    missing = Track(
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
    
    print(f"\n📀 Morceau manquant:")
    print(f"   Artist : {missing.artist}")
    print(f"   Title  : {missing.title}")
    print(f"   Album  : {missing.album}")
    print(f"   Plays  : {missing.playcount}")
    
    # Créer des suggestions
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
        title="Bohemian Rhapsody",
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
    
    suggestions = [
        (suggestion1, 95.0),
        (suggestion2, 68.0),
        (suggestion3, 45.0),
    ]
    
    print(f"\n🔍 Suggestions trouvées:")
    for i, (track, score) in enumerate(suggestions, 1):
        icon = "✓" if score >= 90 else "⚠" if score >= 60 else "✗"
        print(f"   {icon} {i}. {score:.0f}% - {track.artist} - {track.title}")
        print(f"      Album: {track.album} | Plays: {track.playcount}")
    
    print(f"\n💾 Le dialogue permet :")
    print(f"   - Examiner le morceau manquant")
    print(f"   - Sélectionner parmi les suggestions")
    print(f"   - Choisir l'action (COPY/MERGE)")
    print(f"   - Valider avec prévisualisation SQL")
    
    # Exemple d'opération COPY
    operation = SyncOperation(
        missing_urlmd5=missing.urlmd5,
        selected_alternative_urlmd5=suggestion1.urlmd5,
        action="COPY",
        new_playcount=missing.playcount
    )
    
    print(f"\n⚡ Opération générée (COPY) :")
    update_sql, delete_sql = operation.to_sql()
    print(f"   UPDATE: {update_sql[:70]}...")
    print(f"   DELETE: {delete_sql[:70]}...")


def example_2_merge_operation():
    """Exemple 2 : Opération MERGE (fusion des playcounts)."""
    print("\n" + "="*60)
    print("EXEMPLE 2 : Opération MERGE (fusion des playcounts)")
    print("="*60)
    
    missing = Track(
        urlmd5="abc",
        title="Hey Jude",
        artist="The Beatles",
        album="Hey Jude",
        url="file:///music/Beatles/HeyJude.mp3",
        playcount=100,
        lastplayed=None,
        rating=5,
        source="tracks_persistent"
    )
    
    alternative = Track(
        urlmd5="xyz",
        title="Hey Jude",
        artist="The Beatles",
        album="Hey Jude (Remaster)",
        url="file:///alt/Beatles/HeyJude.mp3",
        playcount=75,
        lastplayed=None,
        rating=5,
        source="alternativeplaycount"
    )
    
    print(f"\n📀 Morceau manquant : {missing.artist} - {missing.title}")
    print(f"   Playcount : {missing.playcount}")
    
    print(f"\n🔍 Suggestion : {alternative.artist} - {alternative.title}")
    print(f"   Score : 92%")
    print(f"   Playcount : {alternative.playcount}")
    
    # Opération MERGE
    operation = SyncOperation(
        missing_urlmd5=missing.urlmd5,
        selected_alternative_urlmd5=alternative.urlmd5,
        action="MERGE",
        new_playcount=missing.playcount + alternative.playcount  # Fusion
    )
    
    print(f"\n⚡ Opération MERGE :")
    print(f"   {missing.playcount} + {alternative.playcount} = {operation.new_playcount}")
    
    update_sql, delete_sql = operation.to_sql()
    print(f"\n📝 SQL généré :")
    print(f"   {update_sql[:80]}...")
    print(f"   {delete_sql[:80]}...")


def example_3_low_score_confirmation():
    """Exemple 3 : Confirmation pour score faible."""
    print("\n" + "="*60)
    print("EXEMPLE 3 : Validation - Score faible (< 60%)")
    print("="*60)
    
    missing = Track(
        urlmd5="abc",
        title="Stairway to Heaven",
        artist="Led Zeppelin",
        album="Led Zeppelin IV",
        url="file:///music/LedZeppelin/Stairway.mp3",
        playcount=50,
        lastplayed=None,
        rating=5,
        source="tracks_persistent"
    )
    
    suggestion = Track(
        urlmd5="xyz",
        title="Stairway to Heaven (Live)",
        artist="Led Zeppelin",
        album="The Song Remains the Same",
        url="file:///alt/LedZeppelin/StairwayLive.mp3",
        playcount=10,
        lastplayed=None,
        rating=4,
        source="alternativeplaycount"
    )
    
    score = 45.0
    
    print(f"\n📀 Morceau : {missing.artist} - {missing.title}")
    print(f"\n⚠️  Suggestion faible :")
    print(f"   Score : {score:.0f}%  (< 60%)")
    print(f"   Titre : {suggestion.title}")
    print(f"   Album : {suggestion.album}")
    
    print(f"\n🔔 Le dialogue affichera une confirmation :")
    print(f"   'Le score est faible (45%). Voulez-vous continuer?'")
    print(f"   [Oui] [Non]")
    
    print(f"\n✅ Si utilisateur accepte :")
    operation = SyncOperation(
        missing_urlmd5=missing.urlmd5,
        selected_alternative_urlmd5=suggestion.urlmd5,
        action="COPY",
        new_playcount=missing.playcount
    )
    print(f"   Opération appliquée malgré le faible score")
    print(f"   Operation ID : {operation.operation_id}")


def example_4_batch_mode():
    """Exemple 4 : Mode batch (plusieurs morceaux)."""
    print("\n" + "="*60)
    print("EXEMPLE 4 : Mode batch - traiter plusieurs morceaux")
    print("="*60)
    
    tracks_to_process = [
        Track(urlmd5=f"abc{i}", title=f"Song {i}", artist="Artist", 
              album="Album", url=f"/song{i}", playcount=50+i*10, 
              lastplayed=None, rating=5, source="tracks_persistent")
        for i in range(1, 4)
    ]
    
    print(f"\n📀 Morceaux à traiter :")
    for i, track in enumerate(tracks_to_process, 1):
        print(f"   {i}. {track.title} ({track.playcount} plays)")
    
    print(f"\n🔄 Flux batch :")
    print(f"   1. Ouvrir dialogue pour morceau 1")
    print(f"   2. Utilisateur clique 'Ignorer'")
    print(f"   3. Callback on_next() appelé")
    print(f"   4. Passer au morceau 2")
    print(f"   5. Répéter jusqu'au dernier")
    
    print(f"\n💡 Ou :")
    print(f"   1. Ouvrir dialogue pour morceau 1")
    print(f"   2. Utilisateur clique 'Appliquer'")
    print(f"   3. Opération exécutée")
    print(f"   4. Callback on_next() appelé")
    print(f"   5. Passer au morceau 2")


def example_5_custom_playcount():
    """Exemple 5 : Personnalisation du playcount."""
    print("\n" + "="*60)
    print("EXEMPLE 5 : Personnalisation manuelle du playcount")
    print("="*60)
    
    missing = Track(
        urlmd5="abc",
        title="Imagine",
        artist="John Lennon",
        album="Imagine",
        url="file:///music/Lennon/Imagine.mp3",
        playcount=150,
        lastplayed=None,
        rating=5,
        source="tracks_persistent"
    )
    
    suggestion = Track(
        urlmd5="xyz",
        title="Imagine",
        artist="John Lennon",
        album="Imagine (Remaster)",
        url="file:///alt/Lennon/Imagine.mp3",
        playcount=120,
        lastplayed=None,
        rating=5,
        source="alternativeplaycount"
    )
    
    print(f"\n📀 Morceau manquant :")
    print(f"   {missing.artist} - {missing.title}")
    print(f"   Playcount : {missing.playcount}")
    
    print(f"\n🔍 Suggestion (98% match) :")
    print(f"   {suggestion.artist} - {suggestion.title}")
    print(f"   Playcount : {suggestion.playcount}")
    
    print(f"\n⚡ Utilisateur choisit ACTION = COPY")
    print(f"   Et change playcount manuellement : {missing.playcount} → 160")
    
    print(f"\n💾 Spinbox permet :")
    print(f"   - Min : 0")
    print(f"   - Max : 999999")
    print(f"   - Valeur : 160")
    
    operation = SyncOperation(
        missing_urlmd5=missing.urlmd5,
        selected_alternative_urlmd5=suggestion.urlmd5,
        action="COPY",
        new_playcount=160  # Valeur personnalisée
    )
    
    print(f"\n⚡ Opération avec valeur personnalisée :")
    update_sql, delete_sql = operation.to_sql()
    print(f"   {update_sql}")


def example_6_sql_generation():
    """Exemple 6 : Génération SQL dynamique."""
    print("\n" + "="*60)
    print("EXEMPLE 6 : Génération SQL dynamique selon action")
    print("="*60)
    
    missing = Track(
        urlmd5="m1",
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        url="file:///music/Queen/Bohemian.mp3",
        playcount=42,
        lastplayed=None,
        rating=5,
        source="tracks_persistent"
    )
    
    alternative = Track(
        urlmd5="a1",
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        url="file:///alt/Queen/Bohemian.mp3",
        playcount=38,
        lastplayed=None,
        rating=5,
        source="alternativeplaycount"
    )
    
    print(f"\n📝 ACTION = COPY (42) :")
    op_copy = SyncOperation(
        missing_urlmd5=missing.urlmd5,
        selected_alternative_urlmd5=alternative.urlmd5,
        action="COPY",
        new_playcount=42
    )
    update, delete = op_copy.to_sql()
    print(f"   UPDATE: {update}")
    print(f"   DELETE: {delete}")
    
    print(f"\n📝 ACTION = MERGE (42 + 38 = 80) :")
    op_merge = SyncOperation(
        missing_urlmd5=missing.urlmd5,
        selected_alternative_urlmd5=alternative.urlmd5,
        action="MERGE",
        new_playcount=80
    )
    update, delete = op_merge.to_sql()
    print(f"   UPDATE: {update}")
    print(f"   DELETE: {delete}")
    
    print(f"\n💾 La prévisualisation SQL est DYNAMIQUE :")
    print(f"   - Change avec chaque sélection")
    print(f"   - Change avec chaque modification d'action")
    print(f"   - Change avec chaque édition de playcount")


def example_7_callbacks():
    """Exemple 7 : Callbacks et gestion des résultats."""
    print("\n" + "="*60)
    print("EXEMPLE 7 : Callbacks et gestion des résultats")
    print("="*60)
    
    print(f"\n📌 Callback on_apply(operation: SyncOperation) -> bool :")
    print("""
def handle_apply(operation: SyncOperation) -> bool:
    try:
        # 1. Backup
        backup_db()
        
        # 2. Générer SQL
        update_sql, delete_sql = operation.to_sql()
        
        # 3. Exécuter
        cursor.execute(update_sql)
        if operation.action != "MERGE":
            cursor.execute(delete_sql)
        db.commit()
        
        # 4. Log
        print(f"Sync OK: {operation.operation_id}")
        
        # 5. Retourner True = succès
        return True
        
    except Exception as e:
        # Log erreur
        print(f"Sync failed: {e}")
        # Retourner False = échec
        return False

# Si True  → Dialogue se ferme
# Si False → Dialogue reste ouvert, message d'erreur affiché
""")
    
    print(f"\n📌 Callback on_next() -> None :")
    print("""
def handle_next():
    # 1. Passer au morceau suivant
    next_track = get_next_track()
    
    # 2. Rouvrir le dialogue
    suggestions = matcher.find_best_matches(next_track)
    show_match_dialog(
        root,
        next_track,
        suggestions,
        on_apply=handle_apply,
        on_next=handle_next
    )

# Appelé quand utilisateur clique "Ignorer"
""")


def example_8_complete_workflow():
    """Exemple 8 : Workflow complet intégré."""
    print("\n" + "="*60)
    print("EXEMPLE 8 : Workflow complet (SyncDetector → Matcher → Dialog)")
    print("="*60)
    
    print(f"""
# 1. DETECT missing tracks
detector = SyncDetector("path/to/db")
missing_tracks = detector.find_missing_in_alternative()
print(f"Found {{len(missing_tracks)}} missing tracks")

# 2. MATCH suggestions
matcher = TrackMatcher()
for missing in missing_tracks:
    suggestions = matcher.find_best_matches(missing)
    
    # 3. DISPLAY dialog
    def apply_operation(operation):
        db.execute_sync(operation)
        return True
    
    def go_to_next():
        # Traiter le morceau suivant
        pass
    
    show_match_dialog(
        main_window,
        missing,
        suggestions,
        on_apply=apply_operation,
        on_next=go_to_next
    )
    
    # 4. WAIT for user decision
    # Dialog blocks until closed

# 5. COMPLETE
print("Workflow terminé")
""")


if __name__ == "__main__":
    print("\n🎵 EXEMPLES - MatchDialog\n")
    
    example_1_basic_usage()
    example_2_merge_operation()
    example_3_low_score_confirmation()
    example_4_batch_mode()
    example_5_custom_playcount()
    example_6_sql_generation()
    example_7_callbacks()
    example_8_complete_workflow()
    
    print("\n" + "="*60)
    print("✅ Tous les exemples exécutés avec succès")
    print("="*60)
    print("\n💡 Pour tester l'interface graphique :")
    print("   python3 test_match_dialog.py\n")
