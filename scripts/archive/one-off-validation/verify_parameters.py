"""
Verify parameters were correctly saved to database
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("PARAMETERS VERIFICATION")
print("=" * 80)
print()

# Check total count
cursor.execute("SELECT COUNT(*) FROM tool_parameters")
total_params = cursor.fetchone()[0]
print(f"Total parameters in database: {total_params}")
print()

# Check params_count in tools table (should be auto-updated by trigger)
cursor.execute("""
    SELECT t.name, t.params_count, s.slug
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    WHERE t.params_count > 0
    ORDER BY t.params_count DESC
    LIMIT 10
""")

tools_with_counts = cursor.fetchall()
print("Top 10 tools by params_count (auto-updated by trigger):")
for tool in tools_with_counts:
    print(f"  • {tool[2]:30s} :: {tool[0]:30s} ({tool[1]} params)")
print()

# Sample jina_reader parameters
print("=" * 80)
print("SAMPLE: jina_reader parameters")
print("=" * 80)

cursor.execute("""
    SELECT
        tp.name,
        tp.type,
        tp.description,
        tp.required,
        tp.default_value
    FROM tool_parameters tp
    INNER JOIN tools t ON t.id = tp.tool_id
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'jina-mcp-tools' AND t.name = 'jina_reader'
    ORDER BY tp.name
""")

jina_params = cursor.fetchall()
print(f"Found {len(jina_params)} parameters:")
print()

for param in jina_params:
    req_str = "REQUIRED" if param[3] == 1 else ("OPTIONAL" if param[3] == 0 else "UNKNOWN")
    type_str = f"({param[1]})" if param[1] else ""
    default_str = f"[default: {param[4]}]" if param[4] else ""

    print(f"• {param[0]:20s} {type_str:10s} {req_str:10s} {default_str}")
    if param[2]:
        desc = param[2][:70] + "..." if len(param[2]) > 70 else param[2]
        print(f"  └─ {desc}")
print()

# Sample firecrawl_scrape parameters
print("=" * 80)
print("SAMPLE: firecrawl_scrape parameters")
print("=" * 80)

cursor.execute("""
    SELECT
        tp.name,
        tp.type,
        tp.description,
        tp.required,
        tp.example_value
    FROM tool_parameters tp
    INNER JOIN tools t ON t.id = tp.tool_id
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'firecrawl-mcp-server' AND t.name = 'firecrawl_scrape'
    ORDER BY tp.name
""")

firecrawl_params = cursor.fetchall()
print(f"Found {len(firecrawl_params)} parameters:")
print()

for param in firecrawl_params:
    req_str = "REQUIRED" if param[3] == 1 else ("OPTIONAL" if param[3] == 0 else "UNKNOWN")
    type_str = f"({param[1]})" if param[1] else ""
    example_str = f"[ex: {param[4][:30]}...]" if param[4] else ""

    print(f"• {param[0]:20s} {type_str:10s} {req_str:10s} {example_str}")
    if param[2]:
        desc = param[2][:70] + "..." if len(param[2]) > 70 else param[2]
        print(f"  └─ {desc}")
print()

print("=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)

conn.close()
