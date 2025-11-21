# Migrations - MCP Hub Crawler

Documentation des migrations de schéma et de données.

## Structure

```
migrations/
├── schema/          # Évolution du schéma de base de données
│   ├── 001_sqlite_normalized_schema.sql
│   ├── 002_supabase_schema.sql
│   ├── 003_add_tool_parameters.sql
│   ├── 004_add_mcp_so_urls_table.sql
│   ├── 004_enhanced_github_info.sql
│   └── 005_remove_unique_constraint_mcp_so_url.sql
│
└── data/            # Migration des données
    ├── migration.sql (3.3 MB - migration complète consolidée)
    └── parts/       # Migration splitée en 13 parties pour Supabase MCP
        ├── 01_TRUNCATE_TABLES.sql
        ├── 02_SERVERS.sql
        ├── 03_GITHUB_INFO.sql
        ├── 04-12_MARKDOWN_*.sql (9 parties)
        └── 13_MCP_CONFIG_NPM.sql
```

## Migrations de Schéma

Les fichiers sont numérotés pour indiquer l'ordre d'application :

1. **001** - Schéma SQLite normalisé initial
2. **002** - Adaptation pour Supabase/PostgreSQL
3. **003** - Ajout de la table `tool_parameters`
4. **004** - Ajout table `mcp_so_urls` + enhanced GitHub info
5. **005** - Suppression contrainte unique sur `mcp_so_url`

## Migration des Données

### Fichier Consolidé

`migration.sql` (3.3 MB) contient la migration complète :
- 22 serveurs
- 21 enregistrements GitHub
- 17 configurations npm
- Contenu markdown des READMEs

### Fichiers Splitées

Le dossier `parts/` contient la même migration splitée en 13 fichiers pour contourner les limitations de taille du MCP Supabase tool.

**Note** : Les fichiers 04-12 contiennent le contenu markdown des READMEs, splité en 9 parties (~350 KB chacune).

## Statut

✅ **Migration terminée** (20 Nov 2025)
- Base SQLite locale : 199 serveurs
- Supabase : migration réussie
- Documentation : voir `docs/guides/migration/MIGRATION_STATUS_FINAL.md`
