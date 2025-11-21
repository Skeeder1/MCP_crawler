"""
List all servers in database
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
print("ALL SERVERS IN DATABASE")
print("="*75)

# Get all servers
cursor.execute("""
    SELECT s.id, s.name, s.display_name,
           COUNT(DISTINCT t.id) as tools_count,
           COUNT(DISTINCT tp.id) as params_count
    FROM servers s
    LEFT JOIN tools t ON s.id = t.server_id
    LEFT JOIN tool_parameters tp ON t.id = tp.tool_id
    GROUP BY s.id, s.name, s.display_name
    ORDER BY tools_count DESC, s.name
""")

servers = cursor.fetchall()
print(f"\nTotal servers: {len(servers)}\n")

for i, (server_id, name, display_name, tools_count, params_count) in enumerate(servers, 1):
    print(f"{i:2}. {name}")
    print(f"    Display: {display_name}")
    print(f"    Tools: {tools_count}, Params: {params_count}")

    # Highlight servers with tools but no params
    if tools_count > 0 and params_count == 0:
        print(f"    ⚠️  HAS TOOLS BUT NO PARAMS!")
    print()

# Search for flomo specifically
print("="*75)
print("SEARCHING FOR 'flomo'...")
print("="*75)

cursor.execute("""
    SELECT id, name, display_name
    FROM servers
    WHERE name LIKE '%flomo%' OR display_name LIKE '%flomo%'
""")

flomo_servers = cursor.fetchall()
if flomo_servers:
    print(f"\nFound {len(flomo_servers)} server(s) with 'flomo':")
    for server in flomo_servers:
        print(f"   - {server[1]} (Display: {server[2]})")
else:
    print("\n❌ No server found with 'flomo' in name")

conn.close()
