# 🗄️ Database Schema Documentation - MCP Hub

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tables](#tables)
- [Relationships](#relationships)
- [Triggers](#triggers)
- [Views](#views)
- [Migration Guide](#migration-guide)
- [Query Examples](#query-examples)

---

## Overview

### Schema Version
**v2.0 - Normalized Schema** (January 2025)

### Database Type
SQLite 3 (Normalized structure with 11 tables)

### Key Features
- ✅ Fully normalized schema (3NF)
- ✅ Separate tables for GitHub, NPM, and MCP configuration
- ✅ Many-to-many relationships for categories and tags
- ✅ Automatic counters via triggers
- ✅ Support for both NPM and Docker deployments
- ✅ Markdown content storage with multiple types

### Database Files
- **Main Database**: `data/mcp_servers_normalized.db`
- **Old Database (backup)**: `data/mcp_servers.db`
- **Backup**: `data/mcp_servers_backup.db`

---

## Architecture

### Table Structure (11 Tables)

```
┌─────────────────┐
│    SERVERS      │ ← Core table
└────────┬────────┘
         │
    ┌────┴────┬──────────┬───────────┬──────────┬──────────┬─────────────┐
    │         │          │           │          │          │             │
┌───▼──┐  ┌──▼──┐  ┌────▼─────┐ ┌──▼────┐ ┌───▼────┐ ┌───▼─────┐  ┌───▼─────┐
│MD    │  │tools│  │github_   │ │npm_   │ │mcp_    │ │server_  │  │server_  │
│cont. │  │     │  │info      │ │info   │ │config_ │ │categor. │  │tags     │
└──────┘  └─────┘  └──────────┘ └───────┘ │npm/    │ └────┬────┘  └────┬────┘
                                            │docker  │      │            │
                                            └────────┘  ┌───▼───┐    ┌───▼───┐
                                                        │categor│    │ tags  │
                                                        │ies    │    │       │
                                                        └───────┘    └───────┘
```

### Design Principles
1. **Separation of Concerns**: Each entity has its own table
2. **Denormalization for Performance**: Creator info duplicated in servers table
3. **Flexibility**: Support for multiple deployment methods (NPM/Docker)
4. **Extensibility**: Easy to add new metadata sources

---

## Tables

### 1. `servers` (Core Table)

**Purpose**: Stores core server metadata

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `slug` | TEXT | Unique URL-friendly identifier |
| `name` | TEXT | Server name |
| `display_name` | TEXT | Display name for UI |
| `tagline` | TEXT | Short tagline (200 chars) |
| `short_description` | TEXT | Full description |
| `logo_url` | TEXT | URL to server logo |
| `homepage_url` | TEXT | Homepage URL |
| `install_count` | INTEGER | Number of installations |
| `favorite_count` | INTEGER | Number of favorites |
| `tools_count` | INTEGER | Number of tools (auto-updated) |
| `status` | TEXT | approval status (approved/pending/rejected) |
| `verification_status` | TEXT | verified/unverified |
| `creator_id` | TEXT (UUID) | Creator UUID |
| `creator_name` | TEXT | Creator display name |
| `creator_username` | TEXT | Creator username (NOT NULL) |
| `created_at` | DATETIME | Creation timestamp |
| `published_at` | DATETIME | Publication timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes**:
- `idx_servers_slug` on `slug`
- `idx_servers_status` on `status`
- `idx_servers_creator_username` on `creator_username`
- `idx_servers_updated_at` on `updated_at DESC`

---

### 2. `markdown_content`

**Purpose**: Stores markdown content sections

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `server_id` | TEXT (UUID FK) | Foreign key to servers |
| `content_type` | TEXT | Type: about/readme/faq/tools |
| `content` | TEXT | Markdown content |
| `content_html` | TEXT | Pre-rendered HTML (optional) |
| `word_count` | INTEGER | Word count |
| `estimated_reading_time_minutes` | INTEGER | Est. reading time |
| `extracted_from` | TEXT | Source URL |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Constraints**:
- UNIQUE constraint on `(server_id, content_type)`

**Indexes**:
- `idx_markdown_server_id` on `server_id`
- `idx_markdown_content_type` on `content_type`

---

### 3. `github_info`

**Purpose**: GitHub repository information

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `server_id` | TEXT (UUID FK, UNIQUE) | Foreign key to servers |
| `github_url` | TEXT | Full GitHub URL |
| `github_owner` | TEXT | Repository owner |
| `github_repo` | TEXT | Repository name |
| `github_stars` | INTEGER | Star count |
| `github_forks` | INTEGER | Fork count |
| `github_watchers` | INTEGER | Watcher count |
| `github_open_issues` | INTEGER | Open issues count |
| `github_last_commit` | DATETIME | Last commit date |
| `github_created_at` | DATETIME | Repo creation date |
| `default_branch` | TEXT | Default branch (main/master) |
| `created_at` | DATETIME | Record creation |
| `updated_at` | DATETIME | Record update |
| `last_synced_at` | DATETIME | Last sync with GitHub API |

**Indexes**:
- `idx_github_info_server_id` on `server_id`
- `idx_github_info_stars` on `github_stars DESC`
- `idx_github_info_owner` on `github_owner`
- `idx_github_info_last_commit` on `github_last_commit DESC`

---

### 4. `npm_info`

**Purpose**: npm package information

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `server_id` | TEXT (UUID FK, UNIQUE) | Foreign key to servers |
| `npm_package` | TEXT | Package name (with scope) |
| `npm_version` | TEXT | Current version |
| `npm_downloads_weekly` | INTEGER | Weekly downloads |
| `npm_downloads_monthly` | INTEGER | Monthly downloads |
| `npm_license` | TEXT | License type |
| `npm_homepage` | TEXT | Homepage URL |
| `npm_repository_url` | TEXT | Repository URL |
| `latest_version` | TEXT | Latest version |
| `latest_version_published_at` | DATETIME | Latest version publish date |
| `created_at` | DATETIME | Record creation |
| `updated_at` | DATETIME | Record update |
| `last_synced_at` | DATETIME | Last sync with npm API |

**Indexes**:
- `idx_npm_info_server_id` on `server_id`
- `idx_npm_info_package` on `npm_package`
- `idx_npm_info_downloads` on `npm_downloads_weekly DESC`

---

### 5. `mcp_config_npm`

**Purpose**: NPM-based MCP server configuration

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `server_id` | TEXT (UUID FK, UNIQUE) | Foreign key to servers |
| `command` | TEXT | Command: npx/node/npm |
| `args` | TEXT (JSON) | Arguments array as JSON |
| `env_required` | TEXT (JSON) | Required env vars as JSON array |
| `env_descriptions` | TEXT (JSON) | Env var descriptions as JSON object |
| `runtime` | TEXT | Runtime (default: node) |
| `created_at` | DATETIME | Record creation |
| `updated_at` | DATETIME | Record update |

**Constraints**:
- CHECK constraint: `command IN ('npx', 'node', 'npm')`
- **Mutually exclusive with `mcp_config_docker`** (enforced by trigger)

**Indexes**:
- `idx_mcp_npm_server_id` on `server_id`

**Example JSON formats**:
```json
// args
["-y", "@modelcontextprotocol/server-brave-search"]

// env_required
["BRAVE_API_KEY", "OTHER_KEY"]

// env_descriptions
{
  "BRAVE_API_KEY": {
    "label": "Brave API Key",
    "description": "Your Brave Search API key",
    "type": "secret",
    "get_url": "https://brave.com/api",
    "example": "BSA..."
  }
}
```

---

### 6. `mcp_config_docker`

**Purpose**: Docker-based MCP server configuration

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `server_id` | TEXT (UUID FK, UNIQUE) | Foreign key to servers |
| `docker_image` | TEXT | Docker image name |
| `docker_tag` | TEXT | Docker tag (default: latest) |
| `docker_command` | TEXT (JSON) | Command array as JSON |
| `env_required` | TEXT (JSON) | Required env vars as JSON array |
| `env_descriptions` | TEXT (JSON) | Env var descriptions as JSON object |
| `ports` | TEXT (JSON) | Port mappings as JSON object |
| `volumes` | TEXT (JSON) | Volume mappings as JSON object |
| `network_mode` | TEXT | Network mode (default: bridge) |
| `runtime` | TEXT | Runtime (default: docker) |
| `created_at` | DATETIME | Record creation |
| `updated_at` | DATETIME | Record update |

**Constraints**:
- **Mutually exclusive with `mcp_config_npm`** (enforced by trigger)

**Indexes**:
- `idx_mcp_docker_server_id` on `server_id`

**Example JSON formats**:
```json
// docker_command
["--host", "0.0.0.0", "--port", "8080"]

// ports
{"8080": "8080", "5432": "5432"}

// volumes
{"/data": "/var/lib/postgresql/data"}
```

---

### 7. `tools`

**Purpose**: Individual tools provided by MCP servers

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `server_id` | TEXT (UUID FK) | Foreign key to servers |
| `name` | TEXT | Tool name (unique per server) |
| `display_name` | TEXT | Display name |
| `description` | TEXT | Tool description |
| `input_schema` | TEXT (JSON) | JSON Schema for inputs |
| `example_usage` | TEXT | Usage example |
| `example_response` | TEXT | Response example |
| `category` | TEXT | Tool category |
| `is_dangerous` | INTEGER | 0/1 boolean |
| `requires_auth` | INTEGER | 0/1 boolean |
| `display_order` | INTEGER | Display order |
| `created_at` | DATETIME | Record creation |
| `updated_at` | DATETIME | Record update |

**Constraints**:
- UNIQUE constraint on `(server_id, name)`

**Indexes**:
- `idx_tools_server_id` on `server_id`
- `idx_tools_category` on `category`
- `idx_tools_name` on `name`

---

### 8. `categories`

**Purpose**: Reusable categories for organizing servers

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `slug` | TEXT | Unique slug |
| `name` | TEXT | Category name (unique) |
| `description` | TEXT | Description |
| `icon` | TEXT | Icon name or URL |
| `color` | TEXT | Color hex code |
| `server_count` | INTEGER | Number of servers (auto-updated) |
| `display_order` | INTEGER | Display order |
| `created_at` | DATETIME | Record creation |

---

### 9. `server_categories` (Junction Table)

**Purpose**: Many-to-many relationship between servers and categories

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `server_id` | TEXT (UUID FK) | Foreign key to servers (PK) |
| `category_id` | TEXT (UUID FK) | Foreign key to categories (PK) |
| `display_order` | INTEGER | Display order for this server |
| `added_at` | DATETIME | When added |

**Indexes**:
- `idx_server_categories_server_id` on `server_id`
- `idx_server_categories_category_id` on `category_id`

---

### 10. `tags`

**Purpose**: Reusable tags for labeling servers

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key |
| `slug` | TEXT | Unique slug |
| `name` | TEXT | Tag name (unique) |
| `description` | TEXT | Description |
| `color` | TEXT | Color hex code |
| `server_count` | INTEGER | Number of servers (auto-updated) |
| `created_at` | DATETIME | Record creation |

---

### 11. `server_tags` (Junction Table)

**Purpose**: Many-to-many relationship between servers and tags

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `server_id` | TEXT (UUID FK) | Foreign key to servers (PK) |
| `tag_id` | TEXT (UUID FK) | Foreign key to tags (PK) |
| `display_order` | INTEGER | Display order for this server |
| `added_at` | DATETIME | When added |

**Indexes**:
- `idx_server_tags_server_id` on `server_id`
- `idx_server_tags_tag_id` on `tag_id`

---

## Relationships

### Cardinalities

| Relationship | Type | Description |
|--------------|------|-------------|
| `servers` ↔ `markdown_content` | 1:N (0-4) | One server has 0-4 markdown sections (about, readme, faq, tools) |
| `servers` ↔ `github_info` | 1:0..1 | One server may have GitHub info (optional) |
| `servers` ↔ `npm_info` | 1:0..1 | One server may have npm info (optional) |
| `servers` ↔ `mcp_config_npm` | 1:0..1 | One server has npm config OR... |
| `servers` ↔ `mcp_config_docker` | 1:0..1 | ...docker config (mutually exclusive) |
| `servers` ↔ `tools` | 1:N | One server provides multiple tools |
| `servers` ↔ `categories` | N:M | Many-to-many via server_categories |
| `servers` ↔ `tags` | N:M | Many-to-many via server_tags |

---

## Triggers

### Auto-Counter Triggers

**1. Category Counter**
- `trigger_category_count_insert`: Increment category.server_count on INSERT
- `trigger_category_count_delete`: Decrement category.server_count on DELETE

**2. Tag Counter**
- `trigger_tag_count_insert`: Increment tag.server_count on INSERT
- `trigger_tag_count_delete`: Decrement tag.server_count on DELETE

**3. Tools Counter**
- `trigger_tools_count_insert`: Increment servers.tools_count on INSERT
- `trigger_tools_count_delete`: Decrement servers.tools_count on DELETE

### Mutual Exclusion Triggers

**NPM vs Docker Config**
- `enforce_single_mcp_config_npm`: Prevents adding npm config if docker config exists
- `enforce_single_mcp_config_docker`: Prevents adding docker config if npm config exists

---

## Views

### `v_servers_complete`

**Purpose**: Complete server information with joined data

**Columns**:
- All columns from `servers`
- GitHub info (url, owner, repo, stars, last_commit)
- npm info (package, version, downloads_weekly)
- Runtime and config command

**Usage**:
```sql
SELECT * FROM v_servers_complete WHERE slug = 'brave-search';
```

---

## Migration Guide

### Migrating from Old Schema to Normalized Schema

**Step 1: Run Migration Script**
```bash
python scripts/migrate_to_normalized.py
```

**Step 2: Verify Migration**
```bash
python -c "import sqlite3; conn = sqlite3.connect('data/mcp_servers_normalized.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM servers'); print('Servers:', cursor.fetchone()[0])"
```

**Step 3: Update Code to Use New Models**
```python
# Old
from src.database.models import Server

# New
from src.database.models_normalized import Server
```

**Step 4: Replace Database** (Optional)
```bash
# Backup old database
cp data/mcp_servers.db data/mcp_servers_old.db

# Replace with normalized version
mv data/mcp_servers_normalized.db data/mcp_servers.db
```

### Data Transformation During Migration

| Old Schema | New Schema | Transformation |
|------------|------------|----------------|
| `servers.description` | `servers.tagline` + `servers.short_description` | First 200 chars → tagline |
| `servers.author` | `servers.creator_username` + `servers.creator_name` | Copied |
| `servers.npm_package` | `npm_info.npm_package` | Extracted to separate table |
| `servers.github_url` | `github_info.*` | Parsed and extracted owner/repo |
| `server_content.about/readme/faq` | `markdown_content` (3 rows) | Split into separate rows |
| `server_tools` | `tools` | One-to-one mapping |
| `server_tags` | `tags` + `server_tags` | Deduplicated tags |

---

## Query Examples

### Get Server with All Related Data

```sql
-- Using the view
SELECT * FROM v_servers_complete WHERE slug = 'brave-search';

-- Manual join
SELECT
  s.*,
  gh.github_stars,
  npm.npm_package,
  mcn.command as npm_command
FROM servers s
LEFT JOIN github_info gh ON gh.server_id = s.id
LEFT JOIN npm_info npm ON npm.server_id = s.id
LEFT JOIN mcp_config_npm mcn ON mcn.server_id = s.id
WHERE s.slug = 'brave-search';
```

### Get Server with Tools

```sql
SELECT
  s.name,
  s.slug,
  json_group_array(
    json_object(
      'name', t.name,
      'description', t.description
    )
  ) as tools
FROM servers s
LEFT JOIN tools t ON t.server_id = s.id
WHERE s.slug = 'brave-search'
GROUP BY s.id;
```

### Get Server with Categories and Tags

```sql
SELECT
  s.name,
  s.slug,
  GROUP_CONCAT(DISTINCT c.name) as categories,
  GROUP_CONCAT(DISTINCT t.name) as tags
FROM servers s
LEFT JOIN server_categories sc ON sc.server_id = s.id
LEFT JOIN categories c ON c.id = sc.category_id
LEFT JOIN server_tags st ON st.server_id = s.id
LEFT JOIN tags t ON t.id = st.tag_id
WHERE s.slug = 'brave-search'
GROUP BY s.id;
```

### Search Servers by Text

```sql
-- Full-text search in servers
SELECT * FROM servers
WHERE name LIKE '%brave%'
   OR tagline LIKE '%search%'
   OR short_description LIKE '%api%';

-- Search with join to markdown content
SELECT DISTINCT s.*
FROM servers s
LEFT JOIN markdown_content mc ON mc.server_id = s.id
WHERE s.name LIKE '%brave%'
   OR mc.content LIKE '%search%';
```

### Top Servers by GitHub Stars

```sql
SELECT
  s.name,
  s.slug,
  gh.github_stars,
  gh.github_forks
FROM servers s
INNER JOIN github_info gh ON gh.server_id = s.id
ORDER BY gh.github_stars DESC
LIMIT 10;
```

### Servers by Category

```sql
SELECT
  c.name as category,
  s.name as server_name,
  s.slug
FROM categories c
INNER JOIN server_categories sc ON sc.category_id = c.id
INNER JOIN servers s ON s.id = sc.server_id
WHERE c.slug = 'data-analysis'
ORDER BY sc.display_order;
```

### Popular Tags

```sql
SELECT
  t.name,
  t.slug,
  t.server_count
FROM tags t
ORDER BY t.server_count DESC
LIMIT 20;
```

---

## Statistics

### Current Database Stats (as of migration)

| Metric | Count |
|--------|-------|
| Total Servers | 80 |
| Servers with NPM info | 45 |
| Servers with MCP configs | 45 |
| Total Tools | 57 |
| Unique Tags | 0 (to be populated) |
| Unique Categories | 0 (to be populated) |

### Database Size

```sql
-- Get database size
SELECT page_count * page_size as size
FROM pragma_page_count(), pragma_page_size();

-- Get table sizes
SELECT
  name,
  (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=m.name) as indexes,
  (SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND tbl_name=m.name) as triggers
FROM sqlite_master m
WHERE type='table'
ORDER BY name;
```

---

## Maintenance

### Vacuum Database

```sql
VACUUM;
```

### Analyze Tables

```sql
ANALYZE;
```

### Check Integrity

```sql
PRAGMA integrity_check;
```

### Foreign Key Check

```sql
PRAGMA foreign_key_check;
```

---

## Future Enhancements

### Planned Features

1. **Full-Text Search**: Add FTS5 virtual tables for better search
2. **Version History**: Track changes to servers over time
3. **User Management**: Add users, authentication, and permissions
4. **Analytics**: Track server downloads, usage, and popularity
5. **API Rate Limiting**: Track API calls and rate limits
6. **Webhooks**: Support for GitHub/npm webhooks to auto-update data

### Possible New Tables

- `users`: User accounts and profiles
- `server_versions`: Historical versions of servers
- `downloads`: Download tracking and analytics
- `reviews`: User reviews and ratings
- `api_keys`: API key management
- `webhooks`: Webhook configurations

---

## Contributing

When adding new features to the database:

1. Create a new migration file in `migrations/`
2. Update this documentation
3. Update the models in `src/database/models_normalized.py`
4. Write tests for the new functionality
5. Run integrity checks before committing

---

## Support

For questions or issues related to the database schema:
- Check the [README.md](README.md) for general project information
- Review [CLAUDE.md](CLAUDE.md) for development guidelines
- Open an issue on GitHub for bugs or feature requests

---

**Last Updated**: 2025-01-19
**Schema Version**: v2.0
**Maintainer**: Claude + User
