"""
Check if perplexity server has README in database
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find perplexity server
cursor.execute("""
    SELECT id, name, display_name
    FROM servers
    WHERE name LIKE '%perplexity%' OR name LIKE '%Perplexity%'
""")

servers = cursor.fetchall()
if servers:
    for server_id, name, display_name in servers:
        print(f"Server: {name}")
        print(f"Display: {display_name}")

        # Check if README exists
        cursor.execute("SELECT LENGTH(readme) as readme_size FROM servers WHERE id = ?", (server_id,))
        result = cursor.fetchone()
        if result and result[0]:
            print(f"README size: {result[0]} bytes")

            # Get first 500 chars of README
            cursor.execute("SELECT SUBSTR(readme, 1, 500) FROM servers WHERE id = ?", (server_id,))
            readme_snippet = cursor.fetchone()[0]
            print(f"\nREADME snippet:")
            print(readme_snippet[:300])
        else:
            print("❌ No README found")

        # List tools
        cursor.execute("""
            SELECT name, description
            FROM tools
            WHERE server_id = ?
        """, (server_id,))

        tools = cursor.fetchall()
        print(f"\nTools ({len(tools)}):")
        for tool_name, desc in tools:
            print(f"  - {tool_name}: {desc[:80] if desc else 'No description'}")

        print("\n" + "="*75 + "\n")
else:
    print("❌ No perplexity server found")

conn.close()
