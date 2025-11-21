"""
Check what jina tools are in the database
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("JINA-MCP-TOOLS TOOLS IN DATABASE")
print("=" * 70)
print()

cursor.execute("""
    SELECT t.id, t.name, t.display_name, t.description
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'jina-mcp-tools'
    ORDER BY t.name
""")

tools = cursor.fetchall()

print(f"Found {len(tools)} tools:")
print()

for tool in tools:
    print(f"ID: {tool[0]}")
    print(f"Name: {tool[1]}")
    print(f"Display: {tool[2]}")
    print(f"Description: {tool[3][:80]}..." if tool[3] else "Description: (none)")
    print()

print("=" * 70)
print("EXPECTED: jina_reader, jina_search, jina_search_vip")
print(f"ACTUAL: {', '.join([t[1] for t in tools])}")
print("=" * 70)

conn.close()
