"""
Manual verification: Read all 20 server READMEs and compare with DB
"""
import sqlite3
import sys
import re
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the 20 servers that were processed
cursor.execute("""
    SELECT s.slug, s.id, mc.content
    FROM servers s
    INNER JOIN markdown_content mc ON mc.server_id = s.id
    WHERE mc.content_type = 'readme'
    AND mc.content IS NOT NULL
    AND LENGTH(mc.content) > 100
    ORDER BY s.slug
    LIMIT 20
""")

servers = cursor.fetchall()

print("=" * 80)
print("MANUAL VERIFICATION - 20 SERVERS")
print("=" * 80)
print()

results = []

for slug, server_id, content in servers:
    print(f"{'=' * 80}")
    print(f"SERVER: {slug}")
    print(f"{'=' * 80}")

    # Extract tools section from README
    patterns = [
        r'## Available Tools.*?(?=\n##[^#]|\Z)',
        r'## Tools.*?(?=\n##[^#]|\Z)',
        r'### Available Tools.*?(?=\n###[^#]|\n##[^#]|\Z)',
        r'### Tools.*?(?=\n###[^#]|\n##[^#]|\Z)',
    ]

    tools_section = None
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            tools_section = match.group(0)
            break

    if not tools_section:
        print("📄 README Status: No 'Tools' section found")
        print("   → Expected: 0 tools")

        # Check what's in DB
        cursor.execute("SELECT COUNT(*) FROM tools WHERE server_id = ?", (server_id,))
        db_count = cursor.fetchone()[0]

        print(f"   → In DB: {db_count} tools")

        if db_count == 0:
            print("   ✅ CORRECT - No tools expected, none in DB")
            results.append({'slug': slug, 'expected': 0, 'in_db': 0, 'match': True})
        else:
            print(f"   ❌ ERROR - Found {db_count} tools in DB but README has no tools section")
            results.append({'slug': slug, 'expected': 0, 'in_db': db_count, 'match': False})
    else:
        # Extract tool names manually from the section
        print("📄 README Status: 'Tools' section found")
        print(f"   Section length: {len(tools_section)} chars")
        print()
        print("   MANUAL EXTRACTION:")

        # Try multiple patterns to extract tool names
        tool_names = set()

        # Pattern 1: ### **tool_name**
        p1 = re.findall(r'###\s*\*\*([a-zA-Z0-9_-]+)\*\*', tools_section)
        if p1:
            print(f"   • Pattern '### **tool**': {len(p1)} tools")
            tool_names.update(p1)

        # Pattern 2: ### N. Tool (`tool_name`)
        p2 = re.findall(r'###\s*\d+\.\s*.*?\(`([a-zA-Z0-9_-]+)`\)', tools_section)
        if p2:
            print(f"   • Pattern '### N. Tool (`tool`)': {len(p2)} tools")
            tool_names.update(p2)

        # Pattern 3: - `tool_name` -
        p3 = re.findall(r'-\s*`([a-zA-Z0-9_-]+)`\s*[-–—]', tools_section)
        if p3:
            print(f"   • Pattern '- `tool` -': {len(p3)} tools")
            tool_names.update(p3)

        # Pattern 4: | `tool_name` | (markdown table)
        p4 = re.findall(r'\|\s*`([a-zA-Z0-9_-]+)`\s*\|', tools_section)
        if p4:
            print(f"   • Pattern '| `tool` |': {len(p4)} tools")
            tool_names.update(p4)

        # Pattern 5: - **tool_name**
        p5 = re.findall(r'-\s*\*\*([a-zA-Z0-9_-]+)\*\*', tools_section)
        if p5:
            print(f"   • Pattern '- **tool**': {len(p5)} tools")
            tool_names.update(p5)

        expected_count = len(tool_names)
        print()
        print(f"   📊 TOTAL UNIQUE TOOLS FOUND: {expected_count}")

        if tool_names:
            print("   Tools list:")
            for i, name in enumerate(sorted(tool_names), 1):
                print(f"      {i:2d}. {name}")

        # Check what's in DB
        cursor.execute("""
            SELECT name FROM tools
            WHERE server_id = ?
            ORDER BY name
        """, (server_id,))
        db_tools = [row[0] for row in cursor.fetchall()]
        db_count = len(db_tools)

        print()
        print(f"   💾 IN DATABASE: {db_count} tools")

        if db_tools:
            for i, name in enumerate(db_tools, 1):
                in_readme = "✓" if name in tool_names else "✗ NOT IN README"
                print(f"      {i:2d}. {name:35s} {in_readme}")

        # Compare
        missing = tool_names - set(db_tools)
        extra = set(db_tools) - tool_names

        print()
        if expected_count == db_count and not missing and not extra:
            print("   ✅ PERFECT MATCH - 100% accuracy")
            results.append({'slug': slug, 'expected': expected_count, 'in_db': db_count, 'match': True})
        else:
            print("   ❌ MISMATCH DETECTED")
            if missing:
                print(f"   ⚠️  MISSING from DB ({len(missing)}): {', '.join(sorted(missing))}")
            if extra:
                print(f"   ⚠️  EXTRA in DB ({len(extra)}): {', '.join(sorted(extra))}")
            results.append({'slug': slug, 'expected': expected_count, 'in_db': db_count, 'match': False})

    print()

conn.close()

# Final summary
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print()

total = len(results)
perfect = sum(1 for r in results if r['match'])
accuracy = (perfect / total * 100) if total > 0 else 0

print(f"Servers verified: {total}")
print(f"Perfect matches: {perfect}")
print(f"Accuracy: {accuracy:.1f}%")
print()

print("Details:")
for r in results:
    status = "✅" if r['match'] else "❌"
    print(f"  {status} {r['slug']:30s} | Expected: {r['expected']:2d} | In DB: {r['in_db']:2d}")

print()
if accuracy == 100:
    print("✅ SUCCESS: 100% accuracy achieved!")
    print("   All tools from READMEs are correctly stored in the database.")
else:
    print(f"❌ FAILURE: Only {accuracy:.1f}% accuracy")
    print("   Review mismatches above.")
