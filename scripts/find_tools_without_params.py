"""
Phase 8: Find all tools without parameters
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*75)
print("PHASE 8: TOOLS WITHOUT PARAMETERS")
print("="*75)

# Find all tools without parameters
cursor.execute("""
    SELECT
        s.name as server_name,
        t.id as tool_id,
        t.name as tool_name,
        t.display_name,
        t.description
    FROM tools t
    JOIN servers s ON t.server_id = s.id
    LEFT JOIN tool_parameters tp ON t.id = tp.tool_id
    WHERE tp.id IS NULL
    ORDER BY s.name, t.name
""")

tools_without_params = cursor.fetchall()

print(f"\n📊 Found {len(tools_without_params)} tools without parameters\n")

# Group by server
by_server = {}
for row in tools_without_params:
    server_name = row[0]
    if server_name not in by_server:
        by_server[server_name] = []
    by_server[server_name].append(row)

for server_name, tools in by_server.items():
    print(f"🔸 {server_name} ({len(tools)} tools)")
    for _, tool_id, tool_name, display_name, description in tools:
        print(f"   • {tool_name}")
        print(f"     Display: {display_name}")
        if description:
            desc_short = description[:80] + "..." if len(description) > 80 else description
            print(f"     Description: {desc_short}")
    print()

# Summary
print("="*75)
print("SUMMARY")
print("="*75)
print(f"Total tools without parameters: {len(tools_without_params)}")
print(f"Servers affected: {len(by_server)}")

# Also show total coverage
cursor.execute("SELECT COUNT(*) FROM tools")
total_tools = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT t.id)
    FROM tools t
    JOIN tool_parameters tp ON t.id = tp.tool_id
""")
tools_with_params = cursor.fetchone()[0]

coverage = (tools_with_params / total_tools * 100) if total_tools > 0 else 0

print(f"\nOverall coverage:")
print(f"  Tools with params: {tools_with_params}/{total_tools} ({coverage:.1f}%)")
print(f"  Tools without params: {len(tools_without_params)}/{total_tools} ({100-coverage:.1f}%)")

conn.close()
