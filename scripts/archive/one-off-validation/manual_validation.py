"""
Manual validation: Extract README sections for visual inspection
"""
import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

servers = [
    'firecrawl-mcp-server',
    'mcp-server-flomo',
    'minimax-mcp',
    'playwright-mcp',
    'serper-mcp-server',
    'perplexity'
]

for slug in servers:
    print("=" * 80)
    print(f"SERVER: {slug}")
    print("=" * 80)

    cursor.execute("""
        SELECT mc.content
        FROM servers s
        INNER JOIN markdown_content mc ON mc.server_id = s.id
        WHERE s.slug = ?
        AND mc.content_type = 'readme'
    """, (slug,))

    row = cursor.fetchone()
    if not row:
        print("ERROR: No README found")
        continue

    content = row[0]

    # Find and display tools section
    import re
    patterns = [
        r'## Available Tools.*?(?=\n##[^#]|\Z)',
        r'## Tools.*?(?=\n##[^#]|\Z)',
        r'### Available Tools.*?(?=\n###[^#]|\n##[^#]|\Z)',
        r'### Tools.*?(?=\n###[^#]|\n##[^#]|\Z)',
    ]

    section = None
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            section = match.group(0)
            break

    if section:
        # Limit to first 2000 chars for readability
        display = section[:2000]
        if len(section) > 2000:
            display += f"\n\n... (truncated {len(section) - 2000} chars)"

        print(display)
    else:
        print("WARNING: No tools section found")

    print("\n")

conn.close()
