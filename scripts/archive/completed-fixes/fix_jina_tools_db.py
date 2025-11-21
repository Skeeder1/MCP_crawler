"""
Fix jina-mcp-tools in database:
1. Delete old incorrect tools (parameters extracted as tools)
2. Re-extract correct tools using fixed parser
"""
import sys
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.tools_parser import ToolsParser

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("FIX JINA-MCP-TOOLS IN DATABASE")
print("=" * 70)
print()

# Step 1: Get server_id for jina-mcp-tools
cursor.execute("SELECT id FROM servers WHERE slug = 'jina-mcp-tools'")
server_id = cursor.fetchone()[0]
print(f"Server ID: {server_id}")
print()

# Step 2: Get README content
cursor.execute("""
    SELECT content FROM markdown_content
    WHERE server_id = ? AND content_type = 'readme'
""", (server_id,))
readme_content = cursor.fetchone()[0]
print(f"README content: {len(readme_content)} chars")
print()

# Step 3: Delete old incorrect tools
print("Step 1: Deleting old incorrect tools...")
cursor.execute("""
    DELETE FROM tools
    WHERE server_id = ?
""", (server_id,))
deleted_count = cursor.rowcount
print(f"  ✅ Deleted {deleted_count} old tools")
print()

# Step 4: Extract correct tools using fixed parser
print("Step 2: Extracting correct tools...")
parser = ToolsParser()
tools = parser.parse_tools(readme_content)
print(f"  ✅ Extracted {len(tools)} tools:")
for tool in tools:
    print(f"     • {tool['name']}")
print()

# Step 5: Insert correct tools
print("Step 3: Inserting correct tools...")
now = datetime.utcnow().isoformat()

for tool in tools:
    tool_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO tools (
            id,
            server_id,
            name,
            display_name,
            description,
            input_schema,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tool_id,
        server_id,
        tool['name'],
        tool.get('display_name', ''),
        tool.get('description', ''),
        '{}',
        now,
        now
    ))
    print(f"  ✅ Inserted: {tool['name']}")

print()

# Commit
conn.commit()
print("✅ Changes committed to database")
print()

# Verify
cursor.execute("""
    SELECT name FROM tools
    WHERE server_id = ?
    ORDER BY name
""", (server_id,))

final_tools = [row[0] for row in cursor.fetchall()]
print("Final tools in database:")
for name in final_tools:
    print(f"  • {name}")

print()
print("=" * 70)
print("EXPECTED: jina_reader, jina_search, jina_search_vip")
print(f"ACTUAL: {', '.join(final_tools)}")

if set(final_tools) == {'jina_reader', 'jina_search', 'jina_search_vip'}:
    print("✅ SUCCESS: jina tools are now correct!")
else:
    print("❌ Issue remains")

print("=" * 70)

conn.close()
