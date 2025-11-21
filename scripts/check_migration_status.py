"""
Check migration status for tool_parameters table
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("MIGRATION STATUS CHECK")
print("=" * 70)
print()

# Check if tool_parameters table exists
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND name='tool_parameters'
""")

if cursor.fetchone():
    print("✅ tool_parameters table EXISTS")

    # Get table schema
    cursor.execute("PRAGMA table_info(tool_parameters)")
    columns = cursor.fetchall()

    print(f"   Columns ({len(columns)}):")
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        not_null = "NOT NULL" if col[3] else ""
        default = f"DEFAULT {col[4]}" if col[4] else ""
        print(f"     • {col_name:20s} {col_type:15s} {not_null:10s} {default}")

    # Check row count
    cursor.execute("SELECT COUNT(*) FROM tool_parameters")
    count = cursor.fetchone()[0]
    print(f"   Rows: {count}")
    print()
else:
    print("❌ tool_parameters table DOES NOT EXIST")
    print()

# Check if params_count column exists in tools table
cursor.execute("PRAGMA table_info(tools)")
tools_columns = cursor.fetchall()
tools_col_names = [col[1] for col in tools_columns]

if 'params_count' in tools_col_names:
    print("✅ params_count column EXISTS in tools table")
else:
    print("❌ params_count column DOES NOT EXIST in tools table")

print()

# Check if triggers exist
print("Triggers:")
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='trigger' AND (
        name='trigger_params_count_insert' OR
        name='trigger_params_count_delete'
    )
""")

triggers = cursor.fetchall()
if triggers:
    for trigger in triggers:
        print(f"  ✅ {trigger[0]}")
else:
    print("  ❌ No triggers found")

conn.close()

print()
print("=" * 70)
