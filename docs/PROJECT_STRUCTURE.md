# Structure du Projet - MCP Hub Crawler

Documentation de l'organisation du projet après la réorganisation du 21 Novembre 2025.

## 📁 Arborescence Complète

```
C:\GitHub\crawler MCPhub/
│
├── README.md                    # Documentation principale
├── CLAUDE.md                    # Instructions pour Claude Code
├── DATABASE.md                  # Documentation du schéma
├── .gitignore                   # Règles Git
│
├── config/                      # ⚙️ Configuration centralisée
│   ├── .env                     # Variables d'environnement (GIT IGNORED)
│   ├── .env.example             # Template de configuration
│   ├── requirements.txt         # Dépendances Python
│   ├── package.json             # Dépendances Node.js (analyse TypeScript)
│   ├── package-lock.json
│   └── tsconfig.json            # Configuration TypeScript
│
├── docs/                        # 📚 Documentation
│   ├── guides/
│   │   ├── ANALYZE-README.md
│   │   └── migration/
│   │       ├── MIGRATION_STATUS_FINAL.md
│   │       └── VERIFICATION_REPORT.md
│   ├── reports/
│   │   ├── db-analysis-2025-11-21.md
│   │   ├── missing-configs-analysis.md
│   │   ├── parser-improvement-recommendations.md
│   │   └── PROGRESS_REPORT_PHASE1-2.md
│   └── PROJECT_STRUCTURE.md     # Ce fichier
│
├── data/                        # 💾 Données
│   ├── mcp_servers.db           # Base SQLite principale (8.16 MB, 199 serveurs)
│   └── inspection/              # Artifacts d'inspection manuelle (24 fichiers)
│       ├── *.html, *.png, *.md
│       └── tools_sections/
│
├── migrations/                  # 🔄 Migrations
│   ├── schema/                  # Évolution du schéma (6 fichiers)
│   │   ├── 001_sqlite_normalized_schema.sql
│   │   ├── 002_supabase_schema.sql
│   │   ├── 003_add_tool_parameters.sql
│   │   ├── 004_add_mcp_so_urls_table.sql
│   │   ├── 004_enhanced_github_info.sql
│   │   └── 005_remove_unique_constraint_mcp_so_url.sql
│   ├── data/                    # Migration des données
│   │   ├── migration.sql        # Migration consolidée (3.3 MB)
│   │   └── parts/               # Migration splitée (13 fichiers)
│   └── README.md                # Documentation des migrations
│
├── scripts/                     # 🛠️ Scripts opérationnels
│   ├── config.py                # Configuration partagée
│   ├── types/                   # Définitions TypeScript
│   │   ├── database.types.ts
│   │   └── database.types.js
│   │
│   ├── pipeline/                # 🔥 Pipeline principal (10 scripts)
│   │   ├── scrape_full_pipeline.py         # 🚀 MAIN ENTRY POINT
│   │   ├── scrape_mcp_so.py
│   │   ├── scrape_mcpmarket.py
│   │   ├── backfill_configs_from_readme.py
│   │   └── enrich_*.py (6 enrichers)
│   │
│   ├── tools/                   # 🔧 Outils d'analyse et maintenance
│   │   ├── analysis/            # Analyse DB (2 fichiers TypeScript)
│   │   ├── migration/           # Migration Supabase (4 scripts)
│   │   ├── database/            # Gestion DB (4 scripts)
│   │   ├── inspection/          # Inspection (13 scripts)
│   │   └── utils/               # Utilitaires (6 scripts)
│   │
│   ├── archive/                 # 📦 Scripts complétés (historique)
│   │   ├── completed-fixes/     # Corrections appliquées (9 scripts)
│   │   ├── one-off-validation/  # Validations manuelles (9 scripts)
│   │   └── debug/               # Scripts de debug (2 scripts)
│   │
│   └── README.md                # Guide des scripts
│
├── src/                         # 📦 Package Python (bibliothèque réutilisable)
│   ├── __init__.py
│   ├── database/
│   │   └── models_normalized.py           # Modèles SQLAlchemy
│   ├── parsers/
│   │   ├── readme_parser.py               # Extraction configs README
│   │   ├── tools_parser.py                # Extraction tools
│   │   └── parameters_parser.py           # Extraction paramètres
│   ├── enrichers/
│   │   ├── github_enricher.py             # Enrichissement GitHub
│   │   ├── npm_enricher.py                # Enrichissement npm
│   │   ├── tools_enricher.py
│   │   └── parameters_enricher.py
│   └── scrapers/
│       └── base_scraper.py                # Classe de base scraper
│
├── tests/                       # 🧪 Tests (infrastructure préparée)
│   ├── unit/                    # Tests unitaires (à venir)
│   ├── integration/             # Tests d'intégration (à venir)
│   └── README.md                # Guide des tests
│
├── backups/                     # 💾 Sauvegardes (vide, préparé)
├── temp/                        # 📝 Fichiers temporaires (vide, préparé)
│
└── node_modules/                # 📦 Dépendances NPM (ignoré par Git)
```

## 🎯 Points d'Entrée Principaux

### 1. Pipeline de Collecte
```bash
python scripts/pipeline/scrape_full_pipeline.py
```
Lance le pipeline complet de scraping et enrichissement.

### 2. Analyse de Base de Données
```bash
node scripts/tools/analysis/analyze-database.js
```
Génère un rapport d'analyse complet.

### 3. Configuration
Fichier principal : `scripts/config.py`
Variables d'environnement : `config/.env`

## 📋 Organisation par Fonction

### Scripts Actifs (Production)
- `scripts/pipeline/` - Scripts exécutés régulièrement
- `scripts/tools/` - Outils d'analyse et maintenance

### Scripts Archivés (Historique)
- `scripts/archive/` - Scripts one-off complétés, conservés pour documentation

### Code Réutilisable (Bibliothèque)
- `src/` - Modules Python importés par les scripts

## 🔐 Sécurité

**Fichiers sensibles (GIT IGNORED)** :
- `config/.env` - Clés API et secrets
- `backups/` - Sauvegardes de base de données
- `temp/` - Fichiers temporaires

**Fichiers commitables** :
- `config/.env.example` - Template sans secrets
- Tout le reste du code

## 📊 Statistiques

- **Total fichiers** : ~115 fichiers
- **Scripts Python** : 55 scripts
- **Scripts TypeScript** : 3 fichiers (+ compilés)
- **Documentation** : 12 fichiers .md
- **Serveurs** : 199 dans la base SQLite
- **Migrations** : 20 fichiers SQL (6 schémas + 14 data)

## 🚀 Workflow de Développement

1. **Lire la doc** : `README.md`, `CLAUDE.md`, `DATABASE.md`
2. **Configuration** : Copier `config/.env.example` → `config/.env`
3. **Installer dépendances** : `pip install -r config/requirements.txt`
4. **Lancer pipeline** : `python scripts/pipeline/scrape_full_pipeline.py`
5. **Analyser résultats** : `node scripts/tools/analysis/analyze-database.js`

## 📝 Notes de Réorganisation

**Date** : 21 Novembre 2025
**Raison** : Trop de fichiers dispersés, structure confuse
**Changements** :
- ✅ Configuration centralisée dans `config/`
- ✅ Documentation consolidée dans `docs/`
- ✅ Scripts organisés par fonction (pipeline/tools/archive)
- ✅ Migrations consolidées dans `migrations/`
- ✅ Tests préparés dans `tests/`
- ✅ 46 fichiers inutiles supprimés
- ✅ 113 fichiers réorganisés

**Résultat** : Structure claire, professionnelle, maintenable.
