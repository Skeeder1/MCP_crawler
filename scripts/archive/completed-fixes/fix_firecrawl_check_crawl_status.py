"""
Phase 1.2: Fix firecrawl_check_crawl_status parameters
Current: 7 wrong params (from extract tool)
Expected: 1 param 'id' (string, required)
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
print("PHASE 1.2: FIX firecrawl_check_crawl_status")
print("=" * 80)
print()

# Get tool_id
cursor.execute("""
    SELECT t.id, t.name
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'firecrawl-mcp-server' AND t.name = 'firecrawl_check_crawl_status'
""")

tool = cursor.fetchone()
if not tool:
    print("❌ Tool firecrawl_check_crawl_status not found")
    sys.exit(1)

tool_id, tool_name = tool
print(f"✅ Found tool: {tool_name}")
print(f"   ID: {tool_id}")
print()

# Check current parameters
cursor.execute("""
    SELECT id, name, type, required
    FROM tool_parameters
    WHERE tool_id = ?
    ORDER BY name
""", (tool_id,))

current_params = cursor.fetchall()
print(f"Current parameters ({len(current_params)}) - ALL WRONG:")
for param in current_params:
    param_id, name, type_, required = param
    req_str = "required" if required else "optional"
    type_str = type_ if type_ else "null"
    print(f"  ❌ {name:20s} (type: {type_str:10s}, {req_str})")
print()

# Delete ALL incorrect parameters
print(f"Step 1: Deleting ALL {len(current_params)} incorrect parameters...")
cursor.execute("""
    DELETE FROM tool_parameters
    WHERE tool_id = ?
""", (tool_id,))
deleted = cursor.rowcount
print(f"  ✅ Deleted {deleted} parameter(s)")
print()

# Add correct parameter 'id'
print("Step 2: Adding correct parameter 'id'...")
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
    'id',
    'string',
    'Crawl job ID to check status',
    1,  # required=true
    None,
    '550e8400-e29b-41d4-a716-446655440000',
    now,
    now
))

print(f"  ✅ Added parameter 'id' (param_id: {param_id})")
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
    print(f"  ✅ {name:20s} ({type_:10s}) {req_str}")
    if desc:
        print(f"     └─ {desc}")
print()

if len(final_params) == 1 and final_params[0][0] == 'id':
    print("✅ SUCCESS: firecrawl_check_crawl_status correctly fixed!")
    print("   Was: 7 wrong parameters")
    print("   Now: 1 correct parameter (id)")
else:
    print("❌ ERROR: Unexpected final state")

print("=" * 80)

conn.close()
