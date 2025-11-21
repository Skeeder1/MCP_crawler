"""
Phase 2.1: Enrich mcp-server-flomo parameters
Tool: write_note
Parameters: content (string, required)
"""
import sys
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def enrich_flomo():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 2.1: ENRICH MCP-SERVER-FLOMO")
    print("="*75)

    # Get write_note tool_id
    cursor.execute("""
        SELECT t.id, t.name, t.display_name, s.name as server_name
        FROM tools t
        JOIN servers s ON t.server_id = s.id
        WHERE s.name = 'mcp-server-flomo MCP Server' AND t.name = 'write_note'
    """)

    tool = cursor.fetchone()
    if not tool:
        print("\n❌ Tool 'write_note' not found in mcp-server-flomo")
        conn.close()
        return

    tool_id, tool_name, display_name, server_name = tool
    print(f"\n✅ Found tool: {tool_name} (ID: {tool_id})")
    print(f"   Server: {server_name}")

    # Check current parameters
    cursor.execute("""
        SELECT name, type, required, description
        FROM tool_parameters
        WHERE tool_id = ?
    """, (tool_id,))

    current_params = cursor.fetchall()
    print(f"\n📊 Current parameters: {len(current_params)}")
    for param in current_params:
        print(f"   - {param[0]} ({param[1]}, required={param[2]})")

    # Parameter to add
    param_to_add = {
        'id': str(uuid.uuid4()),
        'tool_id': tool_id,
        'name': 'content',
        'type': 'string',
        'description': 'Text content to write to Flomo',
        'required': 1,  # 1 = required
        'default_value': None,
        'example_value': None,
        'display_order': 0,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

    # Check if parameter already exists
    cursor.execute("""
        SELECT id FROM tool_parameters
        WHERE tool_id = ? AND name = ?
    """, (tool_id, param_to_add['name']))

    existing = cursor.fetchone()

    if existing:
        print(f"\n⚠️  Parameter 'content' already exists, updating...")
        cursor.execute("""
            UPDATE tool_parameters
            SET type = ?, description = ?, required = ?, updated_at = ?
            WHERE tool_id = ? AND name = ?
        """, (
            param_to_add['type'],
            param_to_add['description'],
            param_to_add['required'],
            param_to_add['updated_at'],
            tool_id,
            param_to_add['name']
        ))
    else:
        print(f"\n➕ Adding parameter 'content'...")
        cursor.execute("""
            INSERT INTO tool_parameters (
                id, tool_id, name, type, description,
                required, default_value, example_value, display_order, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            param_to_add['id'],
            param_to_add['tool_id'],
            param_to_add['name'],
            param_to_add['type'],
            param_to_add['description'],
            param_to_add['required'],
            param_to_add['default_value'],
            param_to_add['example_value'],
            param_to_add['display_order'],
            param_to_add['created_at'],
            param_to_add['updated_at']
        ))

    conn.commit()

    # Verify
    cursor.execute("""
        SELECT name, type, required, description
        FROM tool_parameters
        WHERE tool_id = ?
    """, (tool_id,))

    final_params = cursor.fetchall()
    print(f"\n✅ Final parameters count: {len(final_params)}")
    for param in final_params:
        required_str = "required" if param[2] else "optional"
        print(f"   - {param[0]} ({param[1]}, {required_str})")
        print(f"     Description: {param[3]}")

    conn.close()
    print("\n" + "="*75)
    print("✅ PHASE 2.1 COMPLETE - mcp-server-flomo enriched")
    print("="*75)

if __name__ == "__main__":
    enrich_flomo()
