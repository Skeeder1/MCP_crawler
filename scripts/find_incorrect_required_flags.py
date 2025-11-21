"""
Phase 5: Find parameters with incorrect required/optional flags
Focus on common required parameters like: url, query, prompt, id, task_id, etc.
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Parameters that are typically required based on their names
TYPICALLY_REQUIRED = [
    'url',  # URL is almost always required
    'query',  # Search query is usually required
    'prompt',  # AI prompts are usually required
    'id',  # IDs are usually required
    'task_id',  # Task IDs are usually required
    'text',  # Text input is often required
    'fid',  # FID is usually required
]

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*75)
print("PHASE 5: PARAMETERS WITH POTENTIALLY INCORRECT REQUIRED FLAGS")
print("="*75)

# Find parameters that are probably required but marked as optional
cursor.execute("""
    SELECT
        s.name as server_name,
        t.name as tool_name,
        tp.id as param_id,
        tp.name as param_name,
        tp.type,
        tp.required,
        tp.description
    FROM tool_parameters tp
    JOIN tools t ON tp.tool_id = t.id
    JOIN servers s ON t.server_id = s.id
    WHERE tp.required = 0
    ORDER BY s.name, t.name, tp.name
""")

potentially_incorrect = []
for row in cursor.fetchall():
    server_name, tool_name, param_id, param_name, param_type, required, description = row
    # Check if this parameter name is typically required
    if param_name.lower() in TYPICALLY_REQUIRED:
        potentially_incorrect.append((server_name, tool_name, param_id, param_name, param_type, description))

print(f"\n📊 Found {len(potentially_incorrect)} parameters that are optional but might need to be required\n")

# Group by server
by_server = {}
for row in potentially_incorrect:
    server_name = row[0]
    if server_name not in by_server:
        by_server[server_name] = []
    by_server[server_name].append(row)

for server_name, params in by_server.items():
    print(f"🔸 {server_name} ({len(params)} params)")
    for _, tool_name, param_id, param_name, param_type, description in params:
        print(f"   • {tool_name}.{param_name} (type: {param_type}, currently: OPTIONAL)")
        if description:
            desc_short = description[:80] + "..." if len(description) > 80 else description
            print(f"     Description: {desc_short}")
    print()

# Also check firecrawl specifically for url parameters
print("="*75)
print("FIRECRAWL URL PARAMETERS CHECK")
print("="*75)

cursor.execute("""
    SELECT
        t.name as tool_name,
        tp.name as param_name,
        tp.required
    FROM tool_parameters tp
    JOIN tools t ON tp.tool_id = t.id
    JOIN servers s ON t.server_id = s.id
    WHERE s.name LIKE '%Firecrawl%' AND (tp.name = 'url' OR tp.name = 'urls')
    ORDER BY t.name, tp.name
""")

firecrawl_urls = cursor.fetchall()
print(f"\nFirecrawl URL/URLs parameters:")
for tool_name, param_name, required in firecrawl_urls:
    req_str = "REQUIRED" if required else "OPTIONAL"
    status = "✅" if required else "⚠️ "
    print(f"   {status} {tool_name}.{param_name}: {req_str}")

# Summary
print("\n" + "="*75)
print("SUMMARY")
print("="*75)
print(f"Total parameters potentially requiring correction: {len(potentially_incorrect)}")
print(f"Servers affected: {len(by_server)}")

conn.close()
