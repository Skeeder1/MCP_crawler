"""
Get playwright README to extract proper tool descriptions
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find playwright server
cursor.execute("""
    SELECT id, name
    FROM servers
    WHERE name LIKE '%Playwright%'
""")

server = cursor.fetchone()
if server:
    server_id, server_name = server
    print(f"Server: {server_name}")

    # Get README from markdown_content
    cursor.execute("""
        SELECT content
        FROM markdown_content
        WHERE server_id = ? AND content_type = 'readme'
    """, (server_id,))

    content = cursor.fetchone()
    if content:
        readme = content[0]
        print(f"README length: {len(readme)} chars")
        print("\n" + "="*75)

        # Look for the "Available Tools" section
        import re

        # Try to find tools section
        tools_section_match = re.search(r'##\s+Available\s+Tools.*?(?=\n##|\Z)', readme, re.DOTALL | re.IGNORECASE)

        if tools_section_match:
            tools_section = tools_section_match.group(0)
            print("AVAILABLE TOOLS SECTION FOUND")
            print("="*75)
            print(tools_section[:2000])  # Print first 2000 chars
        else:
            # If not found, print first 1000 chars of README
            print("Tools section not found. Printing first 1000 chars:")
            print("="*75)
            print(readme[:1000])
    else:
        print("\n❌ No markdown content found")
else:
    print("❌ No playwright server found")

conn.close()
