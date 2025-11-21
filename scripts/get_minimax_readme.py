"""
Get minimax README from markdown_content table
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find minimax server
cursor.execute("""
    SELECT id, name
    FROM servers
    WHERE name LIKE '%MiniMax%' OR name LIKE '%minimax%'
""")

server = cursor.fetchone()
if server:
    server_id, server_name = server
    print(f"Server: {server_name}")

    # Get README from markdown_content
    cursor.execute("""
        SELECT content
        FROM markdown_content
        WHERE server_id = ?
    """, (server_id,))

    content = cursor.fetchone()
    if content:
        readme = content[0]
        print(f"README length: {len(readme)} chars\n")
        print("="*75)
        print(readme)
    else:
        print("\n❌ No markdown content found")

    # Also list tools
    cursor.execute("""
        SELECT name
        FROM tools
        WHERE server_id = ?
        ORDER BY name
    """, (server_id,))

    tools = cursor.fetchall()
    print("\n" + "="*75)
    print(f"TOOLS ({len(tools)}):")
    for (tool_name,) in tools:
        print(f"  - {tool_name}")
else:
    print("❌ No minimax server found")

conn.close()
