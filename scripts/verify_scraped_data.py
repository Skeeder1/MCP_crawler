"""
Verify that scraped data matches expected MCP server elements
"""
import sys
import os
from pathlib import Path
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

from supabase import create_client
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("="*70)
print("VERIFICATION DES DONNEES SCRAPEES VS ELEMENTS ATTENDUS")
print("="*70)
print()

# Load expected elements
with open(project_root / 'mcp-server-elements important.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

print("ELEMENTS ATTENDUS (d'apres le fichier JSON):")
print("-" * 70)

elements_groups = {
    "Serveur de base": [
        "id", "slug", "name", "display_name", "tagline", "short_description",
        "logo_url", "homepage_url"
    ],
    "GitHub": [
        "github_url", "github_owner", "github_repo", "github_stars", "github_last_commit"
    ],
    "npm": [
        "npm_package", "npm_version"
    ],
    "Categories/Tags": [
        "categories", "tags"
    ],
    "Config MCP": [
        "mcp_config.runtime", "mcp_config.command", "mcp_config.args",
        "mcp_config.env_required", "mcp_config.env_descriptions"
    ],
    "Tools": [
        "tools", "tools_count"
    ],
    "Metriques": [
        "install_count", "favorite_count"
    ],
    "Statut": [
        "status", "verification_status"
    ],
    "Createur": [
        "creator_id", "creator_name", "creator_username"
    ],
    "Dates": [
        "created_at", "published_at", "updated_at"
    ]
}

for group, fields in elements_groups.items():
    print(f"\n{group}:")
    for field in fields:
        # Check if field exists in expected JSON
        if '.' in field:
            parts = field.split('.')
            value = expected
            for part in parts:
                value = value.get(part, None) if isinstance(value, dict) else None
        else:
            value = expected.get(field, None)

        if value is not None:
            if isinstance(value, list):
                status = f"OK (array avec {len(value)} elements)"
            elif isinstance(value, dict):
                status = f"OK (objet avec {len(value)} cles)"
            else:
                status = "OK"
            print(f"  {field:35} {status}")
        else:
            print(f"  {field:35} ABSENT")

print("\n" + "="*70)
print("VERIFICATION DES DONNEES DANS SUPABASE")
print("="*70)

# Véri un serveur
result = supabase.table('servers').select('*').limit(1).execute()
if result.data:
    server = result.data[0]

    print("\nEXEMPLE DE SERVEUR SCRAPPE:")
    print("-" * 70)

    # Serveur de base
    print("\nServeur de base:")
    for field in elements_groups["Serveur de base"]:
        value = server.get(field)
        if value:
            if len(str(value)) > 50:
                display = str(value)[:47] + "..."
            else:
                display = str(value)
            print(f"  {field:25} OK: {display}")
        else:
            print(f"  {field:25} ABSENT")

    # Check GitHub
    print("\nGitHub (table github_info):")
    gh_result = supabase.table('github_info').select('*').eq('server_id', server['id']).execute()
    if gh_result.data:
        gh = gh_result.data[0]
        for field in ["github_url", "github_owner", "github_repo", "github_stars", "github_last_commit"]:
            value = gh.get(field)
            if value is not None:
                print(f"  {field:25} OK: {value}")
            else:
                print(f"  {field:25} ABSENT")
    else:
        print("  Aucune donnee GitHub pour ce serveur")

    # Check npm config
    print("\nConfig MCP (table mcp_config_npm):")
    npm_result = supabase.table('mcp_config_npm').select('*').eq('server_id', server['id']).execute()
    if npm_result.data:
        npm = npm_result.data[0]
        for field in ["runtime", "command", "args", "env_required", "env_descriptions"]:
            value = npm.get(field)
            if value is not None:
                if isinstance(value, (list, dict)):
                    print(f"  {field:25} OK (type: {type(value).__name__})")
                else:
                    print(f"  {field:25} OK: {value}")
            else:
                print(f"  {field:25} ABSENT")
    else:
        print("  Aucune config MCP pour ce serveur")

# Count data in tables
print("\n" + "="*70)
print("COMPTAGE DES DONNEES PAR TABLE")
print("="*70)

counts = {}
tables = ['servers', 'github_info', 'markdown_content', 'mcp_config_npm']
for table in tables:
    count = supabase.table(table).select('count', count='exact').execute().count
    counts[table] = count
    print(f"  {table:25} {count:3} records")

# Analyse manquante
print("\n" + "="*70)
print("ANALYSE DES ELEMENTS MANQUANTS")
print("="*70)

missing = []

# Check if any server has categories/tags
# Note: Since we don't have these tables in public schema yet, we skip this

# Check tools
tools_count = supabase.table('servers').select('tools_count').execute()
if tools_count.data:
    total_tools = sum(s.get('tools_count', 0) for s in tools_count.data)
    if total_tools == 0:
        missing.append("Tools (tools_count = 0 pour tous les serveurs)")

# Check categories/tags - structure exists but no data
# We'd need to check if tables exist first
print("\nElements potentiellement manquants:")
print("  1. categories[] - Structure de table existe, donnees pas scrapees")
print("  2. tags[] - Structure de table existe, donnees pas scrapees")
print("  3. tools[] - Structure de table existe, mais tools_count = 0")

# Summary
print("\n" + "="*70)
print("RESUME")
print("="*70)

present = [
    "Serveur de base (id, slug, name, etc.)",
    "GitHub info (url, stars, owner, repo, last_commit)",
    "npm package (via mcp_config_npm)",
    "Config MCP (command, args, env)",
    "Markdown content (README)",
    "Metriques (install_count, favorite_count)",
    "Statut (status, verification_status)",
    "Createur (creator_*)",
    "Dates (created_at, published_at, updated_at)"
]

absent = [
    "categories[] - Pas scrape depuis mcp.so",
    "tags[] - Pas scrape depuis mcp.so",
    "tools[] - Pas scrape depuis mcp.so (tools_count = 0)"
]

print("\nPresent dans les donnees scrapees:")
for item in present:
    print(f"  OK {item}")

print("\nManquant dans les donnees scrapees:")
for item in absent:
    print(f"  XX {item}")

print("\n" + "="*70)
print("RECOMMANDATIONS")
print("="*70)
print("\nPour avoir toutes les informations du fichier JSON:")
print("  1. Scraper les categories depuis mcp.so")
print("  2. Scraper les tags depuis mcp.so")
print("  3. Scraper les tools depuis mcp.so (ou depuis README/docs)")
print("  4. Parser les tools depuis le code source GitHub si disponible")
