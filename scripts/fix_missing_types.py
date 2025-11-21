"""
Phase 3: Fix all parameters with missing types
"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Type corrections based on descriptions and defaults
TYPE_CORRECTIONS = {
    # Firecrawl extract parameters
    'firecrawl_extract.allowExternalLinks': 'boolean',
    'firecrawl_extract.enableWebSearch': 'boolean',
    'firecrawl_extract.includeSubdomains': 'boolean',
    'firecrawl_extract.prompt': 'string',
    'firecrawl_extract.schema': 'object',
    'firecrawl_extract.systemPrompt': 'string',
    'firecrawl_extract.urls': 'array',

    # Jina parameters
    'jina_reader.customTimeout': 'integer',
    'jina_reader.page': 'integer',
    'jina_reader.url': 'string',
    'jina_search.count': 'integer',
    'jina_search.query': 'string',
    'jina_search.siteFilter': 'string',
    'jina_search_vip.count': 'integer',
    'jina_search_vip.query': 'string',
    'jina_search_vip.siteFilter': 'string',
}

def fix_missing_types():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 3: FIX MISSING TYPES")
    print("="*75)

    # Get all parameters with missing types
    cursor.execute("""
        SELECT
            s.name as server_name,
            t.name as tool_name,
            tp.id as param_id,
            tp.name as param_name,
            tp.type
        FROM tool_parameters tp
        JOIN tools t ON tp.tool_id = t.id
        JOIN servers s ON t.server_id = s.id
        WHERE tp.type IS NULL OR tp.type = ''
        ORDER BY s.name, t.name, tp.name
    """)

    missing_types = cursor.fetchall()
    print(f"\n📊 Found {len(missing_types)} parameters with missing types")

    fixed_count = 0
    skipped_count = 0

    for row in missing_types:
        server_name, tool_name, param_id, param_name, current_type = row
        key = f"{tool_name}.{param_name}"

        if key in TYPE_CORRECTIONS:
            new_type = TYPE_CORRECTIONS[key]

            # Update the type
            cursor.execute("""
                UPDATE tool_parameters
                SET type = ?, updated_at = ?
                WHERE id = ?
            """, (new_type, datetime.now(timezone.utc).isoformat(), param_id))

            print(f"   ✅ {key}: NULL → {new_type}")
            fixed_count += 1
        else:
            print(f"   ⚠️  {key}: No type correction defined (skipped)")
            skipped_count += 1

    conn.commit()

    # Verify
    print("\n" + "="*75)
    print("VERIFICATION")
    print("="*75)

    cursor.execute("""
        SELECT COUNT(*) FROM tool_parameters
        WHERE type IS NULL OR type = ''
    """)
    remaining = cursor.fetchone()[0]

    print(f"   Fixed: {fixed_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Remaining without type: {remaining}")

    conn.close()

    print("\n" + "="*75)
    if remaining == 0:
        print("✅ PHASE 3 COMPLETE - All types fixed!")
    else:
        print(f"⚠️  PHASE 3 PARTIAL - {remaining} types still missing")
    print("="*75)

if __name__ == "__main__":
    fix_missing_types()
