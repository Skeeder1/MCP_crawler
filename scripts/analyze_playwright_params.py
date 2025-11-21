"""
Analyze existing playwright parameters to understand patterns
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*75)
print("PLAYWRIGHT TOOLS WITH PARAMETERS - PATTERN ANALYSIS")
print("="*75)

# Get playwright server
cursor.execute("""
    SELECT id
    FROM servers
    WHERE name LIKE '%Playwright%'
""")

server = cursor.fetchone()
if server:
    server_id = server[0]

    # Get all tools with parameters
    cursor.execute("""
        SELECT
            t.name as tool_name,
            tp.name as param_name,
            tp.type,
            tp.required,
            tp.description
        FROM tools t
        JOIN tool_parameters tp ON t.id = tp.tool_id
        WHERE t.server_id = ?
        ORDER BY t.name, tp.display_order, tp.name
    """, (server_id,))

    results = cursor.fetchall()

    # Group by tool
    by_tool = {}
    for row in results:
        tool_name = row[0]
        if tool_name not in by_tool:
            by_tool[tool_name] = []
        by_tool[tool_name].append(row[1:])  # param details

    print(f"\nFound {len(by_tool)} playwright tools with parameters:")
    print()

    for tool_name, params in sorted(by_tool.items()):
        print(f"📦 {tool_name} ({len(params)} params)")
        for param_name, param_type, required, description in params:
            req_str = "required" if required else "optional"
            print(f"   • {param_name} ({param_type}, {req_str})")
            if description:
                desc_short = description[:60] + "..." if len(description) > 60 else description
                print(f"     {desc_short}")
        print()

    # Look for common patterns
    print("="*75)
    print("COMMON PARAMETER PATTERNS")
    print("="*75)

    all_params = {}
    for params in by_tool.values():
        for param_name, param_type, required, description in params:
            if param_name not in all_params:
                all_params[param_name] = []
            all_params[param_name].append((param_type, required))

    print("\nParameter frequency:")
    for param_name, occurrences in sorted(all_params.items(), key=lambda x: len(x[1]), reverse=True):
        types = set([t for t, _ in occurrences])
        req_count = sum([1 for _, r in occurrences if r])
        opt_count = len(occurrences) - req_count
        print(f"   {param_name}: used {len(occurrences)} times (types: {types}, {req_count} req, {opt_count} opt)")

conn.close()
