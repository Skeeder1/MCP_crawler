# Scripts - MCP Hub Crawler

Guide des scripts du projet.

## Structure

```
scripts/
├── config.py              # Configuration partagée par tous les scripts
├── types/                 # Définitions TypeScript
│
├── pipeline/              # 🔥 Scripts principaux de collecte
│   ├── scrape_full_pipeline.py      # Pipeline complet (MAIN)
│   ├── scrape_mcp_so.py             # Scraper mcp.so registry
│   ├── scrape_mcpmarket.py          # Scraper mcpmarket.ai
│   ├── backfill_configs_from_readme.py
│   ├── enrich_github_info.py
│   ├── enrich_flomo.py
│   ├── enrich_minimax.py
│   ├── enrich_perplexity.py
│   ├── enrich_serper.py
│   └── rescrape_failed_phase2.py
│
├── tools/                 # 🛠️ Outils d'analyse et maintenance
│   ├── analysis/          # Analyse de base de données
│   │   ├── analyze-database.ts (TypeScript)
│   │   └── analyze-database.js (compilé)
│   │
│   ├── migration/         # Scripts de migration Supabase
│   │   ├── migrate_to_supabase_mcp.py
│   │   ├── migrate_in_chunks.py
│   │   ├── run_migration.py
│   │   └── sqlite_to_public_direct.py
│   │
│   ├── database/          # Gestion de base de données
│   │   ├── clean_database.py
│   │   ├── show_db_schema.py
│   │   ├── validate_db_integrity.py
│   │   └── validate_backfill_results.py
│   │
│   ├── inspection/        # Inspection et debugging
│   │   ├── check_*.py (6 scripts)
│   │   ├── inspect_*.py (2 scripts)
│   │   └── get_*.py (5 scripts)
│   │
│   └── utils/             # Utilitaires divers
│       ├── count_tools_visual.py
│       ├── extract_*.py (3 scripts)
│       ├── generate_coverage_report.py
│       ├── list_all_servers.py
│       └── analyze-db.bat (Windows)
│
└── archive/               # 📦 Scripts complétés (historique)
    ├── completed-fixes/   # Corrections one-off appliquées
    ├── one-off-validation/# Validations manuelles
    └── debug/             # Scripts de debug

```

## 🚀 Scripts Principaux

### Pipeline Complet
```bash
cd C:\GitHub\crawler MCPhub
python scripts/pipeline/scrape_full_pipeline.py
```

Lance le pipeline complet de collecte :
1. Scraping mcp.so + mcpmarket.ai
2. Enrichissement GitHub
3. Extraction des tools/parameters
4. Enrichissement serveurs spécifiques

### Analyse de Base de Données
```bash
node scripts/tools/analysis/analyze-database.js
```

Génère un rapport d'analyse complet dans `docs/reports/`.

## 📋 Configuration

Tous les scripts utilisent `config.py` pour :
- Chemins vers la base de données
- Configuration Supabase
- Variables d'environnement (chargées depuis `config/.env`)

## 🧪 Tests

Voir `tests/README.md` pour les tests automatisés (à venir).

## 📚 Documentation

- Guide migration : `docs/guides/migration/`
- Rapports d'analyse : `docs/reports/`
- Structure projet : `docs/PROJECT_STRUCTURE.md`
