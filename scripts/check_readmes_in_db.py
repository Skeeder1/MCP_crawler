"""
Check how many servers in DB have READMEs with content
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# DB path (use existing DB)
db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("ANALYZING READMEs IN DATABASE")
print("=" * 70)
print()

# Count servers with markdown_content type='readme'
cursor.execute("""
    SELECT
        COUNT(DISTINCT mc.server_id) as servers_with_readme,
        COUNT(mc.id) as total_readme_entries,
        AVG(mc.word_count) as avg_word_count,
        MIN(mc.word_count) as min_word_count,
        MAX(mc.word_count) as max_word_count
    FROM markdown_content mc
    WHERE mc.content_type = 'readme'
    AND mc.content IS NOT NULL
    AND LENGTH(mc.content) > 100
""")

stats = cursor.fetchone()

print(f"Servers with README: {stats[0]}")
print(f"Total README entries: {stats[1]}")
print(f"Average word count: {stats[2]:.0f}" if stats[2] else "N/A")
print(f"Min word count: {stats[3]}")
print(f"Max word count: {stats[4]}")
print()

# Get sample of servers with READMEs
print("Sample servers with READMEs:")
print("-" * 70)

cursor.execute("""
    SELECT
        s.slug,
        s.name,
        mc.word_count,
        LENGTH(mc.content) as content_length,
        CASE
            WHEN mc.content LIKE '%## Available Tools%' THEN 'Has "Available Tools"'
            WHEN mc.content LIKE '%## Tools%' THEN 'Has "Tools"'
            WHEN mc.content LIKE '%### Available Tools%' THEN 'Has "### Available Tools"'
            WHEN mc.content LIKE '%### Tools%' THEN 'Has "### Tools"'
            ELSE 'No tools section'
        END as tools_section_status
    FROM servers s
    INNER JOIN markdown_content mc ON mc.server_id = s.id
    WHERE mc.content_type = 'readme'
    AND mc.content IS NOT NULL
    AND LENGTH(mc.content) > 100
    ORDER BY mc.word_count DESC
    LIMIT 20
""")

rows = cursor.fetchall()

for row in rows:
    slug, name, word_count, content_len, tools_status = row
    print(f"  • {slug:25s} | {word_count:5d} words | {tools_status}")

print()

# Count how many have tools sections
cursor.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN mc.content LIKE '%Available Tools%' OR mc.content LIKE '%## Tools%' OR mc.content LIKE '%### Tools%' THEN 1 ELSE 0 END) as with_tools_section
    FROM markdown_content mc
    WHERE mc.content_type = 'readme'
    AND mc.content IS NOT NULL
    AND LENGTH(mc.content) > 100
""")

total, with_tools = cursor.fetchone()

print("Summary:")
print(f"  Total READMEs: {total}")
print(f"  READMEs with 'Tools' section: {with_tools}")
print(f"  Percentage: {(with_tools/total*100) if total > 0 else 0:.1f}%")
print()

conn.close()
