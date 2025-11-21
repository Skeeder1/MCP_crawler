"""
Generate comprehensive coverage report for tools and parameters enrichment
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
print("ENRICHMENT COVERAGE REPORT")
print("=" * 80)
print()

# 1. Overall statistics
print("1. OVERALL STATISTICS")
print("-" * 80)

cursor.execute("SELECT COUNT(*) FROM servers")
total_servers = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT s.id)
    FROM servers s
    INNER JOIN markdown_content mc ON mc.server_id = s.id
    WHERE mc.content_type = 'readme'
""")
servers_with_readme = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM tools")
total_tools = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT server_id) FROM tools")
servers_with_tools = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM tool_parameters")
total_params = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT tool_id) FROM tool_parameters")
tools_with_params = cursor.fetchone()[0]

print(f"Servers in database: {total_servers}")
print(f"  └─ with README: {servers_with_readme} ({servers_with_readme/total_servers*100:.1f}%)")
print(f"  └─ with tools extracted: {servers_with_tools} ({servers_with_tools/total_servers*100:.1f}%)")
print()
print(f"Tools extracted: {total_tools}")
print(f"  └─ with parameters: {tools_with_params} ({tools_with_params/total_tools*100:.1f}%)")
print()
print(f"Parameters extracted: {total_params}")
print(f"  └─ avg per tool: {total_params/total_tools:.1f}")
print()

# 2. Top servers by tools count
print("2. TOP SERVERS BY TOOLS COUNT")
print("-" * 80)

cursor.execute("""
    SELECT s.slug, s.name, COUNT(t.id) as tool_count
    FROM servers s
    LEFT JOIN tools t ON t.server_id = s.id
    GROUP BY s.id
    HAVING tool_count > 0
    ORDER BY tool_count DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"  • {row[0]:35s} {row[2]:3d} tools")
print()

# 3. Top tools by parameters count
print("3. TOP TOOLS BY PARAMETERS COUNT")
print("-" * 80)

cursor.execute("""
    SELECT
        s.slug,
        t.name,
        t.params_count
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    WHERE t.params_count > 0
    ORDER BY t.params_count DESC, s.slug
    LIMIT 15
""")

for row in cursor.fetchall():
    print(f"  • {row[0]:30s} :: {row[1]:30s} ({row[2]:2d} params)")
print()

# 4. Parameter type distribution
print("4. PARAMETER TYPES DISTRIBUTION")
print("-" * 80)

cursor.execute("""
    SELECT type, COUNT(*) as count
    FROM tool_parameters
    WHERE type IS NOT NULL
    GROUP BY type
    ORDER BY count DESC
""")

type_counts = cursor.fetchall()
total_typed = sum(row[1] for row in type_counts)

for row in type_counts:
    pct = row[1] / total_typed * 100 if total_typed > 0 else 0
    print(f"  • {row[0]:15s}: {row[1]:3d} ({pct:5.1f}%)")

cursor.execute("SELECT COUNT(*) FROM tool_parameters WHERE type IS NULL")
untyped = cursor.fetchone()[0]
if untyped > 0:
    print(f"  • (no type)      : {untyped:3d}")
print()

# 5. Required vs Optional parameters
print("5. REQUIRED VS OPTIONAL PARAMETERS")
print("-" * 80)

cursor.execute("SELECT required, COUNT(*) FROM tool_parameters GROUP BY required")
for row in cursor.fetchall():
    if row[0] == 1:
        status = "REQUIRED"
    elif row[0] == 0:
        status = "OPTIONAL"
    else:
        status = "UNKNOWN"
    print(f"  • {status:10s}: {row[1]:3d} ({row[1]/total_params*100:.1f}%)")
print()

# 6. Sample: Complete tool with all parameter details
print("6. SAMPLE: firecrawl_scrape (complete parameter details)")
print("-" * 80)

cursor.execute("""
    SELECT
        tp.name,
        tp.type,
        tp.description,
        tp.required,
        tp.default_value,
        tp.example_value
    FROM tool_parameters tp
    INNER JOIN tools t ON t.id = tp.tool_id
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'firecrawl-mcp-server' AND t.name = 'firecrawl_scrape'
    ORDER BY tp.name
""")

for row in cursor.fetchall():
    name, type_, desc, req, default, example = row

    # Format requirement status
    if req == 1:
        req_str = "REQUIRED"
    elif req == 0:
        req_str = "OPTIONAL"
    else:
        req_str = "UNKNOWN"

    type_str = f"({type_})" if type_ else ""

    print(f"\n  {name}")
    print(f"    Type: {type_ or 'unknown'}  |  {req_str}")
    if desc:
        print(f"    Description: {desc[:70]}...")
    if default:
        print(f"    Default: {default}")
    if example:
        ex = example[:60] + "..." if len(example) > 60 else example
        print(f"    Example: {ex}")
print()

# 7. Servers enriched
print("7. SERVERS ENRICHED (with parameters)")
print("-" * 80)

cursor.execute("""
    SELECT DISTINCT s.slug, s.name
    FROM servers s
    INNER JOIN tools t ON t.server_id = s.id
    INNER JOIN tool_parameters tp ON tp.tool_id = t.id
    ORDER BY s.slug
""")

enriched_servers = cursor.fetchall()
for row in enriched_servers:
    print(f"  ✅ {row[0]}")

print()
print(f"Total: {len(enriched_servers)} servers enriched with parameters")
print()

# 8. Success summary
print("=" * 80)
print("SUCCESS SUMMARY")
print("=" * 80)

print(f"✅ Tools Enrichment:")
print(f"   • {servers_with_tools} servers have tools extracted")
print(f"   • {total_tools} tools extracted")
print(f"   • Success rate: {servers_with_tools/servers_with_readme*100:.1f}%")
print()

print(f"✅ Parameters Enrichment:")
print(f"   • {len(enriched_servers)} servers have parameters extracted")
print(f"   • {tools_with_params} tools have parameters")
print(f"   • {total_params} parameters extracted")
print(f"   • Coverage: {tools_with_params/total_tools*100:.1f}% of tools")
print()

print("✅ Quality:")
print(f"   • {len(type_counts)} different parameter types identified")
print(f"   • Required/Optional flags: {(total_params-untyped)/total_params*100:.1f}% coverage")
print()

print("=" * 80)

conn.close()
