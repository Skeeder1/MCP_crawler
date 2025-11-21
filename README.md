# 🤖 MCP Servers Auto-Collector

> Système automatisé en Python pour collecter et enrichir les métadonnées de 100+ serveurs MCP (Model Context Protocol).

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Vue d'Ensemble

Ce projet collecte automatiquement les métadonnées de tous les serveurs MCP officiels depuis:
- 🐙 [GitHub modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
- 🌐 [MCP Registry API](https://registry.modelcontextprotocol.io)
- 📦 npm Registry
- ⭐ GitHub API

**Résultat**: Fichier JSON structuré contenant 100+ serveurs MCP enrichis avec:
- Métadonnées GitHub (stars, commits, etc.)
- Versions npm et statistiques de téléchargement
- Configuration MCP extraite automatiquement
- Catégorisation et tags intelligents
- Score de qualité et complétude

---

## 🚀 Démarrage Rapide (5 minutes)

### Prérequis

- Python 3.10 ou supérieur
- Git
- Token GitHub (pour API)

### Installation

```bash
# 1. Cloner le repo
git clone <votre-repo>
cd mcp-collector

# 2. Créer environnement virtuel
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Configurer variables d'environnement
cp .env.example .env

# Éditer .env et ajouter votre GITHUB_TOKEN
# Obtenir un token: https://github.com/settings/tokens
```

### Configuration `.env`

```bash
# === REQUIS ===
GITHUB_TOKEN=ghp_votre_token_ici

# === OPTIONNEL ===
NPM_TOKEN=npm_votre_token
LOG_LEVEL=INFO
ENABLE_CACHE=true
```

### Exécution

```bash
# Phase 0: Validation de l'environnement
python scripts/phase0_setup.py

# Phase 1: Collecte initiale (15-25 min)
python scripts/phase1_collect.py

# Phase 2: Enrichissement (20-40 min)
python scripts/phase2_enrich.py

# Phase 3: Validation et export (5-10 min)
python scripts/phase3_validate.py

# Résultat final: data/mcp-servers.json ✨
```

---

## 📁 Structure du Projet

```
mcp-collector/
├── README.md                        # Ce fichier
├── MCP_MASTER_PLAN.md              # Plan détaillé complet
├── PYTHON_VS_JS_COMPARISON.md      # Pourquoi Python?
├── requirements.txt                # Dépendances Python
├── .env.example                    # Template config
│
├── scripts/                        # Scripts d'exécution
│   ├── phase0_setup.py            # Validation environnement
│   ├── phase1_collect.py          # Collecte initiale
│   ├── phase2_enrich.py           # Enrichissement
│   ├── phase3_validate.py         # Validation finale
│   ├── phase4_update.py           # Mise à jour quotidienne
│   └── dev_test.py                # Test avec 5 serveurs
│
├── src/                            # Code source
│   ├── collectors/                # Collecteurs de données
│   ├── parsers/                   # Parsers (README, package.json)
│   ├── processors/                # Processeurs (normalisation, etc.)
│   ├── validators/                # Validateurs (Pydantic)
│   ├── models/                    # Modèles de données
│   └── utils/                     # Utilitaires
│
└── data/                          # Données générées
    ├── mcp-servers.json           # 🎯 RÉSULTAT FINAL
    ├── validation-report.json     # Rapport de qualité
    ├── changelog.md               # Historique des changements
    ├── backups/                   # Sauvegardes quotidiennes
    ├── cache/                     # Cache HTTP
    └── logs/                      # Logs d'exécution
```

---

## 📊 Exemple de Résultat

`data/mcp-servers.json`:

```json
{
  "metadata": {
    "generated_at": "2025-01-19T10:30:00Z",
    "total_servers": 103,
    "version": "2.0.0"
  },
  "servers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "slug": "railway-mcp",
      "name": "Railway",
      "display_name": "Railway MCP Server",
      "tagline": "Deploy applications to Railway from Claude",
      "short_description": "Deploy, manage and monitor your Railway applications...",
      "logo_url": "https://cdn.mcpspot.com/logos/railway.svg",

      "github_url": "https://github.com/jasontanswe/railway-mcp",
      "github_stars": 234,
      "github_last_commit": "2025-01-15T14:30:00Z",

      "npm_package": "@jasontanswe/railway-mcp",
      "npm_version": "1.2.3",

      "categories": ["infrastructure", "deployment"],
      "tags": ["railway", "hosting", "docker"],

      "mcp_config": {
        "runtime": "node",
        "command": "npx",
        "args": ["-y", "@jasontanswe/railway-mcp"],
        "env_required": ["RAILWAY_TOKEN"]
      },

      "tools_count": 8,
      "install_count": 1250,
      "status": "approved"
    }
  ]
}
```

---

## 🎯 Phases d'Exécution

| Phase | Durée | Description | Sortie |
|-------|-------|-------------|--------|
| **0. Setup** | 5 min | Validation environnement | ✅ Env valide |
| **1. Collecte** | 15-25 min | Récupération données brutes | `phase1-raw.json` |
| **2. Enrichissement** | 20-40 min | GitHub API + npm API | `phase2-enriched.json` |
| **3. Validation** | 5-10 min | Validation + scoring | `mcp-servers.json` ✨ |
| **4. Mise à jour** | 10 min | Refresh quotidien | `mcp-servers.json` (màj) |

**Total**: 45-80 minutes pour 100+ serveurs

---

## 🔧 Dépendances Principales

### HTTP & Async
- `aiohttp` - Requêtes HTTP asynchrones
- `asyncio` - Orchestration concurrence
- `aiolimiter` - Rate limiting

### Parsing & Scraping
- `beautifulsoup4` + `lxml` - Parsing HTML/Markdown
- `markdown-it-py` - Parser Markdown avancé

### Validation & Typage
- `pydantic` - Validation de données avec type hints
- `pydantic-settings` - Gestion configuration

### Data Processing
- `pandas` - Manipulation datasets (optionnel mais recommandé)

### Utilities
- `loguru` - Logging élégant
- `tqdm` - Progress bars
- `tenacity` - Retry logic
- `GitPython` - Operations Git
- `python-dotenv` - Variables d'environnement

Voir `requirements.txt` pour la liste complète.

---

## 📖 Documentation

- **[MCP_MASTER_PLAN.md](MCP_MASTER_PLAN.md)** - Plan d'action complet et détaillé (recommandé de lire d'abord)
- **[PYTHON_VS_JS_COMPARISON.md](PYTHON_VS_JS_COMPARISON.md)** - Pourquoi Python est optimal
- **[MCP_SCRAPER_GUIDE.md](MCP_SCRAPER_GUIDE.md)** - Guide original JavaScript (référence)
- **[MCP_SCRAPER_GUIDE_PYTHON.md](MCP_SCRAPER_GUIDE_PYTHON.md)** - Guide Python (référence)

---

## 🤖 Automatisation Quotidienne

### Avec Cron (Linux/Mac)

```bash
# Éditer crontab
crontab -e

# Ajouter ligne (exécution quotidienne à 3h du matin)
0 3 * * * cd /path/to/mcp-collector && /path/to/venv/bin/python scripts/phase4_update.py >> data/logs/cron.log 2>&1
```

### Avec GitHub Actions

Voir `.github/workflows/daily-update.yml` (à créer):

```yaml
name: Daily MCP Update

on:
  schedule:
    - cron: '0 3 * * *'  # 3h quotidien
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python scripts/phase4_update.py
        env:
          GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
      - name: Commit changes
        run: |
          git config user.name "MCP Bot"
          git add data/mcp-servers.json
          git commit -m "chore: daily update $(date +%Y-%m-%d)" || exit 0
          git push
```

---

## 🧪 Tests et Développement

### Mode Test (5 serveurs)

```bash
# Tester avec seulement 5 serveurs pour debug
python scripts/dev_test.py
```

### Validation Manuelle

```bash
# Vérifier que le JSON est valide
python -c "import json; json.load(open('data/mcp-servers.json'))"

# Compter les serveurs
python -c "import json; print(len(json.load(open('data/mcp-servers.json'))['servers']))"

# Lister serveurs avec problèmes
python -c "
import json
data = json.load(open('data/mcp-servers.json'))
needs_review = [s['slug'] for s in data['servers'] if s['status'] != 'approved']
print(f'Needs review: {len(needs_review)}')
print('\n'.join(needs_review))
"
```

---

## 📈 Métriques de Qualité

Après exécution de Phase 3, vérifier `data/validation-report.json`:

```json
{
  "total_servers": 103,
  "approved": 87,
  "needs_review": 12,
  "needs_enrichment": 4,
  "completeness_avg": 82.5,
  "quality_score": "A"
}
```

**Critères de succès:**
- ✅ Total ≥ 50 serveurs
- ✅ Approved ≥ 80%
- ✅ Complétude moyenne ≥ 75%
- ✅ 0 erreurs critiques

---

## 🐛 Troubleshooting

### Erreur: GitHub Rate Limit

```
Error: API rate limit exceeded
```

**Solution:**
1. Vérifier que `GITHUB_TOKEN` est configuré dans `.env`
2. Token donne 5000 req/h au lieu de 60
3. Attendre reset (1h) ou utiliser plusieurs tokens

### Erreur: Dépendances manquantes

```
ModuleNotFoundError: No module named 'aiohttp'
```

**Solution:**
```bash
# Réinstaller dépendances
pip install -r requirements.txt --upgrade
```

### Erreur: Permissions Git

```
Permission denied (publickey)
```

**Solution:**
- Clone en HTTPS au lieu de SSH
- Ou configurer clé SSH: https://docs.github.com/en/authentication

---

## 🤝 Contribution

Les contributions sont bienvenues!

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'feat: add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Ouvrir une Pull Request

---

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

---

## 🙏 Remerciements

- [Model Context Protocol](https://modelcontextprotocol.io) - Pour le protocole MCP
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) - Registre officiel
- Toute la communauté MCP 🚀

---

## 📞 Support

- 📖 **Documentation complète**: [MCP_MASTER_PLAN.md](MCP_MASTER_PLAN.md)
- 🐛 **Issues**: [GitHub Issues](../../issues)
- 💬 **Discussions**: [GitHub Discussions](../../discussions)

---

**Fait avec ❤️ et Python 🐍**
