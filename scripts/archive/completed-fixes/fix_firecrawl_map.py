"""
Phase 1.1: Fix firecrawl_map parameter
Current: id (string, optional)
Expected: url (string, required)
"""
import sys
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("PHASE 1.1: FIX firecrawl_map")
print("=" * 80)
print()

# Get tool_id for firecrawl_map
cursor.execute("""
    SELECT t.id, t.name
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'firecrawl-mcp-server' AND t.name = 'firecrawl_map'
""")

tool = cursor.fetchone()
if not tool:
    print("❌ Tool firecrawl_map not found")
    sys.exit(1)

tool_id, tool_name = tool
print(f"✅ Found tool: {tool_name} (ID: {tool_id})")
print()

# Check current parameters
cursor.execute("""
    SELECT id, name, type, required
    FROM tool_parameters
    WHERE tool_id = ?
""", (tool_id,))

current_params = cursor.fetchall()
print(f"Current parameters ({len(current_params)}):")
for param in current_params:
    param_id, name, type_, required = param
    req_str = "required" if required else "optional"
    print(f"  • {name} (type: {type_}, {req_str})")
print()

# Delete incorrect parameter
print("Step 1: Deleting incorrect parameter 'id'...")
cursor.execute("""
    DELETE FROM tool_parameters
    WHERE tool_id = ? AND name = 'id'
""", (tool_id,))
deleted = cursor.rowcount
print(f"  ✅ Deleted {deleted} parameter(s)")
print()

# Add correct parameter
print("Step 2: Adding correct parameter 'url'...")
now = datetime.utcnow().isoformat()
param_id = str(uuid.uuid4())

cursor.execute("""
    INSERT INTO tool_parameters (
        id,
        tool_id,
        name,
        type,
        description,
        required,
        default_value,
        example_value,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    param_id,
    tool_id,
    'url',
    'string',
    'URL of the website to map and discover indexed URLs',
    1,  # required=true
    None,
    'https://example.com',
    now,
    now
))

print(f"  ✅ Added parameter 'url' (ID: {param_id})")
print()

# Commit
conn.commit()
print("✅ Changes committed to database")
print()

# Verify
cursor.execute("""
    SELECT name, type, description, required
    FROM tool_parameters
    WHERE tool_id = ?
""", (tool_id,))

final_params = cursor.fetchall()
print(f"Final parameters ({len(final_params)}):")
for param in final_params:
    name, type_, desc, required = param
    req_str = "REQUIRED" if required else "OPTIONAL"
    print(f"  • {name:20s} ({type_:10s}) {req_str}")
    if desc:
        print(f"    └─ {desc}")
print()

if len(final_params) == 1 and final_params[0][0] == 'url':
    print("✅ SUCCESS: firecrawl_map correctly fixed!")
else:
    print("❌ ERROR: Unexpected final state")

print("=" * 80)

conn.close()
