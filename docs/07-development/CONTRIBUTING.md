# 🤝 Contributing - Guide Contribution

Merci de votre intérêt pour contribuer à Lyrion Playcount Sync !

## 📝 Types de Contributions

### 📖 Documentation

La documentation est aussi importante que le code !

```bash
# Éditer la documentation
docs/
├── 01-getting-started/
├── 02-installation/
├── 03-configuration/
├── 04-usage/
├── 05-architecture/
├── 06-docker/
├── 07-development/
└── 08-reference/
```

**À faire :**
- Améliorer l'existant
- Corriger les typos
- Ajouter des exemples
- Clarifier les explications

**À éviter :**
- Ne pas éditer racine du projet
- Utiliser la structure `docs/`
- Tester les liens Markdown

### 🐛 Bug Reports

Créer une issue GitHub avec :

```markdown
## 🐛 Description du Bug

[Description claire du problème]

## 📋 Étapes pour reproduire

1. [Étape 1]
2. [Étape 2]
3. [Étape 3]

## 💭 Comportement Attendu

[Description du comportement attendu]

## 💥 Comportement Réel

[Description du comportement réel]

## 📦 Environnement

- OS: [Windows/Linux/macOS]
- Python: 3.x.x
- Docker: [Oui/Non]
- Logs: [coller logs pertinents]
```

### 🎁 Nouvelles Fonctionnalités

Proposer d'abord une issue pour discuter :

```markdown
## 🎁 Nouvelle Fonctionnalité

### Description
[Description claire de la fonctionnalité]

### Cas d'Usage
[Qui en aurait besoin ? Pourquoi ?]

### Solution Proposée
[Comment implémenter ?]

### Alternatives Considérées
[Y a-t-il d'autres solutions ?]
```

## 💻 Contribution Code

### Workflow

```bash
# 1. Fork le projet
# (bouton Fork sur GitHub)

# 2. Clone ta version
git clone https://github.com/TON-USER/lyrion-playcount-sync.git
cd lyrion-playcount-sync

# 3. Créer une branche
git checkout -b feature/ma-feature

# 4. Faire les changements
# ... éditer les fichiers ...

# 5. Tester
pytest tests/

# 6. Commit
git commit -am "feat: Description courte"

# 7. Push
git push origin feature/ma-feature

# 8. Créer Pull Request
# Aller sur GitHub et ouvrir une PR
```

### Conventions de Commit

Utiliser le format **Conventional Commits** :

```
<type>(<scope>): <message>
```

**Types** :
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction bug
- `docs:` Changement documentation
- `style:` Formatage, sans impact code
- `refactor:` Restructuration code
- `test:` Ajout/modification tests
- `chore:` Maintenance, dépendances

**Exemples** :
```bash
git commit -m "feat(sync): Ajout support mode merge"
git commit -m "fix(db): Correction typo requête SQL"
git commit -m "docs: Amélioration guide installation"
git commit -m "refactor: Simplification SyncDetector"
git commit -m "test: 100% coverage SyncOperations"
```

### Style de Code

Respecter **PEP 8** :

```bash
# Installer outils
pip install black flake8 mypy

# Formater
black src/

# Linter
flake8 src/

# Type checking
mypy src/
```

**Directives** :
- Max 100 caractères par ligne
- Docstrings pour toutes les fonctions/classes
- Type hints (Python 3.9+)
- Tests pour chaque nouvelle fonction

### Tests

Ajouter des tests pour :
- Nouvelles fonctionnalités
- Corrections de bugs
- Edge cases

```bash
# Lancer tous les tests
pytest tests/

# Avec couverture
pytest --cov=src tests/

# Test spécifique
pytest tests/test_sync_detector.py::test_detect_missing_tracks
```

Structure tests :

```python
import pytest
from src.models.sync_detector import SyncDetector

class TestSyncDetector:
    
    def test_detect_missing_tracks(self, db_connection):
        """Test détection morceaux manquants"""
        detector = SyncDetector(db_connection)
        missing = detector.detect_missing_tracks()
        
        assert len(missing) > 0
        assert missing[0]['urlmd5'] is not None
    
    def test_detect_with_empty_db(self, empty_db):
        """Test comportement DB vide"""
        detector = SyncDetector(empty_db)
        missing = detector.detect_missing_tracks()
        
        assert missing == []
```

## 📚 Bonnes Pratiques

### Code

✅ **À faire** :
- Écrire du code clair et lisible
- Ajouter des commentaires utiles
- Respcter la structure existante
- Tester avant de commit

❌ **À éviter** :
- Code vitreux sans commentaires
- Functions géantes (>50 lignes)
- Hardcoding de valeurs
- Commits énormes

### Documentation

✅ **À faire** :
- Utiliser Markdown clair
- Ajouter des exemples
- Documenter les paramètres
- Corriger les typos

❌ **À éviter** :
- Documentation obsolète
- Liens cassés
- Exemples non fonctionnels
- Syntaxe Markdown incorrecte

### PR (Pull Requests)

✅ **À faire** :
- Description claire et concise
- Lien vers issues associées
- Reviewer assigné
- Tous les tests passent

❌ **À éviter** :
- PR énormes (découper en petites)
- Changements non-relatifs
- Pas de description
- Code non-testé

## 🎯 Areas d'Amélioration

Si vous cherchez par où commencer :

### 🟢 Facile
- [ ] Corriger typos documentation
- [ ] Améliorer README
- [ ] Ajouter exemples d'utilisation
- [ ] Améliorer messages d'erreur

### 🟡 Moyen
- [ ] Ajouter plus de tests
- [ ] Améliorer logging
- [ ] Optimiser requêtes SQL
- [ ] Ajouter type hints

### 🔴 Difficile
- [ ] Interface web alternative à VNC
- [ ] API REST pour l'application
- [ ] Support multiples sources de sync
- [ ] Sync bidirectionnel

## 📋 Checklist Avant PR

- [ ] Tests ajoutés (si applicable)
- [ ] Tous les tests passent (`pytest`)
- [ ] Code formaté (`black`)
- [ ] Pas de warnings linter (`flake8`)
- [ ] Type checking OK (`mypy`)
- [ ] Documentation mise à jour
- [ ] Changelog mis à jour
- [ ] Commits avec bons messages
- [ ] Pas de secrets (clés API, passwords)
- [ ] Reviewed au moins 1x

## 🔄 Process de Revue

**Cycle de Revue** :

1. **PR ouverte** → Vérifier CI
2. **Code review** → Commentaires du maintainer
3. **Adjustments** → Répondre aux commentaires
4. **Approval** → Au moins 1 reviewer
5. **Merge** → Le maintainer merge

**Temps de réponse** :
- Comment → 2-3 jours
- Décision merge → 1 semaine max

## 🙏 Merci !

Tout contribution compte, du typo corrigé à la nouvelle fonctionnalité.

Nous apprécions votre aide pour améliorer le projet !

---

**Questions ?** → [GitHub Discussions](https://github.com/ton-user/lyrion-playcount-sync/discussions)
