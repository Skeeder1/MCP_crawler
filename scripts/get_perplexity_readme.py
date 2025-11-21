"""
Get perplexity README from markdown_content table
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
    SELECT id, name
    FROM servers
    WHERE name LIKE '%Perplexity%'
""")

server = cursor.fetchone()
if server:
    server_id, server_name = server
    print(f"Server: {server_name} (ID: {server_id})")

    # Get README from markdown_content
    cursor.execute("""
        SELECT content_type, content
        FROM markdown_content
        WHERE server_id = ?
    """, (server_id,))

    content = cursor.fetchone()
    if content:
        content_type, readme = content
        print(f"Content type: {content_type}")
        print(f"Content length: {len(readme)} chars")
        print("\n" + "="*75)
        print(readme)
    else:
        print("\n❌ No markdown content found for this server")
else:
    print("❌ No perplexity server found")

conn.close()
