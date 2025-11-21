"""
Debug why jina_reader has wrong parameters
"""
import sys
import re
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.parameters_parser import ParametersParser

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get jina README
cursor.execute("""
    SELECT mc.content
    FROM servers s
    INNER JOIN markdown_content mc ON mc.server_id = s.id
    WHERE s.slug = 'jina-mcp-tools'
    AND mc.content_type = 'readme'
""")

readme_content = cursor.fetchone()[0]

print("=" * 80)
print("DEBUGGING jina_reader PARAMETER EXTRACTION")
print("=" * 80)
print()

# Manually extract tool section using the same logic as ParametersEnricher
tool_name = 'jina_reader'

patterns = [
    rf'`{re.escape(tool_name)}`',
    rf'\*\*{re.escape(tool_name)}\*\*',
    rf'###\s+{re.escape(tool_name)}',
    rf'###\s+[^#\n]*{re.escape(tool_name)}',
]

for i, pattern in enumerate(patterns, 1):
    match = re.search(pattern, readme_content, re.IGNORECASE)
    if match:
        print(f"Pattern {i} MATCHED: {pattern}")
        start = match.start()
        context_start = max(0, start - 200)
        context_end = min(len(readme_content), start + 2000)
        tool_section = readme_content[context_start:context_end]

        print(f"Match position: {start}")
        print(f"Section start: {context_start}")
        print(f"Section end: {context_end}")
        print()
        print("Extracted section:")
        print("-" * 80)
        print(tool_section[:800])
        print("-" * 80)
        print()

        # Parse parameters from this section
        parser = ParametersParser()
        params = parser.parse_parameters(tool_section)

        print(f"Parsed {len(params)} parameters:")
        for param in params:
            print(f"  • {param['name']}: {param['description'][:50]}...")

        break
else:
    print("❌ No pattern matched!")

# Check what's actually in the database
print()
print("=" * 80)
print("PARAMETERS IN DATABASE for jina_reader:")
print("=" * 80)

cursor.execute("""
    SELECT tp.name, tp.description
    FROM tool_parameters tp
    INNER JOIN tools t ON t.id = tp.tool_id
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'jina-mcp-tools' AND t.name = 'jina_reader'
""")

for param in cursor.fetchall():
    print(f"  • {param[0]}: {param[1]}")

conn.close()
