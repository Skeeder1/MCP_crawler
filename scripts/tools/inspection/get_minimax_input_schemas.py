"""
Get input_schema from minimax tools to extract parameters
"""
import sys
import sqlite3
import json
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find minimax server
cursor.execute("""
    SELECT id
    FROM servers
    WHERE name LIKE '%MiniMax%'
""")

server = cursor.fetchone()
if server:
    server_id = server[0]

    # Get all tools with their input_schema
    cursor.execute("""
        SELECT name, display_name, input_schema
        FROM tools
        WHERE server_id = ?
        ORDER BY name
    """, (server_id,))

    tools = cursor.fetchall()
    print("="*75)
    print("MINIMAX TOOLS INPUT SCHEMAS")
    print("="*75)

    for tool_name, display_name, input_schema in tools:
        print(f"\n📦 {tool_name}")
        print(f"   Display: {display_name}")
        print(f"   Input Schema:")

        if input_schema:
            try:
                schema = json.loads(input_schema)
                if 'properties' in schema:
                    props = schema['properties']
                    required = schema.get('required', [])

                    for prop_name, prop_details in props.items():
                        prop_type = prop_details.get('type', 'unknown')
                        prop_desc = prop_details.get('description', 'No description')
                        is_required = prop_name in required

                        print(f"      - {prop_name} ({prop_type}, {'required' if is_required else 'optional'})")
                        print(f"        Description: {prop_desc}")

                        # Check for enum values
                        if 'enum' in prop_details:
                            print(f"        Enum: {prop_details['enum']}")

                        # Check for default value
                        if 'default' in prop_details:
                            print(f"        Default: {prop_details['default']}")
                else:
                    print(f"      Schema: {json.dumps(schema, indent=2)}")
            except json.JSONDecodeError:
                print(f"      ❌ Invalid JSON schema")
        else:
            print("      ❌ No schema found")

else:
    print("❌ No minimax server found")

conn.close()
