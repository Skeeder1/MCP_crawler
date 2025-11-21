"""
Extract current state of database for manual verification
"""
import sys
import sqlite3
import json
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all servers with READMEs
cursor.execute("""
    SELECT
        s.id,
        s.slug,
        s.name,
        mc.content
    FROM servers s
    LEFT JOIN markdown_content mc ON mc.server_id = s.id AND mc.content_type = 'readme'
    WHERE mc.content IS NOT NULL
    ORDER BY s.slug
""")

servers = []
for row in cursor.fetchall():
    server_id, slug, name, readme_content = row

    # Get tools for this server
    cursor.execute("""
        SELECT id, name, display_name, description
        FROM tools
        WHERE server_id = ?
        ORDER BY name
    """, (server_id,))

    tools = []
    for tool_row in cursor.fetchall():
        tool_id, tool_name, display_name, description = tool_row

        # Get parameters for this tool
        cursor.execute("""
            SELECT name, type, description, required, default_value, example_value
            FROM tool_parameters
            WHERE tool_id = ?
            ORDER BY name
        """, (tool_id,))

        params = []
        for param_row in cursor.fetchall():
            param_name, param_type, param_desc, required, default_val, example_val = param_row
            params.append({
                'name': param_name,
                'type': param_type,
                'description': param_desc,
                'required': required == 1,
                'default_value': default_val,
                'example_value': example_val
            })

        tools.append({
            'name': tool_name,
            'display_name': display_name,
            'description': description,
            'parameters': params
        })

    servers.append({
        'slug': slug,
        'name': name,
        'tools': tools,
        'readme_path': f"data/inspection/readmes/{slug}_readme.md"
    })

conn.close()

# Output as JSON for easy reading
output = {
    'total_servers': len(servers),
    'servers': servers
}

print(json.dumps(output, indent=2, ensure_ascii=False))
