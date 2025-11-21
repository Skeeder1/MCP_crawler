"""
Delete incorrect jina parameters and re-enrich with fixed pattern order
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichers.parameters_enricher import ParametersEnricher

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("FIX JINA PARAMETERS")
print("=" * 80)
print()

# Step 1: Delete all parameters for jina tools
print("Step 1: Deleting old jina parameters...")
cursor.execute("""
    DELETE FROM tool_parameters
    WHERE tool_id IN (
        SELECT t.id FROM tools t
        INNER JOIN servers s ON s.id = t.server_id
        WHERE s.slug = 'jina-mcp-tools'
    )
""")
deleted = cursor.rowcount
print(f"  ✅ Deleted {deleted} parameters")
conn.commit()
print()

# Step 2: Re-run enricher on jina tools only
print("Step 2: Re-extracting parameters for jina tools...")
print()

# Get jina tools
cursor.execute("""
    SELECT
        t.id as tool_id,
        t.server_id,
        t.name as tool_name,
        t.display_name,
        s.slug as server_slug,
        mc.content as readme_content
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    INNER JOIN markdown_content mc ON mc.server_id = s.id
    WHERE s.slug = 'jina-mcp-tools'
    AND mc.content_type = 'readme'
    ORDER BY t.name
""")

tools = []
for row in cursor.fetchall():
    tools.append({
        'tool_id': row[0],
        'server_id': row[1],
        'tool_name': row[2],
        'display_name': row[3],
        'server_slug': row[4],
        'readme_content': row[5]
    })

enricher = ParametersEnricher(str(db_path))
enricher.connect()

for tool in tools:
    params = enricher.extract_parameters_for_tool(tool)
    print(f"  • {tool['tool_name']:20s} → {len(params)} parameters")

    for param in params:
        print(f"      - {param['name']}: {param['description'][:50]}...")
        enricher.save_parameter(param)
    print()

enricher.conn.commit()
enricher.close()

print("✅ Parameters re-enriched successfully")
print()

# Step 3: Verify
print("=" * 80)
print("VERIFICATION")
print("=" * 80)

cursor.execute("""
    SELECT t.name, COUNT(tp.id) as param_count
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    LEFT JOIN tool_parameters tp ON tp.tool_id = t.id
    WHERE s.slug = 'jina-mcp-tools'
    GROUP BY t.name
    ORDER BY t.name
""")

for row in cursor.fetchall():
    print(f"  • {row[0]:20s}: {row[1]} parameters")

print()
print("=" * 80)

conn.close()
