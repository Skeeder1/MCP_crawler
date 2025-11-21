"""
Phase 3: Find all parameters with missing types
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
print("PHASE 3: PARAMETERS WITH MISSING TYPES")
print("="*75)

# Find all parameters with NULL or empty type
cursor.execute("""
    SELECT
        s.name as server_name,
        t.name as tool_name,
        tp.id as param_id,
        tp.name as param_name,
        tp.type,
        tp.description,
        tp.required,
        tp.default_value
    FROM tool_parameters tp
    JOIN tools t ON tp.tool_id = t.id
    JOIN servers s ON t.server_id = s.id
    WHERE tp.type IS NULL OR tp.type = ''
    ORDER BY s.name, t.name, tp.name
""")

missing_types = cursor.fetchall()

print(f"\n📊 Found {len(missing_types)} parameters with missing types\n")

# Group by server
by_server = {}
for row in missing_types:
    server_name = row[0]
    if server_name not in by_server:
        by_server[server_name] = []
    by_server[server_name].append(row)

for server_name, params in by_server.items():
    print(f"🔸 {server_name} ({len(params)} params)")
    for row in params:
        _, tool_name, param_id, param_name, param_type, description, required, default_value = row
        req_str = "required" if required else "optional"
        print(f"   • {tool_name}.{param_name} ({req_str})")
        if description:
            desc_short = description[:60] + "..." if len(description) > 60 else description
            print(f"     Description: {desc_short}")
        if default_value:
            print(f"     Default: {default_value}")
    print()

# Statistics
print("="*75)
print("SUMMARY")
print("="*75)
print(f"Total parameters with missing types: {len(missing_types)}")
print(f"Servers affected: {len(by_server)}")

conn.close()
