"""
Extract tools sections to individual files for manual reading
"""
import sqlite3
import re
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
output_dir = Path(__file__).parent.parent / "data" / "inspection" / "tools_sections"
output_dir.mkdir(exist_ok=True, parents=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

servers_with_tools = [
    'firecrawl-mcp-server',
    'jina-mcp-tools',
    'mcp-server-flomo',
    'minimax-mcp',
    'perplexity',
    'playwright-mcp',
    'serper-mcp-server'
]

print("Extracting tools sections for manual reading...")
print()

for slug in servers_with_tools:
    cursor.execute("""
        SELECT mc.content
        FROM servers s
        INNER JOIN markdown_content mc ON mc.server_id = s.id
        WHERE s.slug = ? AND mc.content_type = 'readme'
    """, (slug,))

    row = cursor.fetchone()
    if row:
        content = row[0]

        # Find tools section
        patterns = [
            r'## Available Tools.*?(?=\n##[^#]|\Z)',
            r'## Tools.*?(?=\n##[^#]|\Z)',
        ]

        section = None
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                section = match.group(0)
                break

        if section:
            output_file = output_dir / f"{slug}_tools.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"SERVER: {slug}\n")
                f.write("=" * 80 + "\n\n")
                f.write(section)

            print(f"✓ {slug:30s} | {len(section):5d} chars → {output_file.name}")

conn.close()

print()
print(f"Files saved to: {output_dir}")
