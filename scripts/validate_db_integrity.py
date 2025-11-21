"""
Validate database integrity after enrichment
"""
import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("DATABASE INTEGRITY VALIDATION")
print("=" * 70)
print()

# 1. Check tools count
cursor.execute("SELECT COUNT(*) FROM tools")
total_tools = cursor.fetchone()[0]
print(f"✓ Total tools in DB: {total_tools}")

# 2. Check servers with tools
cursor.execute("""
    SELECT COUNT(DISTINCT server_id) FROM tools
""")
servers_with_tools = cursor.fetchone()[0]
print(f"✓ Servers with tools: {servers_with_tools}")

# 3. Verify tools_count column matches actual count
print("\n" + "=" * 70)
print("VERIFYING TOOLS_COUNT COLUMN")
print("=" * 70)

cursor.execute("""
    SELECT
        s.slug,
        s.tools_count,
        COUNT(t.id) as actual_count
    FROM servers s
    LEFT JOIN tools t ON t.server_id = s.id
    GROUP BY s.id
    HAVING s.tools_count != actual_count
""")

mismatches = cursor.fetchall()

if mismatches:
    print(f"\n⚠️  WARNING: {len(mismatches)} servers have incorrect tools_count:")
    for slug, expected, actual in mismatches:
        print(f"  • {slug:30s} | Expected: {expected} | Actual: {actual}")
    print("\n  → Triggers may not have fired correctly")
else:
    print("\n✅ All servers have correct tools_count column")

# 4. Check for NULL values in NOT NULL columns
print("\n" + "=" * 70)
print("CHECKING NOT NULL CONSTRAINTS")
print("=" * 70)

cursor.execute("""
    SELECT COUNT(*) FROM tools
    WHERE display_name IS NULL OR display_name = ''
""")
null_display = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM tools
    WHERE description IS NULL OR description = ''
""")
null_desc = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM tools
    WHERE input_schema IS NULL OR input_schema = ''
""")
null_schema = cursor.fetchone()[0]

if null_display > 0:
    print(f"⚠️  {null_display} tools have empty display_name")
else:
    print("✅ All tools have display_name")

if null_desc > 0:
    print(f"⚠️  {null_desc} tools have empty description")
else:
    print("✅ All tools have description")

if null_schema > 0:
    print(f"⚠️  {null_schema} tools have empty input_schema")
else:
    print("✅ All tools have input_schema")

# 5. Show top servers by tool count
print("\n" + "=" * 70)
print("TOP SERVERS BY TOOL COUNT")
print("=" * 70)

cursor.execute("""
    SELECT
        s.slug,
        COUNT(t.id) as tool_count,
        s.tools_count as recorded_count
    FROM servers s
    LEFT JOIN tools t ON t.server_id = s.id
    GROUP BY s.id
    HAVING tool_count > 0
    ORDER BY tool_count DESC
    LIMIT 10
""")

print()
for slug, actual, recorded in cursor.fetchall():
    match = "✓" if actual == recorded else "✗"
    print(f"  {match} {slug:30s} | {actual:2d} tools (recorded: {recorded})")

# 6. Sample tools
print("\n" + "=" * 70)
print("SAMPLE TOOLS (5 random)")
print("=" * 70)

cursor.execute("""
    SELECT
        s.slug,
        t.name,
        t.display_name,
        LENGTH(t.description) as desc_len
    FROM tools t
    JOIN servers s ON s.id = t.server_id
    ORDER BY RANDOM()
    LIMIT 5
""")

print()
for slug, name, display, desc_len in cursor.fetchall():
    print(f"  • {slug:25s} | {name:30s}")
    print(f"    Display: {display}")
    print(f"    Desc length: {desc_len} chars")
    print()

# 7. Run PRAGMA integrity check
print("=" * 70)
print("SQLITE INTEGRITY CHECK")
print("=" * 70)

cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()[0]

if result == "ok":
    print("\n✅ Database integrity: OK")
else:
    print(f"\n❌ Database integrity: {result}")

# 8. Foreign key check
cursor.execute("PRAGMA foreign_keys = ON")
cursor.execute("PRAGMA foreign_key_check")
fk_errors = cursor.fetchall()

if fk_errors:
    print(f"\n⚠️  Foreign key violations: {len(fk_errors)}")
    for error in fk_errors[:5]:
        print(f"  {error}")
else:
    print("✅ No foreign key violations")

conn.close()

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
