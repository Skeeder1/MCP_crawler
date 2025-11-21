"""
Phase 1.3: Fix firecrawl_search parameters
Current: url (string, optional)
Expected: query, limit, lang, country, scrapeOptions
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
print("PHASE 1.3: FIX firecrawl_search")
print("=" * 80)
print()

# Get tool_id
cursor.execute("""
    SELECT t.id, t.name
    FROM tools t
    INNER JOIN servers s ON s.id = t.server_id
    WHERE s.slug = 'firecrawl-mcp-server' AND t.name = 'firecrawl_search'
""")

tool = cursor.fetchone()
if not tool:
    print("❌ Tool firecrawl_search not found")
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
""", (tool_id,))

current_params = cursor.fetchall()
print(f"Current parameters ({len(current_params)}):")
for param in current_params:
    param_id, name, type_, required = param
    req_str = "required" if required else "optional"
    type_str = type_ if type_ else "null"
    print(f"  ❌ {name:20s} (type: {type_str:10s}, {req_str})")
print()

# Delete incorrect parameter
print("Step 1: Deleting incorrect parameter 'url'...")
cursor.execute("""
    DELETE FROM tool_parameters
    WHERE tool_id = ?
""", (tool_id,))
deleted = cursor.rowcount
print(f"  ✅ Deleted {deleted} parameter(s)")
print()

# Add correct parameters
print("Step 2: Adding correct parameters...")
now = datetime.utcnow().isoformat()

params_to_add = [
    {
        'name': 'query',
        'type': 'string',
        'description': 'Search query to find relevant web pages',
        'required': True,
        'default_value': None,
        'example_value': 'latest AI research papers 2023'
    },
    {
        'name': 'limit',
        'type': 'integer',
        'description': 'Maximum number of search results to return',
        'required': False,
        'default_value': '5',
        'example_value': '10'
    },
    {
        'name': 'lang',
        'type': 'string',
        'description': 'Language code for search results (e.g., "en", "fr")',
        'required': False,
        'default_value': None,
        'example_value': 'en'
    },
    {
        'name': 'country',
        'type': 'string',
        'description': 'Country code for localized search results (e.g., "us", "uk")',
        'required': False,
        'default_value': None,
        'example_value': 'us'
    },
    {
        'name': 'scrapeOptions',
        'type': 'object',
        'description': 'Optional scraping configuration for search results (formats, onlyMainContent, etc.)',
        'required': False,
        'default_value': None,
        'example_value': '{"formats": ["markdown"], "onlyMainContent": true}'
    }
]

for param in params_to_add:
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
        param['name'],
        param['type'],
        param['description'],
        1 if param['required'] else 0,
        param['default_value'],
        param['example_value'],
        now,
        now
    ))
    req_str = "REQUIRED" if param['required'] else "OPTIONAL"
    print(f"  ✅ Added: {param['name']:20s} ({param['type']:10s}) {req_str}")

print()

# Commit
conn.commit()
print("✅ Changes committed to database")
print()

# Verify
cursor.execute("""
    SELECT name, type, description, required, default_value
    FROM tool_parameters
    WHERE tool_id = ?
    ORDER BY required DESC, name
""", (tool_id,))

final_params = cursor.fetchall()
print(f"Final parameters ({len(final_params)}):")
for param in final_params:
    name, type_, desc, required, default_val = param
    req_str = "REQUIRED" if required else "OPTIONAL"
    default_str = f" [default: {default_val}]" if default_val else ""
    print(f"  ✅ {name:20s} ({type_:10s}) {req_str}{default_str}")
    if desc:
        print(f"     └─ {desc[:70]}...")
print()

if len(final_params) == 5:
    print("✅ SUCCESS: firecrawl_search correctly fixed!")
    print("   Was: 1 wrong parameter (url)")
    print("   Now: 5 correct parameters (query, limit, lang, country, scrapeOptions)")
else:
    print(f"⚠️  WARNING: Expected 5 parameters, got {len(final_params)}")

print("=" * 80)

conn.close()
