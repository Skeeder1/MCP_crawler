"""
Debug which pattern is matching in jina-mcp-tools
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.tools_parser import ToolsParser


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

content = cursor.fetchone()[0]
conn.close()

parser = ToolsParser()

print("=" * 80)
print("DEBUGGING JINA-MCP-TOOLS PARSING")
print("=" * 80)
print()

# Test section extraction
section = parser._extract_tools_section(content)
if section:
    print(f"✅ Tools section extracted ({len(section)} chars)")
    print()
    print("Section preview:")
    print("-" * 80)
    print(section[:500])
    print("-" * 80)
    print()
else:
    print("❌ No tools section found")
    sys.exit(1)

# Test each pattern individually
import re

print("Testing Pattern 1 (### **tool_name**):")
pattern1 = r'###\s*\*\*([a-zA-Z0-9_-]+)\*\*\s*\n(.*?)(?=\n+###\s*\*\*|\Z)'
matches1 = list(re.finditer(pattern1, section, re.DOTALL))
print(f"  Found {len(matches1)} matches")
for m in matches1:
    print(f"    - {m.group(1)}")
print()

print("Testing Pattern 2 (### 1. Tool (`name`)):")
pattern2 = r'###\s*\d+\.\s*.*?\(`([a-zA-Z0-9_-]+)`\)\s*\n(.*?)(?=\n+###\s*\d+\.|\Z)'
matches2 = list(re.finditer(pattern2, section, re.DOTALL))
print(f"  Found {len(matches2)} matches")
for m in matches2:
    print(f"    - {m.group(1)}")
print()

print("Testing Pattern 3 (- `name` - desc):")
# Clean section first
cleaned = parser._remove_parameters_sections(section)
print(f"  Section size after cleaning: {len(section)} → {len(cleaned)} chars")
pattern3 = r'-\s*`([a-zA-Z0-9_-]+)`\s*[-–—]\s*([^\n]+)'
matches3 = list(re.finditer(pattern3, cleaned))
print(f"  Found {len(matches3)} matches")
for m in matches3:
    print(f"    - {m.group(1)}: {m.group(2)[:50]}...")
print()

print("Testing Pattern 4 (table):")
pattern4 = r'\|\s*`([a-zA-Z0-9_-]+)`\s*\|\s*([^|\n]+)\s*\|'
matches4 = list(re.finditer(pattern4, section))
print(f"  Found {len(matches4)} matches")
for m in matches4:
    print(f"    - {m.group(1)}")
print()

print("Testing Pattern 5 (- **name**: desc):")
pattern5 = r'-\s*\*\*([a-zA-Z0-9_-]+)\*\*:?\s*([^\n]+)'
matches5 = list(re.finditer(pattern5, section))
print(f"  Found {len(matches5)} matches")
for m in matches5:
    print(f"    - {m.group(1)}: {m.group(2)[:50]}...")
print()

print("Testing Pattern 6 (### tool_name or ### tool1 / tool2):")
pattern6 = r'###\s+([a-zA-Z0-9_/-]+)\s*\n(.*?)(?=\n###|\n##|\Z)'
matches6 = list(re.finditer(pattern6, section, re.DOTALL))
print(f"  Found {len(matches6)} matches")
for m in matches6:
    names = m.group(1)
    desc = m.group(2)[:100]
    print(f"    - Names: {names}")
    print(f"      Desc: {desc}...")
print()

print("=" * 80)
print("FULL PARSE RESULT:")
print("=" * 80)
tools = parser.parse_tools(content)
print(f"Found {len(tools)} tools:")
for tool in tools:
    print(f"  - {tool['name']}")
