#!/usr/bin/env python3
"""
Exemples pratiques d'utilisation des modèles.
"""

from datetime import datetime, timezone
from src.models import Track, MatchSuggestion, SyncOperation


def example_1_track_creation():
    """Exemple 1: Créer et utiliser des Track."""
    print("\n" + "=" * 60)
    print("📝 Exemple 1: Création et utilisation de Track")
    print("=" * 60)
    
    # Créer un morceau persistent
    persistent = Track(
        urlmd5="persistent_md5_001",
        title="Imagine",
        artist="John Lennon",
        album="Imagine",
        url="http://music.example.com/imagine",
        playcount=42,
        lastplayed=1705795200,  # 21/01/2024
        rating=5,
        source="tracks_persistent"
    )
    
    print(f"\n📀 Morceau persistent:")
    print(f"   Display: {persistent.display_name()}")
    print(f"   Plays: {persistent.playcount}")
    print(f"   Last played: {persistent.lastplayed_formatted()}")
    print(f"   Rating: {'⭐' * persistent.rating if persistent.rating else 'N/A'}")
    print(f"   Source: {persistent.source}")
    
    # Créer un morceau alternative
    alternative = Track(
        urlmd5="alternative_md5_001",
        title="Imagine",
        artist="John Lennon",
        album="Imagine",
        url="http://music.example.com/imagine_alt",
        playcount=150,
        lastplayed=1705881600,  # 22/01/2024
        rating=None,
        source="alternativeplaycount"
    )
    
    print(f"\n🎵 Morceau alternative:")
    print(f"   Display: {alternative.display_name()}")
    print(f"   Plays: {alternative.playcount}")
    print(f"   Last played: {alternative.lastplayed_formatted()}")
    print(f"   Rating: N/A (non-évalué)")
    print(f"   Source: {alternative.source}")
    
    return persistent, alternative


def example_2_match_suggestion():
    """Exemple 2: Créer et gérer une MatchSuggestion."""
    print("\n" + "=" * 60)
    print("🎯 Exemple 2: MatchSuggestion et scoring")
    print("=" * 60)
    
    # Morceau manquant
    missing = Track(
        urlmd5="missing_001",
        title="Hey Jude",
        artist="The Beatles",
        album=None,
        url=None,
        playcount=0,
        source="tracks_persistent"
    )
    
    print(f"\n❌ Morceau manquant: {missing.display_name()}")
    
    # Créer une suggestion
    suggestion = MatchSuggestion(missing)
    
    # Candidats alternatifs
    candidates = [
        Track("alt_001", "Hey Jude", "The Beatles", "Hey Jude", None, 200),
        Track("alt_002", "Hey Jude", "Beatles", "Hey Jude", None, 180),
        Track("alt_003", "Hey Jude", "Various", "Best Of 60s", None, 50),
        Track("alt_004", "Jude", "John Lennon", "Solo", None, 10),
    ]
    
    scores = [98.5, 92.0, 55.0, 15.0]
    
    print(f"\n📋 Candidats évalués:")
    for i, (track, score) in enumerate(zip(candidates, scores), 1):
        suggestion.add_match(track, score)
        quality = "LIKELY ✅" if score >= 80 else ("POSSIBLE ⚠️" if score >= 60 else "UNLIKELY ❌")
        print(f"   {i}. {track.display_name():30} | {score:5.1f}% | {quality}")
    
    print(f"\n🤖 Auto-match possible: {'YES ✅' if suggestion.auto_match_possible else 'NO ⚠️'}")
    
    best = suggestion.get_best_match()
    if best:
        track, score = best
        print(f"🏆 Meilleur match: {track.display_name()} ({score:.1f}%)")
    
    print(f"\n🎯 Top 2 matches:")
    for i, (track, score) in enumerate(suggestion.get_top_n(2), 1):
        print(f"   {i}. {track.display_name()} ({score:.1f}%)")
    
    return suggestion


def example_3_sync_operations():
    """Exemple 3: Créer différentes opérations de sync."""
    print("\n" + "=" * 60)
    print("⚙️  Exemple 3: Opérations de synchronisation")
    print("=" * 60)
    
    # Opération COPY
    print(f"\n📋 Opération COPY:")
    print(f"   Scénario: Copier les données de alternativeplaycount vers tracks_persistent")
    
    op_copy = SyncOperation(
        missing_urlmd5="missing_001",
        selected_alternative_urlmd5="alternative_001",
        action="COPY",
        new_playcount=150
    )
    
    print(f"   Operation ID: {op_copy.operation_id}")
    print(f"   Timestamp: {op_copy.timestamp.isoformat()}")
    
    update_sql, delete_sql = op_copy.to_sql()
    print(f"   SQL 1 (UPDATE): {update_sql}")
    print(f"   SQL 2 (DELETE): {delete_sql}")
    
    # Opération MERGE
    print(f"\n📊 Opération MERGE:")
    print(f"   Scénario: Fusionner les playcounts (42 + 150 = 192)")
    
    op_merge = SyncOperation(
        missing_urlmd5="missing_001",
        selected_alternative_urlmd5="alternative_001",
        action="MERGE",
        new_playcount=192
    )
    
    print(f"   Operation ID: {op_merge.operation_id}")
    
    update_sql, delete_sql = op_merge.to_sql()
    print(f"   SQL 1 (UPDATE): {update_sql}")
    print(f"   SQL 2 (DELETE): {delete_sql}")
    
    # Opération DELETE
    print(f"\n🗑️  Opération DELETE:")
    print(f"   Scénario: Supprimer un morceau en doublon")
    
    op_delete = SyncOperation(
        missing_urlmd5="duplicate_001",
        selected_alternative_urlmd5="duplicate_alt_001",
        action="DELETE"
    )
    
    print(f"   Operation ID: {op_delete.operation_id}")
    
    update_sql, delete_sql = op_delete.to_sql()
    print(f"   SQL 1 (DELETE): {update_sql}")
    print(f"   SQL 2 (DELETE): {delete_sql}")
    
    return op_copy, op_merge, op_delete


def example_4_workflow_complete():
    """Exemple 4: Workflow complet: détection -> matching -> opération."""
    print("\n" + "=" * 60)
    print("🔄 Exemple 4: Workflow complet")
    print("=" * 60)
    
    # Étape 1: Détecter un morceau manquant
    print(f"\n1️⃣  Détection d'un morceau manquant:")
    
    missing = Track(
        urlmd5="missing_beethoven",
        title="Symphony No. 9",
        artist="Ludwig van Beethoven",
        album=None,
        url=None,
        playcount=0,
        source="tracks_persistent"
    )
    
    print(f"   Trouvé: {missing.display_name()}")
    print(f"   Playcount actuel: {missing.playcount}")
    
    # Étape 2: Matcher avec alternatives
    print(f"\n2️⃣  Recherche de correspondances:")
    
    suggestion = MatchSuggestion(missing)
    
    alt1 = Track("alt_b_1", "Symphony No. 9", "Beethoven", "Complete", None, 250)
    suggestion.add_match(alt1, 94.5)
    
    alt2 = Track("alt_b_2", "Symphony 9", "Beethoven", "Best Of", None, 100)
    suggestion.add_match(alt2, 82.0)
    
    print(f"   Correspondances trouvées: {len(suggestion.suggested_matches)}")
    for i, (track, score) in enumerate(suggestion.suggested_matches, 1):
        quality = "✅" if score >= 80 else "⚠️"
        print(f"   {i}. {track.display_name()} | {score:.1f}% {quality}")
    
    # Étape 3: Accepter le meilleur match
    print(f"\n3️⃣  Acceptation du meilleur match:")
    
    best = suggestion.get_best_match()
    if best:
        selected, score = best
        print(f"   Sélection: {selected.display_name()}")
        print(f"   Score de confiance: {score:.1f}%")
        
        # Calculer le nouveau playcount
        old_playcount = missing.playcount
        new_playcount = old_playcount + selected.playcount
        
        print(f"   Ancien playcount: {old_playcount}")
        print(f"   Playcount alternatif: {selected.playcount}")
        print(f"   Nouveau playcount (MERGE): {new_playcount}")
        
        # Étape 4: Créer l'opération de sync
        print(f"\n4️⃣  Création de l'opération de sync:")
        
        op = SyncOperation(
            missing_urlmd5=missing.urlmd5,
            selected_alternative_urlmd5=selected.urlmd5,
            action="MERGE",
            new_playcount=new_playcount
        )
        
        print(f"   Opération ID: {op.operation_id}")
        print(f"   Action: MERGE")
        print(f"   Timestamp: {op.timestamp.isoformat()}")
        
        # Étape 5: Générer et afficher les SQL
        print(f"\n5️⃣  SQL à exécuter:")
        
        update_sql, delete_sql = op.to_sql()
        print(f"   UPDATE:\n      {update_sql}")
        print(f"   DELETE:\n      {delete_sql}")
        
        # Étape 6: Export pour logging
        print(f"\n6️⃣  Export pour logging:")
        
        json_log = op.to_json()
        print(f"   JSON:\n{json_log}")


def example_5_validation_and_errors():
    """Exemple 5: Gestion des validations et erreurs."""
    print("\n" + "=" * 60)
    print("⚠️  Exemple 5: Validations et gestion d'erreurs")
    print("=" * 60)
    
    errors = []
    
    # Test 1: Playcount négatif
    print(f"\n❌ Erreur 1: Playcount négatif")
    try:
        Track("md5", "Song", "Artist", None, None, -5)
        print(f"   ✗ Validation échouée!")
    except ValueError as e:
        print(f"   ✓ Rejeté: {e}")
    
    # Test 2: Rating invalide
    print(f"\n❌ Erreur 2: Rating hors limites")
    try:
        Track("md5", "Song", "Artist", None, None, 10, rating=10)
        print(f"   ✗ Validation échouée!")
    except ValueError as e:
        print(f"   ✓ Rejeté: {e}")
    
    # Test 3: Source invalide
    print(f"\n❌ Erreur 3: Source invalide")
    try:
        Track("md5", "Song", "Artist", None, None, 10, source="INVALID")
        print(f"   ✗ Validation échouée!")
    except ValueError as e:
        print(f"   ✓ Rejeté: {e}")
    
    # Test 4: Action SyncOperation invalide
    print(f"\n❌ Erreur 4: Action SyncOperation invalide")
    try:
        SyncOperation("missing", "alt", "UNKNOWN")
        print(f"   ✗ Validation échouée!")
    except ValueError as e:
        print(f"   ✓ Rejeté: {e}")
    
    # Test 5: Score MatchSuggestion invalide
    print(f"\n❌ Erreur 5: Score MatchSuggestion invalide")
    try:
        track = Track("md5", "Song", "Artist", None, None, 10)
        suggestion = MatchSuggestion(track)
        suggestion.add_match(track, 150.0)  # Score > 100
        print(f"   ✗ Validation échouée!")
    except ValueError as e:
        print(f"   ✓ Rejeté: {e}")
    
    print(f"\n✅ Tous les tests de validation réussis!")


def main():
    """Exécuter tous les exemples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🎵 Exemples d'utilisation des modèles Track  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    
    example_1_track_creation()
    example_2_match_suggestion()
    example_3_sync_operations()
    example_4_workflow_complete()
    example_5_validation_and_errors()
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + "  ✅ Tous les exemples ont été exécutés  ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()


if __name__ == "__main__":
    main()
