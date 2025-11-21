#!/usr/bin/env python3
"""
Fix command constraint in mcp_config_npm table to accept new commands
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Disable foreign keys to avoid trigger issues
cursor.execute("PRAGMA foreign_keys = OFF")

print("=" * 70)
print("Fixing command constraint in mcp_config_npm")
print("=" * 70)

# Get current schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='mcp_config_npm';")
current_schema = cursor.fetchone()[0]
print("\nCurrent schema:")
print(current_schema)
print()

# SQLite doesn't support ALTER TABLE to modify CHECK constraints
# We need to recreate the table

print("Step 1: Drop temp table if exists...")
cursor.execute("DROP TABLE IF EXISTS mcp_config_npm_new")

print("Step 2: Creating new table without constraint...")

# Create new table structure (removing CHECK constraint)
cursor.execute("""
CREATE TABLE mcp_config_npm_new (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    server_id TEXT NOT NULL,
    command TEXT,
    args TEXT,
    env_required TEXT,
    env_descriptions TEXT,
    runtime TEXT DEFAULT 'node',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
)
""")

print("Step 3: Copying existing data...")
cursor.execute("""
INSERT INTO mcp_config_npm_new
SELECT * FROM mcp_config_npm
""")

rows_copied = cursor.rowcount
print(f"   Copied {rows_copied} rows")

print("Step 4: Get ALL triggers that reference mcp_config_npm...")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger';")
all_triggers = cursor.fetchall()
affected_triggers = [(name, sql) for name, sql in all_triggers if sql and 'mcp_config_npm' in sql]

for name, sql in affected_triggers:
    print(f"   Found trigger: {name}")

print("Step 5: Drop all affected triggers temporarily...")
for name, sql in affected_triggers:
    cursor.execute(f"DROP TRIGGER IF EXISTS {name}")
    print(f"   Dropped: {name}")

print("Step 6: Dropping old table...")
cursor.execute("DROP TABLE mcp_config_npm")

print("Step 7: Renaming new table...")
cursor.execute("ALTER TABLE mcp_config_npm_new RENAME TO mcp_config_npm")

print("Step 8: Recreating triggers...")
for name, sql in affected_triggers:
    if sql:
        # Recreate trigger with same SQL
        cursor.execute(sql)
        print(f"   Recreated trigger: {name}")

print("Step 9: Creating index...")
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_mcp_config_npm_server
ON mcp_config_npm(server_id)
""")

conn.commit()

# Re-enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

print("\n" + "=" * 70)
print("[SUCCESS] Table mcp_config_npm updated successfully!")
print("Now accepts any command: npx, npm, node, uvx, pip, python, git, etc.")
print("=" * 70)

conn.close()
