"""
Check mcp-server-flomo status in database
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
print("MCP-SERVER-FLOMO STATUS CHECK")
print("="*75)

# Check if server exists
cursor.execute("""
    SELECT id, name, display_name
    FROM servers
    WHERE name = 'mcp-server-flomo'
""")

server = cursor.fetchone()
if server:
    server_id, name, display_name = server
    print(f"\n✅ Server found:")
    print(f"   ID: {server_id}")
    print(f"   Name: {name}")
    print(f"   Display Name: {display_name}")

    # Check tools
    cursor.execute("""
        SELECT id, name, display_name, description
        FROM tools
        WHERE server_id = ?
    """, (server_id,))

    tools = cursor.fetchall()
    print(f"\n📊 Tools count: {len(tools)}")
    for tool in tools:
        print(f"   - {tool[1]} (ID: {tool[0]})")
        print(f"     Description: {tool[3]}")
else:
    print("\n❌ Server 'mcp-server-flomo' not found in database")

conn.close()
