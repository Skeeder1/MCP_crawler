"""
Show database schema to understand structure
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("="*75)
print("DATABASE SCHEMA")
print("="*75)

for (table_name,) in tables:
    print(f"\n📦 Table: {table_name}")
    print("   Columns:")

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        pk_marker = " [PK]" if pk else ""
        null_marker = " NOT NULL" if not_null else ""
        print(f"      - {col_name} ({col_type}){pk_marker}{null_marker}")

conn.close()
