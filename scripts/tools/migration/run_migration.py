"""
Run a SQL migration file on the database
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if len(sys.argv) < 2:
    print("Usage: python run_migration.py <migration_file>")
    sys.exit(1)

migration_file = sys.argv[1]
migration_path = Path(migration_file)

if not migration_path.exists():
    print(f"❌ Migration file not found: {migration_path}")
    sys.exit(1)

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    sys.exit(1)

print(f"Running migration: {migration_path.name}")
print(f"Database: {db_path}")
print()

# Read migration SQL
with open(migration_path, 'r', encoding='utf-8') as f:
    sql = f.read()

# Connect and execute
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Execute the migration
    cursor.executescript(sql)
    conn.commit()
    print("✅ Migration completed successfully")
except Exception as e:
    conn.rollback()
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
finally:
    conn.close()
