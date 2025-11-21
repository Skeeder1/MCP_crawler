# 📘 Guide Technique - MCP Hub Crawler

> Documentation technique complète de l'architecture, du fonctionnement du code et des interactions entre composants.

**Date**: 21 Novembre 2025
**Version**: 2.0 (après réorganisation)

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Architecture Générale](#2-architecture-générale)
3. [Flow de Données Complet](#3-flow-de-données-complet)
4. [Modules et Composants](#4-modules-et-composants)
5. [Base de Données](#5-base-de-données)
6. [Interactions entre Fichiers](#6-interactions-entre-fichiers)
7. [Patterns de Code](#7-patterns-de-code)
8. [Configuration et Anti-Détection](#8-configuration-et-anti-détection)
9. [Gestion d'Erreurs](#9-gestion-derreurs)
10. [Guide Développeur](#10-guide-développeur)

---

## 1. Vue d'Ensemble

### Objectif du Projet

Le MCP Hub Crawler est un système automatisé de collecte et d'enrichissement de métadonnées pour les serveurs MCP (Model Context Protocol). Il scrape, enrichit, parse et stocke des informations depuis :

- 🌐 **mcp.so** - Marketplace officiel
- 🛒 **mcpmarket.ai** - Marketplace alternatif
- 🐙 **GitHub API** - Métadonnées des repositories
- 📦 **npm Registry** - Informations des packages Node.js

### Technologies Utilisées

| Technologie | Usage | Fichiers Clés |
|-------------|-------|---------------|
| **Python 3.10+** | Langage principal | Tout le code |
| **SQLAlchemy** | ORM pour SQLite | `src/database/models_normalized.py` |
| **Playwright** | Scraping web avec navigateur | `src/scrapers/base_scraper.py` |
| **aiohttp** | Requêtes HTTP async | `src/enrichers/*.py` |
| **TypeScript** | Analyse de base de données | `scripts/tools/analysis/analyze-database.ts` |
| **SQLite** | Base de données | `data/mcp_servers.db` |

### Chiffres Clés

- **199 serveurs** MCP collectés
- **11 tables** SQL normalisées
- **4 sources** de données externes
- **3 phases** de traitement principales
- **10 scripts** pipeline actifs
- **27 outils** d'analyse et maintenance

---

## 2. Architecture Générale

### Schéma d'Architecture Haut Niveau

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOURCES EXTERNES                          │
├─────────────────────────────────────────────────────────────────┤
│  mcp.so  │  mcpmarket.ai  │  GitHub API  │  npm Registry       │
└────┬────────────┬──────────────┬───────────────┬────────────────┘
     │            │              │               │
     ▼            ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE COLLECTE                             │
├─────────────────────────────────────────────────────────────────┤
│  BaseScraper (Playwright)  │  GitHubEnricher  │  NpmEnricher   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE PARSING                              │
├─────────────────────────────────────────────────────────────────┤
│  ReadmeParser  │  ToolsParser  │  ParametersParser             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   COUCHE PERSISTANCE                             │
├─────────────────────────────────────────────────────────────────┤
│           SQLAlchemy Models + SQLite Database                   │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Principal

Le fichier **`scripts/pipeline/scrape_full_pipeline.py`** (365 lignes) orchestre tout :

```
Phase 1: Nettoyage DB
    ↓
Phase 2: Collecte URLs depuis mcp.so
    ↓
Phase 3: Scraping + Enrichissement par serveur
    ├─ Scrape page serveur (mcp.so)
    ├─ Enrichissement GitHub (si URL GitHub trouvée)
    ├─ Enrichissement npm (si package npm trouvé)
    ├─ Parsing README (extraction config + env vars)
    └─ Sauvegarde en base de données
    ↓
Phase 4: Statistiques et rapports
```

---

## 3. Flow de Données Complet

### Voyage d'une Donnée : De la Source à la Base

```
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: COLLECTE URLS                                          │
└─────────────────────────────────────────────────────────────────┘
mcp.so/servers
    ↓ [Playwright scraping avec pagination]
Liste d'URLs: ['mcp.so/servers/gitlab', 'mcp.so/servers/brave-search', ...]

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: SCRAPING SERVEUR                                       │
└─────────────────────────────────────────────────────────────────┘
mcp.so/servers/gitlab
    ↓ [Playwright extraction]
Données brutes: {
    name: "GitLab MCP Server",
    slug: "gitlab",
    description: "Interact with GitLab API",
    github_url: "https://github.com/modelcontextprotocol/servers/tree/main/src/gitlab",
    npm_url: "@modelcontextprotocol/server-gitlab",
    tags: ["version-control", "api"]
}

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: ENRICHISSEMENT GITHUB                                  │
└─────────────────────────────────────────────────────────────────┘
github_url
    ↓ [GitHub API v3 - 7 requêtes parallèles]
    ├─ GET /repos/{owner}/{repo} → stars, forks, watchers, topics
    ├─ GET /repos/{owner}/{repo}/readme → README.md (base64)
    ├─ GET /repos/{owner}/{repo}/languages → {Python: 50%, JS: 30%}
    ├─ GET /repos/{owner}/{repo}/contributors → Top 10
    ├─ GET /repos/{owner}/{repo}/releases/latest → v1.2.3
    ├─ GET /repos/{owner}/{repo}/commits?since=30d → 45 commits
    └─ GET /repos/{owner}/{repo}/community/profile → README✅, LICENSE✅
    ↓
Données enrichies: {
    github_stars: 1234,
    github_forks: 56,
    primary_language: "Python",
    github_topics: ["mcp", "gitlab", "api"],
    github_health_score: 85,
    readme_content: "# GitLab MCP Server\n\n...",
    ...
}

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4: ENRICHISSEMENT NPM                                     │
└─────────────────────────────────────────────────────────────────┘
npm_package_name
    ↓ [npm Registry API]
    ├─ GET /{package} → version, license, repository
    └─ GET /api/npmjs.org/downloads/point/last-week/{pkg} → 1250/week
    ↓
Données npm: {
    npm_version: "1.0.3",
    npm_downloads_weekly: 1250,
    npm_license: "MIT",
    ...
}

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5: PARSING README                                         │
└─────────────────────────────────────────────────────────────────┘
readme_content
    ↓ [ReadmeParser.parse_all()]
    ├─ extract_installation_config()
    │  ├─ Pattern 1: JSON config blocks → {"command": "npx", "args": [...]}
    │  ├─ Pattern 2: git clone + install
    │  ├─ Pattern 3: npx/npm commands
    │  └─ Pattern 4: docker run
    └─ extract_environment_variables()
       └─ GITLAB_TOKEN, GITLAB_URL, etc.
    ↓
Config extracted: {
    installation_config: {
        type: "npm",
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-gitlab"],
        runtime: "node"
    },
    env_required: ["GITLAB_TOKEN", "GITLAB_URL"],
    env_descriptions: {
        "GITLAB_TOKEN": "GitLab personal access token",
        ...
    }
}

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 6: EXTRACTION TOOLS                                       │
└─────────────────────────────────────────────────────────────────┘
readme_content
    ↓ [ToolsParser.parse_tools()]
    ├─ Strategy 1: Extraction section "Available Tools"
    │  └─ Pattern: ### **tool_name** - description
    ├─ Strategy 2: JSON schema code blocks
    └─ Strategy 3: Headings pattern matching
    ↓
Tools extracted: [
    {
        name: "get_repository",
        display_name: "Get Repository",
        description: "Fetches information about a GitLab repository",
        input_schema: {...}
    },
    {
        name: "create_merge_request",
        ...
    }
]

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 7: EXTRACTION PARAMETERS                                  │
└─────────────────────────────────────────────────────────────────┘
tool_documentation
    ↓ [ParametersParser.parse_parameters()]
    ├─ Pattern 1: - `name` (type, optional): description
    ├─ Pattern 2: - `name` - description (required)
    └─ Pattern 3: **Arguments:** list
    ↓
Parameters extracted: [
    {
        name: "project_id",
        type: "string",
        description: "GitLab project ID",
        required: true
    },
    {
        name: "branch",
        type: "string",
        description: "Branch name",
        required: false,
        default: "main"
    }
]

┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 8: SAUVEGARDE DATABASE                                    │
└─────────────────────────────────────────────────────────────────┘
All parsed data
    ↓ [save_enriched_server() - Transaction]
    ├─ INSERT INTO servers (...) → server_id
    ├─ INSERT INTO markdown_content (...) → liens vers server_id
    ├─ INSERT INTO github_info (...) → server_id FK
    ├─ INSERT INTO npm_info (...) → server_id FK
    ├─ INSERT INTO mcp_config_npm (...) → server_id FK
    ├─ INSERT INTO tags + server_tags (M2M)
    ├─ INSERT INTO tools (...) → tool_id
    └─ INSERT INTO tool_parameters (...) → tool_id FK
    ↓
Database committed ✅
```

---

## 4. Modules et Composants

### 4.1 Scrapers (`src/scrapers/`)

#### **BaseScraper** (`base_scraper.py`, 287 lignes)

**Rôle** : Classe de base pour le scraping avec Playwright, avec mesures anti-détection.

**Utilisation** :
```python
async with BaseScraper(headless=True) as scraper:
    await scraper.navigate("https://mcp.so/servers")
    html = await scraper.get_html()
    links = await scraper.get_all_hrefs("a.server-link")
```

**Méthodes Clés** :

| Méthode | Description | Retour |
|---------|-------------|--------|
| `start()` | Lance le navigateur Playwright | None |
| `navigate(url)` | Navigue vers une URL avec timeout | None |
| `get_html()` | Récupère le HTML de la page actuelle | str |
| `get_text(selector)` | Extrait le texte d'un sélecteur CSS | str |
| `get_all_hrefs(selector)` | Extrait tous les liens | List[str] |
| `wait_for_selector(selector)` | Attend l'apparition d'un élément | None |
| `evaluate(script)` | Exécute du JavaScript | Any |
| `close()` | Ferme le navigateur | None |

**Anti-Détection** :
- User-agents aléatoires (5 variants)
- Viewports personnalisés
- Script d'init cachant `navigator.webdriver`
- Flags: `--disable-blink-features=AutomationControlled`

---

### 4.2 Enrichers (`src/enrichers/`)

#### **GitHubEnricher** (`github_enricher.py`, 578 lignes)

**Rôle** : Enrichissement via GitHub REST API v3.

**Authentification** : Utilise `GITHUB_TOKEN` depuis `config/.env`
**Rate Limit** : 5000 req/heure (authentifié) vs 60/heure (non-auth)

**Méthodes API** :

| Méthode | Endpoint GitHub | Données Récupérées |
|---------|----------------|-------------------|
| `fetch_repository_info()` | `/repos/{owner}/{repo}` | stars, forks, watchers, topics, language, created_at, updated_at, archived |
| `fetch_readme()` | `/repos/{owner}/{repo}/readme` | README.md décodé (base64) |
| `fetch_languages()` | `/repos/{owner}/{repo}/languages` | Distribution langage {Python: 50000, JS: 30000} |
| `fetch_contributors()` | `/repos/{owner}/{repo}/contributors` | Top 10 contributeurs |
| `fetch_latest_release()` | `/repos/{owner}/{repo}/releases/latest` | Version, release notes, date |
| `fetch_commits_activity()` | `/repos/{owner}/{repo}/commits?since=30d` | Nombre de commits derniers 30j |
| `fetch_community_files()` | `/repos/{owner}/{repo}/community/profile` | Présence README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT |

**Health Score** (0-100) :
```python
def calculate_health_score(repo_info) -> int:
    score = 0
    score += min(repo_info['stars'] / 10, 20)      # Max 20 pts
    score += min(repo_info['commit_frequency'] * 2, 20)  # Max 20 pts
    score += repo_info['community_files_count'] * 5    # Max 20 pts (4 files)
    score += min(repo_info['contributors_count'] * 3, 15)  # Max 15 pts
    score += 10 if repo_info['has_recent_release'] else 0  # 10 pts
    score += 10 if not repo_info['archived'] else 0       # 10 pts
    return min(int(score), 100)
```

**Utilisation** :
```python
async with GitHubEnricher(token=GITHUB_TOKEN) as enricher:
    data = await enricher.fetch_comprehensive_info("modelcontextprotocol", "servers")
    # Retourne: dict avec 20+ champs
```

#### **NpmEnricher** (`npm_enricher.py`, 245 lignes)

**Rôle** : Enrichissement via npm Registry API.

**Endpoints** :
- `https://registry.npmjs.org/{package}` - Métadonnées package
- `https://api.npmjs.org/downloads/point/last-week/{package}` - Statistiques téléchargement

**Données Récupérées** :
- Version actuelle
- License (SPDX)
- Repository URL (GitHub généralement)
- Téléchargements hebdo/mensuels
- Date dernière publication
- Homepage

**Utilisation** :
```python
npm_enricher = NpmEnricher()
data = await npm_enricher.fetch_package_info("@modelcontextprotocol/server-gitlab")
# Retourne: {npm_version, npm_downloads_weekly, npm_license, ...}
```

---

### 4.3 Parsers (`src/parsers/`)

#### **ReadmeParser** (`readme_parser.py`, 496 lignes)

**Rôle** : Extraction de la configuration d'installation et des variables d'environnement depuis README.md.

**Méthodes Principales** :

| Méthode | Priorité | Pattern Recherché | Exemple Output |
|---------|----------|-------------------|----------------|
| `_extract_json_config_blocks()` | Phase 1 | `{"mcpServers": {...}}` | Config JSON complet |
| `_extract_git_clone_install()` | Phase 2 | `git clone URL` + `npm install` | {type: "git", url, install_cmd} |
| `_extract_npm_config()` | Phase 3 | `npx @org/package` | {command: "npx", args: [...]} |
| `_extract_python_config()` | Phase 3 | `pip install package` | {command: "pip", args: [...]} |
| `_extract_docker_config()` | Phase 5 | `docker run -p 8080 image` | {image, ports, volumes} |
| `extract_environment_variables()` | Sec. | Section "Environment" | {env_vars: [], env_desc: {}} |

**Patterns de Configuration Supportés** :

1. **JSON Config Blocks** (Priorité 1)
```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_TOKEN": "your-token"
      }
    }
  }
}
```

2. **Git Clone + Install** (Priorité 2)
```bash
git clone https://github.com/org/repo
cd repo
npm install
```

3. **NPM Direct** (Priorité 3)
```bash
npx -y @modelcontextprotocol/server-gitlab
```

4. **Python/pip** (Priorité 3)
```bash
pip install mcp-server-gitlab
python -m mcp_server_gitlab
```

5. **Docker** (Priorité 5)
```bash
docker run -p 8080:8080 org/mcp-gitlab
```

**Extraction Variables d'Environnement** :
```python
# Recherche sections avec keywords: "environment", "configuration", "env vars"
# Patterns détectés:
# - VARIABLE_NAME: description
# - VARIABLE_NAME (required): description
# - export VARIABLE_NAME=value
```

#### **ToolsParser** (`tools_parser.py`, 370 lignes)

**Rôle** : Extraction des outils (tools) depuis README.

**Stratégies Multi-Patterns** :

**Stratégie 1** : Section "Available Tools"
```markdown
## Available Tools

### **get_repository**
Fetches information about a GitLab repository.

### **create_merge_request**
Creates a new merge request.
```

**Stratégie 2** : JSON Schema
```json
{
  "tools": [
    {
      "name": "get_repository",
      "description": "Fetches repo info",
      "inputSchema": {...}
    }
  ]
}
```

**Stratégie 3** : Headings Pattern
```markdown
### `get_repository` / `list_branches`
```

**Stratégie 4** : Markdown Lists
```markdown
- `get_repository` - Fetches repository information
- `create_merge_request` - Creates a merge request
```

**Stratégie 5** : Tables
```markdown
| Tool | Description |
|------|-------------|
| `get_repository` | Fetches repo info |
```

**Output** :
```python
[
    {
        "name": "get_repository",
        "display_name": "Get Repository",
        "description": "Fetches information about a GitLab repository",
        "input_schema": {...}  # Si trouvé dans JSON
    }
]
```

#### **ParametersParser** (`parameters_parser.py`, 348 lignes)

**Rôle** : Extraction des paramètres de chaque tool.

**Patterns Supportés** :

**Pattern 1 - Détaillé** (playwright-mcp style)
```markdown
- `project_id` (string, required): GitLab project ID
- `branch` (string, optional): Branch name (default: main)
```

**Pattern 2 - Simple** (jina-mcp style)
```markdown
- `url` - URL to scrape (required)
- `format` - Output format: markdown or html (optional)
```

**Pattern 3 - Arguments Section**
```markdown
**Arguments:**
- project_id: Project identifier
- branch: Git branch
```

**Pattern 4 - JSON Examples**
```json
{
  "project_id": "123",
  "branch": "main"
}
```
→ Infère les types depuis les valeurs

**Output** :
```python
[
    {
        "name": "project_id",
        "type": "string",
        "description": "GitLab project ID",
        "required": True,
        "default": None,
        "example": "123"
    }
]
```

---

### 4.4 Database Models (`src/database/models_normalized.py`, 685 lignes)

Voir section [5. Base de Données](#5-base-de-données) pour le schéma complet.

---

### 4.5 Scripts Pipeline (`scripts/pipeline/`)

#### **scrape_full_pipeline.py** (365 lignes)

**Le chef d'orchestre** - Coordonne toutes les phases.

**Structure** :
```python
async def main():
    # Phase 1: Clean database
    clean_database()

    # Phase 2: Collect server URLs from mcp.so
    urls = await scrape_server_list()

    # Phase 3: Process each server
    for url in urls:
        # 3a. Scrape basic info
        data = await scrape_single_server(scraper, url)

        # 3b. Enrich with GitHub
        if data['github_url']:
            github_data = await github_enricher.fetch_comprehensive_info(...)

        # 3c. Enrich with npm
        if data['npm_url']:
            npm_data = await npm_enricher.fetch_package_info(...)

        # 3d. Parse README config
        if github_data and 'readme' in github_data:
            parser = ReadmeParser(github_data['readme']['content'])
            config_data = parser.parse_all()

        # 3e. Save to database
        save_enriched_server(session, data, github_data, npm_data, ...)

    # Phase 4: Display stats
    print_statistics(stats)
```

**Fonction Clé** : `save_enriched_server()`
```python
def save_enriched_server(session, data, github_data, npm_data, readme, config, tags_map):
    """
    Sauvegarde un serveur et toutes ses données associées.

    Transaction atomique : COMMIT si succès, ROLLBACK si erreur.

    Tables modifiées:
    - servers (INSERT)
    - markdown_content (INSERT si readme fourni)
    - github_info (INSERT si github_data fourni)
    - npm_info (INSERT si npm_data fourni)
    - mcp_config_npm (INSERT si config fourni)
    - tags + server_tags (INSERT many-to-many)
    """
    # 1. Create server
    server = Server(id=str(uuid4()), slug=data['slug'], name=data['name'], ...)
    session.add(server)
    session.flush()  # Get server.id

    # 2. Save markdown content
    if readme:
        content = MarkdownContent(
            id=str(uuid4()),
            server_id=server.id,
            content_type='readme',
            content=readme['content'],
            ...
        )
        session.add(content)

    # 3. Save GitHub info
    if github_data:
        github = GithubInfo(
            id=str(uuid4()),
            server_id=server.id,
            github_url=github_data['github_url'],
            github_stars=github_data['stars'],
            ...
        )
        session.add(github)

    # 4. Save npm info (similaire)
    # 5. Save mcp_config_npm (similaire)
    # 6. Save tags (many-to-many)

    return True
```

#### **scrape_mcp_so.py** (365 lignes)

**Scraping du marketplace mcp.so**.

**Fonctions** :
- `scrape_server_list()` : Collecte URLs via pagination
- `scrape_single_server(url)` : Scrape page serveur individuelle

**Pattern de Pagination** :
```python
async def scrape_server_list(scraper, max_urls=100):
    urls = []
    page = 1

    while len(urls) < max_urls:
        await scraper.navigate(f"https://mcp.so/servers?page={page}")
        links = await scraper.get_all_hrefs("a.server-card")

        if not links:  # No more results
            break

        urls.extend(links)
        page += 1
        await asyncio.sleep(random.uniform(3, 7))  # Anti-detection

    return urls[:max_urls]
```

#### **enrich_*.py** (6 fichiers d'enrichment)

Scripts spécialisés pour des serveurs spécifiques :
- `enrich_github_info.py` : Enrichissement GitHub batch
- `enrich_flomo.py` : Enrichissement serveur Flomo
- `enrich_perplexity.py` : Enrichissement serveur Perplexity
- `enrich_minimax.py` : Enrichissement serveur Minimax
- `enrich_serper.py` : Enrichissement serveur Serper

---

## 5. Base de Données

### Schéma Complet (11 Tables)

```sql
┌─────────────────────────────────────────────────────────────────┐
│                          SERVERS (Core)                          │
├─────────────────────────────────────────────────────────────────┤
│ id (PK) │ slug (UQ) │ name │ display_name │ tagline            │
│ short_description │ status │ verification_status │ tools_count │
│ created_at │ updated_at                                         │
└────┬────────────────────────────────────────────────────────────┘
     │
     ├─────────────────────────────────────────────────┐
     │                                                 │
     ▼                                                 ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│   MARKDOWN_CONTENT      │              │     GITHUB_INFO         │
│   (1-to-Many)           │              │     (1-to-1)            │
├─────────────────────────┤              ├─────────────────────────┤
│ server_id (FK)          │              │ server_id (FK, UQ)      │
│ content_type (about/    │              │ github_url              │
│   readme/faq/tools)     │              │ github_stars            │
│ content (TEXT)          │              │ github_forks            │
│ word_count              │              │ github_health_score     │
│ UQ(server_id,           │              │ primary_language        │
│    content_type)        │              │ github_topics (JSON)    │
└─────────────────────────┘              │ last_synced_at          │
                                         └─────────────────────────┘
     │
     ├─────────────────────────────────────────────────┐
     │                                                 │
     ▼                                                 ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│       NPM_INFO          │              │   MCP_CONFIG_NPM        │
│       (1-to-1)          │              │   (1-to-1)              │
├─────────────────────────┤              ├─────────────────────────┤
│ server_id (FK, UQ)      │              │ server_id (FK, UQ)      │
│ npm_package             │              │ command (npx/npm/node)  │
│ npm_version             │              │ args (JSON array)       │
│ npm_downloads_weekly    │              │ env_required (JSON)     │
│ npm_license             │              │ env_descriptions (JSON) │
└─────────────────────────┘              │ runtime (node/python)   │
                                         └─────────────────────────┘
     │
     └────────────────────┐
                          ▼
                ┌─────────────────────────┐
                │        TOOLS            │
                │      (1-to-Many)        │
                ├─────────────────────────┤
                │ server_id (FK)          │
                │ name (snake_case)       │
                │ display_name            │
                │ description             │
                │ input_schema (JSON)     │
                │ is_dangerous            │
                │ requires_auth           │
                │ UQ(server_id, name)     │
                └────┬────────────────────┘
                     │
                     ▼
           ┌─────────────────────────┐
           │   TOOL_PARAMETERS       │
           │   (Many per Tool)       │
           ├─────────────────────────┤
           │ tool_id (FK)            │
           │ name                    │
           │ type (string/int/etc.)  │
           │ description             │
           │ required (boolean)      │
           │ default_value (JSON)    │
           │ example_value (JSON)    │
           └─────────────────────────┘

     ┌─────────────── Many-to-Many ────────────────┐
     │                                              │
     ▼                                              ▼
┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│ CATEGORIES   │◄──►│SERVER_CATEGORIES│    │    TAGS      │
├──────────────┤    ├────────────────┤    ├──────────────┤
│ slug (UQ)    │    │ server_id (FK) │    │ slug (UQ)    │
│ name (UQ)    │    │ category_id(FK)│    │ name (UQ)    │
│ server_count │    │ PK(server_id,  │    │ server_count │
└──────────────┘    │    category_id)│    └──────────────┘
                    └────────────────┘
                             ▲
                             │
                    ┌────────────────┐
                    │  SERVER_TAGS   │
                    ├────────────────┤
                    │ server_id (FK) │
                    │ tag_id (FK)    │
                    │ PK(server_id,  │
                    │    tag_id)     │
                    └────────────────┘
```

### Tables Détaillées

#### **servers**
```sql
CREATE TABLE servers (
    id VARCHAR(36) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    tagline TEXT,
    short_description TEXT,
    status VARCHAR(20) CHECK(status IN ('approved', 'pending', 'rejected')) DEFAULT 'approved',
    verification_status VARCHAR(20) CHECK(verification_status IN ('verified', 'unverified')) DEFAULT 'unverified',
    creator_name TEXT,
    tools_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_servers_slug ON servers(slug);
CREATE INDEX idx_servers_status ON servers(status);
CREATE INDEX idx_servers_updated_at ON servers(updated_at DESC);
```

#### **markdown_content**
```sql
CREATE TABLE markdown_content (
    id VARCHAR(36) PRIMARY KEY,
    server_id VARCHAR(36) NOT NULL,
    content_type VARCHAR(20) CHECK(content_type IN ('about', 'readme', 'faq', 'tools')) NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER,
    estimated_reading_time_minutes INTEGER,
    extracted_from TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE (server_id, content_type)
);
```

#### **github_info**
```sql
CREATE TABLE github_info (
    id VARCHAR(36) PRIMARY KEY,
    server_id VARCHAR(36) UNIQUE NOT NULL,
    github_url TEXT NOT NULL,
    github_owner TEXT,
    github_repo TEXT,
    github_stars INTEGER DEFAULT 0,
    github_forks INTEGER DEFAULT 0,
    github_watchers INTEGER DEFAULT 0,
    github_last_commit DATETIME,
    commit_frequency INTEGER,
    primary_language TEXT,
    languages TEXT,  -- JSON: {Python: 50000, JS: 30000}
    github_topics TEXT,  -- JSON array
    github_health_score INTEGER,
    has_readme INTEGER DEFAULT 0,
    has_license INTEGER DEFAULT 0,
    has_contributing INTEGER DEFAULT 0,
    github_created_at DATETIME,
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);
```

#### **tools**
```sql
CREATE TABLE tools (
    id VARCHAR(36) PRIMARY KEY,
    server_id VARCHAR(36) NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    input_schema TEXT,  -- JSON Schema
    example_usage TEXT,
    example_response TEXT,
    is_dangerous INTEGER DEFAULT 0,
    requires_auth INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE (server_id, name)
);
```

#### **tool_parameters**
```sql
CREATE TABLE tool_parameters (
    id VARCHAR(36) PRIMARY KEY,
    tool_id VARCHAR(36) NOT NULL,
    name TEXT NOT NULL,
    type TEXT,  -- string, integer, array, object
    description TEXT,
    required INTEGER DEFAULT 0,
    default_value TEXT,  -- JSON string
    example_value TEXT,  -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);
```

---

## 6. Interactions entre Fichiers

### Graphe d'Import

```
scrape_full_pipeline.py (365L)
├─ IMPORTS
│  ├─ src.database.models_normalized
│  │  └─ Server, GithubInfo, NpmInfo, MarkdownContent, McpConfigNpm, Tag, ServerTag
│  ├─ src.enrichers.github_enricher
│  │  └─ GitHubEnricher (async class)
│  ├─ src.enrichers.npm_enricher
│  │  └─ NpmEnricher (async class)
│  ├─ src.parsers.readme_parser
│  │  └─ ReadmeParser (class)
│  ├─ scripts.pipeline.scrape_mcp_so
│  │  └─ scrape_server_list(), scrape_single_server()
│  └─ scripts.config
│     └─ PHASE1_CONFIG, PHASE2_CONFIG
│
└─ CALLS
   ├─ clean_database() → scripts/clean_database.py
   ├─ scrape_server_list() → scrape_mcp_so.py
   ├─ scrape_single_server() → scrape_mcp_so.py
   ├─ github_enricher.fetch_comprehensive_info() → GitHubEnricher
   ├─ npm_enricher.fetch_package_info() → NpmEnricher
   ├─ readme_parser.parse_all() → ReadmeParser
   └─ save_enriched_server() → INSERTS en base

scrape_mcp_so.py (365L)
├─ IMPORTS
│  ├─ src.scrapers.base_scraper
│  │  └─ BaseScraper (async class)
│  ├─ src.parsers.tools_parser
│  │  └─ ToolsParser (class)
│  ├─ src.parsers.parameters_parser
│  │  └─ ParametersParser (class)
│  └─ src.database.models_normalized
│     └─ Server, Tool, ToolParameter
│
└─ USES
   ├─ BaseScraper.navigate() → Playwright page.goto()
   ├─ BaseScraper.get_all_hrefs() → page.query_selector_all()
   └─ ToolsParser.parse_tools() → Parse README

GitHubEnricher (src/enrichers/github_enricher.py, 578L)
├─ IMPORTS
│  ├─ aiohttp (async HTTP client)
│  ├─ dotenv (charge config/.env)
│  └─ pathlib.Path
│
└─ USES
   ├─ aiohttp.ClientSession.get() → GitHub API
   ├─ X-RateLimit-* headers → Rate limiting
   └─ base64.b64decode() → Décodage README

ReadmeParser (src/parsers/readme_parser.py, 496L)
├─ NO EXTERNAL IMPORTS (pure Python)
└─ USES
   ├─ re.search(), re.findall() → Pattern matching
   ├─ json.loads() → Parse JSON configs
   └─ Markdown heading detection

ToolsParser (src/parsers/tools_parser.py, 370L)
├─ IMPORTS
│  └─ re (regex)
└─ USES
   ├─ Multiple regex patterns
   └─ 3 parsing strategies (section/JSON/headings)

SQLAlchemy Models (src/database/models_normalized.py, 685L)
├─ IMPORTS
│  ├─ sqlalchemy (ORM)
│  └─ datetime, uuid
└─ DEFINES
   ├─ Base = declarative_base()
   └─ 11 table classes
```

### Flux d'Appel Détaillé

```
main() @ scrape_full_pipeline.py
│
├─ Phase 1: clean_database()
│  └─ Bash call: python scripts/clean_database.py
│
├─ Phase 2: scrape_server_list()
│  └─ scrape_mcp_so.scrape_server_list()
│     └─ BaseScraper.navigate()
│        └─ Playwright async_api.chromium.launch()
│           └─ page.goto("https://mcp.so/servers")
│              └─ page.query_selector_all("a.server-card")
│
└─ Phase 3: Loop over URLs
   ├─ scrape_single_server(url)
   │  └─ scrape_mcp_so.scrape_single_server()
   │     └─ BaseScraper.navigate(url)
   │        └─ Extract: name, description, github_url, npm_url, tags
   │
   ├─ IF github_url:
   │  └─ github_enricher.fetch_comprehensive_info(owner, repo)
   │     ├─ fetch_repository_info()
   │     │  └─ aiohttp.get("https://api.github.com/repos/{owner}/{repo}")
   │     ├─ fetch_readme()
   │     │  └─ aiohttp.get("/repos/{owner}/{repo}/readme")
   │     │     └─ base64.b64decode(content)
   │     ├─ fetch_languages()
   │     ├─ fetch_contributors()
   │     ├─ fetch_latest_release()
   │     ├─ fetch_commits_activity()
   │     └─ fetch_community_files()
   │
   ├─ IF npm_url:
   │  └─ npm_enricher.fetch_package_info(package_name)
   │     ├─ aiohttp.get("https://registry.npmjs.org/{package}")
   │     └─ aiohttp.get("https://api.npmjs.org/downloads/point/last-week/{pkg}")
   │
   ├─ IF readme_content:
   │  └─ readme_parser.parse_all(readme_content)
   │     ├─ extract_installation_config()
   │     │  ├─ _extract_json_config_blocks()
   │     │  │  └─ json.loads(code_block)
   │     │  ├─ _extract_npm_config()
   │     │  │  └─ re.search(r"npx\s+(.+)")
   │     │  └─ _extract_python_config()
   │     │     └─ re.search(r"pip install (.+)")
   │     └─ extract_environment_variables()
   │        └─ re.findall(r"([A-Z_]+):\s*(.+)")
   │
   └─ save_enriched_server(data, github_data, npm_data, config)
      └─ SQLAlchemy Transaction
         ├─ session.add(Server(...))
         ├─ session.flush() → Get server_id
         ├─ session.add(MarkdownContent(server_id=...))
         ├─ session.add(GithubInfo(server_id=...))
         ├─ session.add(NpmInfo(server_id=...))
         ├─ session.add(McpConfigNpm(server_id=...))
         ├─ FOR tag IN tags:
         │  └─ session.add(ServerTag(server_id, tag_id))
         └─ session.commit()  # Atomique
```

---

## 7. Patterns de Code

### 7.1 Async Context Managers

**Pattern** : Gestion automatique de ressources avec `async with`.

```python
# Enrichers
async with GitHubEnricher(token=GITHUB_TOKEN) as enricher:
    data = await enricher.fetch_repository_info(owner, repo)
    # Auto-fermeture de la session aiohttp

# Scrapers
async with BaseScraper(headless=True) as scraper:
    await scraper.navigate(url)
    html = await scraper.get_html()
    # Auto-fermeture du navigateur Playwright

# Implémentation
class GitHubEnricher:
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
```

**Avantages** :
- Cleanup automatique (fermeture connexions)
- Gestion d'erreurs propre
- Code lisible

### 7.2 Multiple Strategy Parsing

**Pattern** : Tentatives successives avec fallbacks.

```python
class ToolsParser:
    def parse_tools(self, markdown):
        # Strategy 1: Extract "Tools" section
        tools = self._parse_tools_from_section(markdown)
        if tools:
            return tools

        # Strategy 2: Parse JSON code blocks
        tools = self._parse_tools_from_code_blocks(markdown)
        if tools:
            return tools

        # Strategy 3: Fallback - scan all headings
        tools = self._parse_tools_from_headings(markdown)
        return tools
```

**Avantages** :
- Robustesse face à différents formats
- Couverture maximale des cas
- Dégradation gracieuse

### 7.3 Transactional Database Operations

**Pattern** : Transactions atomiques avec rollback.

```python
def save_enriched_server(session, data, github_data, npm_data, ...):
    try:
        # 1. Create server
        server = Server(...)
        session.add(server)
        session.flush()  # Get ID without committing

        # 2. Create related records
        if github_data:
            github = GithubInfo(server_id=server.id, ...)
            session.add(github)

        # 3. Commit ALL or NOTHING
        session.commit()
        return True

    except Exception as e:
        session.rollback()  # Undo ALL changes
        logger.error(f"Failed: {e}")
        return False
```

**Avantages** :
- Cohérence des données garantie
- Pas d'états partiels en base
- Facilite debugging

### 7.4 Rate Limiting with Headers

**Pattern** : Respect des limites API.

```python
class GitHubEnricher:
    async def _make_request(self, url):
        async with self.session.get(url) as response:
            # Check rate limit
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

            if remaining < 10:
                wait_seconds = reset_time - time.time()
                logger.warning(f"Rate limit low. Waiting {wait_seconds}s")
                await asyncio.sleep(wait_seconds + 5)

            return await response.json()
```

**Avantages** :
- Pas de blocage API
- Scraping continu
- Respect des ToS

### 7.5 Anti-Detection Measures

**Pattern** : Comportement humain simulé.

```python
def get_random_delay(min_delay, max_delay):
    base_delay = random.uniform(min_delay, max_delay)
    jitter = random.uniform(-0.2, 0.3)  # ±20-30% variation
    return max(0.5, base_delay + jitter)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
    # 5 variants
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    # 5 variants
]

def get_random_viewport():
    return random.choice(VIEWPORT_SIZES)
```

**Utilisé par** : BaseScraper, config.py

### 7.6 Exponential Backoff Retry

**Pattern** : Retry avec délai exponentiel.

```python
def calculate_backoff_delay(attempt, base_delay, max_delay):
    """
    Exponential: delay = base * (2 ^ attempt)
    With jitter: ±20%
    """
    delay = base_delay * (2 ** attempt)
    delay = min(delay, max_delay)
    jitter = delay * random.uniform(-0.2, 0.2)
    return delay + jitter

# Usage
for attempt in range(MAX_RETRIES):
    try:
        result = await fetch_data(url)
        break
    except Exception as e:
        if attempt < MAX_RETRIES - 1:
            delay = calculate_backoff_delay(attempt, base=5.0, max=120.0)
            await asyncio.sleep(delay)
        else:
            raise
```

**Scénario** :
- Attempt 0: 5s (base)
- Attempt 1: 10s (2×5)
- Attempt 2: 20s (4×5)
- Attempt 3: 40s (8×5)
- Attempt 4: 80s (16×5)
- Attempt 5: 120s (capped)

### 7.7 Lazy Loading with flush()

**Pattern** : Obtenir l'ID sans commit.

```python
# Create server
server = Server(id=str(uuid4()), ...)
session.add(server)
session.flush()  # INSERT + get auto-generated ID

# Use server.id immediately without committing
github_info = GithubInfo(server_id=server.id, ...)
session.add(github_info)

# Commit all at once
session.commit()
```

**Avantages** :
- Relations créées avant commit
- Rollback possible si erreur ultérieure
- Performance (batch commit)

---

## 8. Configuration et Anti-Détection

### Configuration Centralisée (`scripts/config.py`)

**PHASE1_CONFIG** (Collecte URLs)
```python
{
    'TARGET_URLS': 100,                # Nombre d'URLs à collecter
    'MAX_PAGES': 50,                   # Pages max de pagination
    'DELAY_BETWEEN_PAGES_MIN': 3.0,    # Délai min entre pages (s)
    'DELAY_BETWEEN_PAGES_MAX': 7.0,    # Délai max entre pages (s)
    'INITIAL_PAGE_WAIT': 5.0,          # Attente initiale JS render
    'PAGE_LOAD_WAIT': 3.0,             # Attente chargement page
    'MAX_PAGE_RETRIES': 3,             # Retry si échec
    'RETRY_DELAY_BASE': 5.0,           # Base délai retry
    'RETRY_DELAY_MAX': 60.0,           # Max délai retry
    'BATCH_SIZE': 50,                  # Taille batch DB
    'EMPTY_PAGE_THRESHOLD': 3,         # Pages vides avant stop
    'HEADLESS': True,                  # Mode headless
    'TIMEOUT': 30000,                  # Timeout page (ms)
    'ROTATE_USER_AGENT': True,         # Rotation user-agent
    'RANDOM_VIEWPORT': True,           # Viewport aléatoire
    'SIMULATE_HUMAN': True,            # Comportement humain
}
```

**PHASE2_CONFIG** (Scraping serveurs)
```python
{
    'BATCH_SIZE': 10,
    'MAX_RETRIES': 3,
    'DELAY_BETWEEN_URLS_MIN': 2.0,
    'DELAY_BETWEEN_URLS_MAX': 5.0,
    'DELAY_BETWEEN_BATCHES_MIN': 10.0,
    'DELAY_BETWEEN_BATCHES_MAX': 20.0,
    'INITIAL_PAGE_WAIT': 4.0,
    'RETRY_DELAY_BASE': 10.0,
    'RETRY_DELAY_MAX': 120.0,
    'HEADLESS': True,
    'TIMEOUT': 30000,
    'PARALLEL_WORKERS': 1,             # 1 pour sécurité
    'ROTATE_USER_AGENT': True,
    'RANDOM_VIEWPORT': True,
    'SIMULATE_HUMAN': True,
}
```

**Scénarios Prédéfinis** :
- `dev` : 10 serveurs, rapide (test)
- `production_100` : 100 serveurs, équilibré
- `production_1000` : 1000 serveurs, modéré
- `production_10000` : 10000 serveurs, agressif mais safe

```python
phase1, phase2 = apply_scenario('production_100')
```

### Mesures Anti-Détection

**1. Rotation User-Agent** :
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 ... Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...',
]
```

**2. Viewports Aléatoires** :
```python
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},  # Full HD
    {'width': 1366, 'height': 768},   # Laptop commun
    {'width': 1536, 'height': 864},   # Laptop
    {'width': 1440, 'height': 900},   # MacBook
    {'width': 1280, 'height': 720},   # HD
]
```

**3. Délais Aléatoires** :
```python
def get_random_delay(min_delay, max_delay):
    base_delay = random.uniform(min_delay, max_delay)
    jitter = random.uniform(-0.2, 0.3)  # Variation humaine
    return max(0.5, base_delay + jitter)
```

**4. Playwright Hardening** :
```python
browser = await playwright.chromium.launch(
    headless=True,
    args=[
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
        '--disable-dev-shm-usage',
    ]
)

# Init script
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
""")
```

**5. Rate Limiting GitHub** :
```python
if remaining < 10:
    wait_seconds = reset_time - time.time()
    logger.warning(f"Rate limit: {remaining}. Waiting {wait_seconds}s")
    await asyncio.sleep(wait_seconds + 5)
```

---

## 9. Gestion d'Erreurs

### Stratégie Globale

**Principe** : **Dégradation gracieuse** - Les échecs partiels ne bloquent pas le pipeline.

### Niveaux d'Erreur

#### **Niveau 1 : Database (CRITICAL)**

Transaction atomique - **ROLLBACK si erreur**.

```python
try:
    save_enriched_server(session, data, github_data, ...)
    session.commit()  # TOUT ou RIEN
    stats['saved'] += 1
except Exception as e:
    session.rollback()  # Annule TOUTES les modifications
    stats['errors'] += 1
    logger.error(f"DB error: {e}")
    continue  # Skip au serveur suivant
```

**Comportement** : Si la sauvegarde d'un serveur échoue, le serveur est ignoré mais le pipeline continue.

#### **Niveau 2 : Enrichment (OPTIONAL)**

Échec non-bloquant - **Continuer avec None**.

```python
# GitHub enrichment
github_data = None
try:
    if data.get('github_url'):
        github_data = await github_enricher.fetch_comprehensive_info(owner, repo)
except Exception as e:
    logger.warning(f"GitHub enrichment failed: {e}")
    github_data = None  # Continue sans données GitHub

# npm enrichment
npm_data = None
try:
    if data.get('npm_url'):
        npm_data = await npm_enricher.fetch_package_info(package_name)
except Exception as e:
    logger.warning(f"npm enrichment failed: {e}")
    npm_data = None  # Continue sans données npm
```

**Comportement** : Si GitHub/npm fail, le serveur est quand même sauvegardé avec les données disponibles.

#### **Niveau 3 : Parsing (ENHANCEMENT)**

Échec non-bloquant - **Continuer sans config**.

```python
config_data = None
try:
    if readme_content:
        parser = ReadmeParser(readme_content['content'])
        config_data = parser.parse_all()
except Exception as e:
    logger.warning(f"README parsing failed: {e}")
    config_data = None  # Pas de config mais serveur sauvegardé
```

**Comportement** : Le serveur est sauvegardé même sans config d'installation extraite.

#### **Niveau 4 : Scraping (RETRY + SKIP)**

Retry avec backoff, puis skip si échec.

```python
for attempt in range(MAX_RETRIES):
    try:
        data = await scrape_single_server(scraper, url)
        break  # Success
    except Exception as e:
        if attempt < MAX_RETRIES - 1:
            delay = calculate_backoff_delay(attempt, base=5.0, max=60.0)
            logger.warning(f"Retry {attempt+1}/{MAX_RETRIES} after {delay}s")
            await asyncio.sleep(delay)
        else:
            logger.error(f"Failed after {MAX_RETRIES} attempts: {e}")
            stats['errors'] += 1
            continue  # Skip ce serveur
```

**Comportement** : 3 tentatives avec délai exponentiel, puis skip.

### Logging

**Niveaux** :
- `ERROR` : Échecs critiques (DB, scraping après retries)
- `WARNING` : Échecs non-bloquants (GitHub fail, parsing fail)
- `INFO` : Progression normale

**Exemple Log** :
```
[INFO] Processing server 45/100: gitlab
[INFO] GitHub enrichment: 1234 stars, health score 85
[WARNING] npm package not found: @modelcontextprotocol/server-gitlab
[INFO] README parsed: npx config extracted
[INFO] Saved server gitlab (7 tools, 23 parameters)
[INFO] Progress: 45/100 (45%), Saved: 44, Errors: 1
```

### Statistiques Finales

```python
stats = {
    'total': 100,
    'saved': 96,
    'errors': 4,
    'github_enriched': 92,
    'npm_enriched': 88,
    'config_extracted': 85,
    'tools_extracted': 78,
}

success_rate = (stats['saved'] / stats['total']) * 100
print(f"Success rate: {success_rate:.1f}%")
```

---

## 10. Guide Développeur

### 10.1 Setup Environnement

**1. Installation**
```bash
# Clone repo
git clone <repo-url>
cd "crawler MCPhub"

# Environnement virtuel Python
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Dépendances Python
pip install -r config/requirements.txt

# Dépendances Node.js (pour analyse TypeScript)
npm install --prefix config/
```

**2. Configuration**
```bash
# Copier template
cp config/.env.example config/.env

# Éditer config/.env
# GITHUB_TOKEN=ghp_your_token_here
# NPM_TOKEN=npm_optional_token
```

**3. Vérification**
```bash
# Test imports
python -c "from src.database.models_normalized import Base; print('OK')"

# Test Playwright
playwright install chromium

# Test base de données
ls data/mcp_servers.db  # Doit exister (7.8 MB)
```

### 10.2 Exécuter le Pipeline

**Pipeline complet** :
```bash
python scripts/pipeline/scrape_full_pipeline.py --max-servers 10
```

**Phases individuelles** :
```bash
# Phase 1: Collecte URLs
python scripts/pipeline/scrape_mcp_so.py

# Phase 2: Enrichissement GitHub
python scripts/pipeline/enrich_github_info.py

# Analyse database
node scripts/tools/analysis/analyze-database.js
```

**Avec scénarios** :
```python
# Dans le script
from scripts.config import apply_scenario

phase1, phase2 = apply_scenario('dev')  # 10 serveurs rapide
phase1, phase2 = apply_scenario('production_100')  # 100 serveurs
```

### 10.3 Ajouter un Nouveau Parser

**Exemple** : Parser pour extraire les prix depuis README.

**1. Créer le fichier** `src/parsers/pricing_parser.py`

```python
import re
from typing import Optional, Dict

class PricingParser:
    """Extract pricing information from README markdown."""

    def __init__(self, markdown_content: str):
        self.content = markdown_content

    def extract_pricing(self) -> Optional[Dict]:
        """
        Extract pricing from README.

        Patterns:
        - ## Pricing
        - $X/month
        - Free tier: ...

        Returns:
            Dict with {tier, price, currency} or None
        """
        # Find "Pricing" section
        pricing_section = self._find_section(['pricing', 'cost', 'price'])
        if not pricing_section:
            return None

        # Extract price pattern: $X/month, €X/mo, etc.
        pattern = r'([€$£])(\d+(?:\.\d{2})?)\s*/\s*(month|mo|year|yr)'
        match = re.search(pattern, pricing_section, re.IGNORECASE)

        if match:
            return {
                'currency': match.group(1),
                'amount': float(match.group(2)),
                'period': match.group(3).lower(),
                'tier': 'paid'
            }

        # Check for "free" mentions
        if re.search(r'\bfree\b', pricing_section, re.IGNORECASE):
            return {
                'currency': None,
                'amount': 0,
                'period': None,
                'tier': 'free'
            }

        return None

    def _find_section(self, keywords):
        """Find section by keywords (same as ReadmeParser)."""
        for keyword in keywords:
            pattern = rf'^#+\s*{keyword}.*?(?=^#+|\Z)'
            match = re.search(pattern, self.content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                return match.group(0)
        return None
```

**2. Ajouter table database** `src/database/models_normalized.py`

```python
class PricingInfo(Base):
    __tablename__ = 'pricing_info'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), unique=True, nullable=False)
    tier = Column(String(20))  # 'free', 'paid', 'freemium'
    currency = Column(String(3))  # 'USD', 'EUR', 'GBP'
    amount = Column(Float)
    period = Column(String(10))  # 'month', 'year'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    server = relationship('Server', backref='pricing')
```

**3. Intégrer dans pipeline** `scripts/pipeline/scrape_full_pipeline.py`

```python
from src.parsers.pricing_parser import PricingParser

# Dans la boucle de traitement
if readme_content:
    # Existing parsers
    readme_parser = ReadmeParser(readme_content['content'])
    config_data = readme_parser.parse_all()

    # NEW: Pricing parser
    pricing_parser = PricingParser(readme_content['content'])
    pricing_data = pricing_parser.extract_pricing()

# Dans save_enriched_server()
if pricing_data:
    pricing = PricingInfo(
        id=str(uuid4()),
        server_id=server.id,
        tier=pricing_data['tier'],
        currency=pricing_data.get('currency'),
        amount=pricing_data.get('amount'),
        period=pricing_data.get('period')
    )
    session.add(pricing)
```

**4. Migration database**

```bash
# Créer migration
# migrations/schema/006_add_pricing_info.sql
CREATE TABLE pricing_info (
    id VARCHAR(36) PRIMARY KEY,
    server_id VARCHAR(36) UNIQUE NOT NULL,
    tier VARCHAR(20),
    currency VARCHAR(3),
    amount REAL,
    period VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);
```

**5. Tester**

```python
# Test unitaire
def test_pricing_parser():
    readme = """
    ## Pricing

    This service costs $10/month for the pro plan.
    Free tier available with limited features.
    """
    parser = PricingParser(readme)
    pricing = parser.extract_pricing()

    assert pricing['currency'] == '$'
    assert pricing['amount'] == 10.0
    assert pricing['period'] == 'month'
```

### 10.4 Debugging

**Logging détaillé** :
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspecting database** :
```bash
sqlite3 data/mcp_servers.db
.tables
.schema servers
SELECT * FROM servers LIMIT 5;
```

**Playwright debugging (UI visible)** :
```python
scraper = BaseScraper(headless=False)  # Voir le navigateur
await scraper.navigate(url)
await asyncio.sleep(10)  # Observer manuellement
```

**Profiling performance** :
```python
import time

start = time.time()
await github_enricher.fetch_repository_info(owner, repo)
elapsed = time.time() - start
print(f"GitHub enrichment: {elapsed:.2f}s")
```

### 10.5 Tests (À Implémenter)

**Structure suggérée** :
```
tests/
├── unit/
│   ├── test_readme_parser.py
│   ├── test_tools_parser.py
│   ├── test_parameters_parser.py
│   └── test_github_enricher.py
└── integration/
    ├── test_full_pipeline.py
    └── test_database_persistence.py
```

**Exemple test** :
```python
# tests/unit/test_readme_parser.py
import pytest
from src.parsers.readme_parser import ReadmeParser

def test_extract_npm_config():
    readme = """
    ## Installation

    ```bash
    npx -y @modelcontextprotocol/server-gitlab
    ```
    """
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()

    assert config is not None
    assert config['type'] == 'npm'
    assert config['command'] == 'npx'
    assert '-y' in config['args']
    assert '@modelcontextprotocol/server-gitlab' in config['args']

def test_extract_env_vars():
    readme = """
    ## Configuration

    - GITLAB_TOKEN: Your GitLab personal access token
    - GITLAB_URL: GitLab instance URL (optional)
    """
    parser = ReadmeParser(readme)
    result = parser.extract_environment_variables()

    assert 'GITLAB_TOKEN' in result['env_required']
    assert 'GITLAB_URL' in result['env_required']
    assert 'GitLab personal access token' in result['env_descriptions']['GITLAB_TOKEN']
```

---

## Annexes

### A. Commandes Utiles

```bash
# Compter lignes de code
find src/ scripts/ -name "*.py" | xargs wc -l

# Lister tous les imports
grep -r "^import\|^from" src/ scripts/ | sort | uniq

# Analyser taille base de données
du -h data/mcp_servers.db

# Compter serveurs en base
sqlite3 data/mcp_servers.db "SELECT COUNT(*) FROM servers;"

# Serveurs avec le plus de tools
sqlite3 data/mcp_servers.db "SELECT name, tools_count FROM servers ORDER BY tools_count DESC LIMIT 10;"

# Requête GitHub health scores
sqlite3 data/mcp_servers.db "SELECT s.name, g.github_stars, g.github_health_score FROM servers s JOIN github_info g ON s.id = g.server_id ORDER BY g.github_health_score DESC LIMIT 10;"
```

### B. Ressources Externes

**APIs** :
- GitHub REST API: https://docs.github.com/en/rest
- npm Registry API: https://github.com/npm/registry/blob/master/docs/REGISTRY-API.md
- Playwright Python: https://playwright.dev/python/docs/intro

**Documentation** :
- SQLAlchemy: https://docs.sqlalchemy.org/
- aiohttp: https://docs.aiohttp.org/
- MCP Specification: https://modelcontextprotocol.io/

### C. Glossaire

| Terme | Définition |
|-------|------------|
| **MCP** | Model Context Protocol - Protocol pour connecter LLMs aux outils externes |
| **Server** | Serveur MCP fournissant des tools/resources |
| **Tool** | Fonction exposée par un serveur MCP (ex: get_repository) |
| **Parameter** | Argument d'un tool (ex: project_id) |
| **Enrichment** | Ajout de métadonnées depuis sources externes (GitHub, npm) |
| **Scraping** | Extraction automatique de données depuis pages web |
| **ORM** | Object-Relational Mapping (SQLAlchemy) |
| **Async** | Programmation asynchrone (asyncio, aiohttp) |
| **Health Score** | Score 0-100 évaluant la qualité d'un repository GitHub |

---

## Conclusion

Cette documentation couvre l'architecture complète du MCP Hub Crawler. Pour aller plus loin :

1. **Lire le code** : Les fichiers sont bien commentés
2. **Suivre les imports** : Comprendre les dépendances
3. **Tester localement** : Exécuter le pipeline avec 10 serveurs
4. **Consulter les logs** : Observer le flow en temps réel
5. **Examiner la base** : Requêtes SQL pour comprendre les données

**Questions ?** Consultez :
- `docs/PROJECT_STRUCTURE.md` - Structure du projet
- `scripts/README.md` - Guide des scripts
- `DATABASE.md` - Schéma de base de données
- `CLAUDE.md` - Workflow de développement

---

**Dernière mise à jour** : 21 Novembre 2025
**Auteur** : Documentation générée avec Claude Code
