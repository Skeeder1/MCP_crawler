"""
Phase 4: Find tools and parameters with description artifacts
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
print("PHASE 4: DESCRIPTIONS WITH ARTIFACTS")
print("="*75)

# Common artifact patterns
ARTIFACT_PATTERNS = [
    '- Title:',
    '- Description:',
    '**Title**:',
    '**Description**:',
    '• ',
    '- ',
]

# Find tools with artifact descriptions
print("\n🔍 Checking TOOL descriptions...")
cursor.execute("""
    SELECT s.name, t.name, t.description
    FROM tools t
    JOIN servers s ON t.server_id = s.id
    WHERE t.description IS NOT NULL
    ORDER BY s.name, t.name
""")

tools_with_artifacts = []
for server_name, tool_name, description in cursor.fetchall():
    if description:
        for pattern in ARTIFACT_PATTERNS:
            if description.startswith(pattern):
                tools_with_artifacts.append((server_name, tool_name, description, pattern))
                break

print(f"Found {len(tools_with_artifacts)} tools with artifact descriptions\n")

# Group by server
by_server = {}
for row in tools_with_artifacts:
    server_name = row[0]
    if server_name not in by_server:
        by_server[server_name] = []
    by_server[server_name].append(row)

for server_name, items in by_server.items():
    print(f"🔸 {server_name} ({len(items)} tools)")
    for _, tool_name, description, pattern in items:
        print(f"   • {tool_name}")
        print(f"     Pattern: '{pattern}'")
        desc_short = description[:80] + "..." if len(description) > 80 else description
        print(f"     Current: {desc_short}")
    print()

# Find parameters with artifact descriptions
print("="*75)
print("\n🔍 Checking PARAMETER descriptions...")
cursor.execute("""
    SELECT
        s.name as server_name,
        t.name as tool_name,
        tp.name as param_name,
        tp.description
    FROM tool_parameters tp
    JOIN tools t ON tp.tool_id = t.id
    JOIN servers s ON t.server_id = s.id
    WHERE tp.description IS NOT NULL
    ORDER BY s.name, t.name, tp.name
""")

params_with_artifacts = []
for server_name, tool_name, param_name, description in cursor.fetchall():
    if description:
        for pattern in ARTIFACT_PATTERNS:
            if description.startswith(pattern):
                params_with_artifacts.append((server_name, tool_name, param_name, description, pattern))
                break

print(f"Found {len(params_with_artifacts)} parameters with artifact descriptions\n")

if params_with_artifacts:
    by_server_params = {}
    for row in params_with_artifacts:
        server_name = row[0]
        if server_name not in by_server_params:
            by_server_params[server_name] = []
        by_server_params[server_name].append(row)

    for server_name, items in by_server_params.items():
        print(f"🔸 {server_name} ({len(items)} params)")
        for _, tool_name, param_name, description, pattern in items:
            print(f"   • {tool_name}.{param_name}")
            print(f"     Pattern: '{pattern}'")
            desc_short = description[:80] + "..." if len(description) > 80 else description
            print(f"     Current: {desc_short}")
        print()

# Summary
print("="*75)
print("SUMMARY")
print("="*75)
print(f"Tools with artifacts: {len(tools_with_artifacts)}")
print(f"Parameters with artifacts: {len(params_with_artifacts)}")
print(f"Total: {len(tools_with_artifacts) + len(params_with_artifacts)}")

conn.close()
