# 📖 Overview - Vue d'Ensemble du Projet

## 🎯 Qu'est-ce que Lyrion Playcount Sync ?

Application desktop pour **synchroniser les compteurs de lectures** entre deux sources dans Lyrion (serveur de musique).

### Le Problème Résolu

Lyrion stocke les playcounts dans **deux tables** :

```
┌─────────────────────────────────────────────────────────┐
│ tracks_persistent (Lyrion interne)                      │
│ ├─ urlmd5: ABC123                                       │
│ ├─ playcount: 150                    ┌──────────────┐   │
│ └─ ...                                │  INCOHÉRENCE │   │
│                                       │  Playcount    │   │
│ alternativeplaycount (Last.fm, etc.)  │  pas synchronisé  │
│ ├─ urlmd5: ABC123                     │              │   │
│ ├─ playcount: 200  (DIFFÉRENT!)       └──────────────┘   │
│ └─ ...                                                    │
└─────────────────────────────────────────────────────────┘
```

**Résultat** : Les compteurs ne sont pas cohérents entre les sources.

### La Solution

✅ **Détecte** les incohérences  
🔍 **Propose** des matchs automatiques  
✏️ **Synchronise** avec validation manuelle  
🗑️ **Nettoie** les tables après sync  

## 🏗️ Architecture Simple

```
┌──────────────────────────────────┐
│  Interface Graphique (Tkinter)   │
│  - Scanner                       │
│  - Viewer matches                │
│  - Éditeur actions               │
└────────────────┬─────────────────┘
                 │
┌────────────────▼─────────────────┐
│  Logique Métier                  │
│  - SyncDetector (SQL queries)    │
│  - TrackMatcher (fuzzy match)    │
│  - SyncOperations (DB update)    │
└────────────────┬─────────────────┘
                 │
┌────────────────▼─────────────────┐
│  Lyrion Database (SQLite)        │
│  - tracks_persistent            │
│  - alternativeplaycount         │
│  - tracks (metadata)            │
└──────────────────────────────────┘
```

## 🔧 Composants Clés

### 1. **SyncDetector** 
Trouve les morceaux à synchroniser via requêtes SQL :
- Morceaux dans `tracks_persistent` mais pas dans `alternativeplaycount`
- Morceaux avec playcounts différents

### 2. **TrackMatcher**
Propose des matchs entre les morceaux en utilisant RapidFuzz :
- Matching par titre + artiste + album
- Score de confiance (0-100%)

### 3. **GUI (MainWindow + MatchDialog)**
Interface utilisateur pour :
- Voir les détections
- Valider/ajuster les matchs
- Exécuter les synchronisations

### 4. **SyncOperations**
Exécute les opérations DB en toute sécurité :
- Transactions SQL (rollback si erreur)
- Backup automatiques
- Logging détaillé

## 🎨 Workflow Utilisateur

```
┌─────────────┐
│   Démarrer  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ Cliquer "Scanner"        │
│ → Analyse la DB          │
│ → Affiche incohérences   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Voir les matches proposés            │
│ → Double-clic pour détails           │
│ → Couleur = confiance (🟢🟠🔴)      │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Valider et synchroniser              │
│ → Choisir action (COPY/MERGE)        │
│ → Valider chaque match               │
│ → Cliquer "Appliquer"                │
└──────┬───────────────────────────────┘
       │
       ▼
┌───────────────────────┐
│ ✅ Synchronisation OK │
│ → Backup créé         │
│ → Tables mises à jour │
└───────────────────────┘
```

## 💾 Données Lyrion

### Tables Principales

**tracks_persistent**
```sql
urlmd5 TEXT PRIMARY KEY,        -- Identifiant unique
playcount INTEGER,              -- Compteur Lyrion
lastplayed INTEGER,             -- Dernière écoute
rating INTEGER                  -- Note utilisateur
```

**alternativeplaycount**
```sql
urlmd5 TEXT PRIMARY KEY,        -- Identifiant unique
playcount INTEGER,              -- Compteur source externe
lastplayed INTEGER,             -- Dernière écoute
source TEXT                     -- Source (Last.fm, etc)
```

**tracks** (Métadonnées)
```sql
id INTEGER PRIMARY KEY,
url TEXT,                       -- Chemin du fichier
urlmd5 TEXT,                    -- Lien vers autres tables
title TEXT,                     -- Titre
album INTEGER                   -- ID album
```

## 🔐 Sécurité

✅ **Backup automatique** avant chaque sync  
✅ **Transactions SQL** (rollback si erreur)  
✅ **Validation manuelle** de chaque opération  
✅ **Logs détaillés** de toutes les actions  
✅ **Permissions vérifiées** au démarrage  

## 🚀 Déploiement

Deux options :

### Docker (Recommandé)
```bash
docker-compose -f config/docker-compose.yml up -d
# Accès : http://localhost:6080/vnc.html
```

### Local (Dev)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/main.py
```

## 📊 Cas d'Usage

### Pour les Fans de Musique
Synchroniser Last.fm ou ListenBrainz avec Lyrion sans risquer la DB

### Pour les Administrateurs NAS
Maintenir la cohérence entre sources sur Synology/QNAP

### Pour les Développeurs
Intégrer Lyrion avec d'autres outils musicaux

## 🔄 Flux de Synchronisation

```
1️⃣ DÉTECTION
   SELECT * FROM tracks_persistent tp
   WHERE NOT EXISTS (
     SELECT 1 FROM alternativeplaycount ap
     WHERE ap.urlmd5 = tp.urlmd5
   )

2️⃣ MATCHING
   Pour chaque morceau non-trouvé:
   - Chercher dans tracks pour métadonnées
   - Fuzzy match sur titre/artiste
   - Retourner meilleur candidat + score

3️⃣ VALIDATION
   Utilisateur approuve ou corrige le match

4️⃣ SYNCHRONISATION
   INSERT/UPDATE dans alternativeplaycount
   avec protection transactions SQL

5️⃣ CLEANUP
   Optionnel: DELETE depuis tracks_persistent
```

## 📝 Próximos Passos

- [Installation](../02-installation/) - Mettre en place l'app
- [Configuration](../03-configuration/) - Adapter les paramètres
- [Guide Utilisateur](../04-usage/USER_GUIDE.md) - Apprendre à l'utiliser
- [Architecture](../05-architecture/) - Comprendre le code

---

**Prêt à commencer ?** → [Quick Start](./QUICKSTART.md)
