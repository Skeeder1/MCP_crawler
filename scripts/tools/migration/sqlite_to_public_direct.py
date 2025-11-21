"""
Insert markdown and npm config data from SQLite directly to public schema
"""
import sys
import os
from pathlib import Path
import sqlite3
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent.parent  # Racine du projet
load_dotenv(project_root / 'config' / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DB_PATH = project_root / 'data' / 'mcp_servers.db'

print("="*70)
print("🚀 SQLite → Supabase public (MARKDOWN + npm config)")
print("="*70)

# Connect
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
print("\n✅ Connected")

def row_to_dict(row):
    return {k: row[k] for k in row.keys()}

# 1. MARKDOWN_CONTENT
print(f"\n{'='*70}")
print("📦 1. Inserting MARKDOWN_CONTENT")
print(f"{'='*70}\n")

cursor = conn.cursor()
cursor.execute("SELECT * FROM markdown_content")
rows = cursor.fetchall()

print(f"Found {len(rows)} markdown records in SQLite")

success = 0
for i, row in enumerate(rows, 1):
    content_preview = (row['content'] or '')[:30]
    print(f"[{i}/{len(rows)}] {content_preview}...", end='')

    try:
        data = row_to_dict(row)
        supabase.table('markdown_content').insert(data).execute()
        print(" ✅")
        success += 1
    except Exception as e:
        print(f" ❌ {str(e)[:60]}")

print(f"\nMarkdown: ✅ {success}/{len(rows)}")

# 2. MCP_CONFIG_NPM
print(f"\n{'='*70}")
print("📦 2. Inserting MCP_CONFIG_NPM")
print(f"{'='*70}\n")

cursor.execute("SELECT * FROM mcp_config_npm")
rows = cursor.fetchall()

print(f"Found {len(rows)} npm config records in SQLite")

success = 0
for i, row in enumerate(rows, 1):
    print(f"[{i}/{len(rows)}] {row['command']}...", end='')

    try:
        data = row_to_dict(row)

        # Parse JSON fields
        if data.get('args'):
            data['args'] = json.loads(data['args']) if isinstance(data['args'], str) else data['args']
        if data.get('env_required'):
            data['env_required'] = json.loads(data['env_required']) if isinstance(data['env_required'], str) else data['env_required']
        if data.get('env_descriptions'):
            data['env_descriptions'] = json.loads(data['env_descriptions']) if isinstance(data['env_descriptions'], str) else data['env_descriptions']

        supabase.table('mcp_config_npm').insert(data).execute()
        print(" ✅")
        success += 1
    except Exception as e:
        print(f" ❌ {str(e)[:60]}")

print(f"\nnpm config: ✅ {success}/{len(rows)}")

conn.close()

# Verification
print(f"\n{'='*70}")
print("🔍 Final Verification")
print(f"{'='*70}\n")

try:
    s = supabase.table('servers').select('count', count='exact').execute()
    g = supabase.table('github_info').select('count', count='exact').execute()
    m = supabase.table('markdown_content').select('count', count='exact').execute()
    n = supabase.table('mcp_config_npm').select('count', count='exact').execute()

    print(f"  servers:           {s.count}")
    print(f"  github_info:       {g.count}")
    print(f"  markdown_content:  {m.count}")
    print(f"  mcp_config_npm:    {n.count}")

    print(f"\n{'='*70}")
    if m.count > 0 and n.count > 0:
        print("✅ MIGRATION COMPLETE!")
        print(f"{'='*70}\n")
        print("🎉 Toutes les données sont maintenant dans public !")
        print("✅ Accessible via REST API (supabase-py)")
    else:
        print("⚠️  Migration incomplète")
        print(f"{'='*70}")

except Exception as e:
    print(f"⚠️  Error: {e}")
