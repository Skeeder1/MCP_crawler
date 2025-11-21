"""
Phase 2.2: Enrich perplexity parameters
4 tools: perplexity_search, perplexity_ask, perplexity_research, perplexity_reason
"""
import sys
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def enrich_perplexity():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 2.2: ENRICH PERPLEXITY")
    print("="*75)

    # Get perplexity server ID
    cursor.execute("""
        SELECT id, name
        FROM servers
        WHERE name LIKE '%Perplexity%'
    """)

    server = cursor.fetchone()
    if not server:
        print("\n❌ Perplexity server not found")
        conn.close()
        return

    server_id, server_name = server
    print(f"\n✅ Found server: {server_name}")

    # Get all 4 tools
    cursor.execute("""
        SELECT id, name, display_name
        FROM tools
        WHERE server_id = ?
        ORDER BY name
    """, (server_id,))

    tools = cursor.fetchall()
    print(f"\n📊 Tools found: {len(tools)}")
    for tool_id, tool_name, display_name in tools:
        print(f"   - {tool_name}")

    # Parameters to add for each tool
    # All tools get 'query' parameter
    # research and reason also get 'strip_thinking'
    params_to_add = {
        'perplexity_search': [
            {
                'name': 'query',
                'type': 'string',
                'description': 'Search query to find current information',
                'required': 1
            }
        ],
        'perplexity_ask': [
            {
                'name': 'query',
                'type': 'string',
                'description': 'Question or search query for the AI assistant',
                'required': 1
            }
        ],
        'perplexity_research': [
            {
                'name': 'query',
                'type': 'string',
                'description': 'Research topic for deep, comprehensive analysis',
                'required': 1
            },
            {
                'name': 'strip_thinking',
                'type': 'boolean',
                'description': 'Set to true to remove <think>...</think> tags from response, saving context tokens',
                'required': 0,
                'default_value': 'false'
            }
        ],
        'perplexity_reason': [
            {
                'name': 'query',
                'type': 'string',
                'description': 'Complex problem or analytical task for advanced reasoning',
                'required': 1
            },
            {
                'name': 'strip_thinking',
                'type': 'boolean',
                'description': 'Set to true to remove <think>...</think> tags from response, saving context tokens',
                'required': 0,
                'default_value': 'false'
            }
        ]
    }

    total_params_added = 0

    for tool_id, tool_name, display_name in tools:
        if tool_name not in params_to_add:
            print(f"\n⚠️  No parameters defined for {tool_name}")
            continue

        print(f"\n📝 Processing {tool_name}...")
        params = params_to_add[tool_name]

        for param in params:
            # Check if parameter already exists
            cursor.execute("""
                SELECT id FROM tool_parameters
                WHERE tool_id = ? AND name = ?
            """, (tool_id, param['name']))

            existing = cursor.fetchone()

            if existing:
                print(f"   ⚠️  {param['name']} already exists, updating...")
                cursor.execute("""
                    UPDATE tool_parameters
                    SET type = ?, description = ?, required = ?, default_value = ?, updated_at = ?
                    WHERE tool_id = ? AND name = ?
                """, (
                    param['type'],
                    param['description'],
                    param['required'],
                    param.get('default_value'),
                    datetime.now(timezone.utc).isoformat(),
                    tool_id,
                    param['name']
                ))
            else:
                print(f"   ➕ Adding {param['name']} ({param['type']}, {'required' if param['required'] else 'optional'})")
                param_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()

                cursor.execute("""
                    INSERT INTO tool_parameters (
                        id, tool_id, name, type, description,
                        required, default_value, example_value, display_order, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    param_id,
                    tool_id,
                    param['name'],
                    param['type'],
                    param['description'],
                    param['required'],
                    param.get('default_value'),
                    None,
                    0,
                    now,
                    now
                ))
                total_params_added += 1

    conn.commit()

    # Verify results
    print("\n" + "="*75)
    print("VERIFICATION")
    print("="*75)

    cursor.execute("""
        SELECT t.name, COUNT(tp.id) as param_count
        FROM tools t
        LEFT JOIN tool_parameters tp ON t.id = tp.tool_id
        WHERE t.server_id = ?
        GROUP BY t.id, t.name
        ORDER BY t.name
    """, (server_id,))

    results = cursor.fetchall()
    for tool_name, param_count in results:
        print(f"   {tool_name}: {param_count} parameters")

    conn.close()

    print("\n" + "="*75)
    print(f"✅ PHASE 2.2 COMPLETE - Added {total_params_added} parameters to perplexity")
    print("="*75)

if __name__ == "__main__":
    enrich_perplexity()
