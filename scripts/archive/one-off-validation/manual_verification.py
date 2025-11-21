"""
Manual verification script - Extract READMEs from DB for manual reading
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get README for a specific server
server_slug = sys.argv[1] if len(sys.argv) > 1 else None

if not server_slug:
    print("Usage: python manual_verification.py <server-slug>")
    print("\nAvailable servers:")
    cursor.execute("""
        SELECT s.slug, COUNT(t.id) as tool_count
        FROM servers s
        LEFT JOIN tools t ON t.server_id = s.id
        INNER JOIN markdown_content mc ON mc.server_id = s.id AND mc.content_type = 'readme'
        GROUP BY s.slug
        ORDER BY tool_count DESC, s.slug
    """)
    for row in cursor.fetchall():
        slug, count = row
        status = f"({count} tools)" if count > 0 else "(NO TOOLS)"
        print(f"  • {slug:35s} {status}")
    sys.exit(1)

# Get README content
cursor.execute("""
    SELECT mc.content
    FROM servers s
    INNER JOIN markdown_content mc ON mc.server_id = s.id
    WHERE s.slug = ? AND mc.content_type = 'readme'
""", (server_slug,))

row = cursor.fetchone()
if not row:
    print(f"No README found for {server_slug}")
    sys.exit(1)

print(row[0])

conn.close()
