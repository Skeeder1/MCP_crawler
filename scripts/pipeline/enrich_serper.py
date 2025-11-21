"""
Phase 2.4: Enrich serper-mcp-server parameters
13 tools with ~50 parameters total
Source: https://github.com/garylab/serper-mcp-server schemas.py
"""
import sys
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Complete parameter definitions from GitHub source + reasonable deductions
SERPER_PARAMS = {
    'google_search': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code (e.g., us, uk)'},
        {'name': 'location', 'type': 'string', 'required': 0, 'description': 'Geographic location'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'tbs', 'type': 'string', 'required': 0, 'description': 'Time period filter'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
    ],
    'google_search_autocomplete': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'location', 'type': 'string', 'required': 0, 'description': 'Geographic location'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'autocorrect', 'type': 'boolean', 'required': 0, 'description': 'Enable autocorrect', 'default_value': 'true'},
    ],
    'google_search_shopping': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'location', 'type': 'string', 'required': 0, 'description': 'Geographic location'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'autocorrect', 'type': 'boolean', 'required': 0, 'description': 'Enable autocorrect', 'default_value': 'true'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
    ],
    'google_search_maps': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'll', 'type': 'string', 'required': 0, 'description': 'GPS position and zoom level'},
        {'name': 'placeId', 'type': 'string', 'required': 0, 'description': 'Place identifier'},
        {'name': 'cid', 'type': 'string', 'required': 0, 'description': 'CID identifier'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
    ],
    'google_search_reviews': [
        {'name': 'fid', 'type': 'string', 'required': 1, 'description': 'The FID (Feature ID)'},
        {'name': 'cid', 'type': 'string', 'required': 0, 'description': 'CID identifier'},
        {'name': 'placeId', 'type': 'string', 'required': 0, 'description': 'Place identifier'},
        {'name': 'sortBy', 'type': 'string', 'required': 0, 'description': 'Sort order: mostRelevant, newest, highestRating, lowestRating', 'default_value': 'mostRelevant'},
        {'name': 'topicId', 'type': 'string', 'required': 0, 'description': 'Topic identifier'},
        {'name': 'nextPageToken', 'type': 'string', 'required': 0, 'description': 'Pagination token'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
    ],
    'google_search_patents': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
    ],
    'google_search_lens': [
        {'name': 'url', 'type': 'string', 'required': 1, 'description': 'The URL of the image to search'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
    ],
    'webpage_scrape': [
        {'name': 'url', 'type': 'string', 'required': 1, 'description': 'The URL to scrape'},
        {'name': 'includeMarkdown', 'type': 'boolean', 'required': 0, 'description': 'Include markdown formatting', 'default_value': 'false'},
    ],
    # Deduced parameters for missing tools (based on similar tools)
    'google_search_images': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'location', 'type': 'string', 'required': 0, 'description': 'Geographic location'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
    ],
    'google_search_videos': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'location', 'type': 'string', 'required': 0, 'description': 'Geographic location'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
    ],
    'google_search_places': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'll', 'type': 'string', 'required': 0, 'description': 'GPS position and zoom level'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
    ],
    'google_search_news': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'gl', 'type': 'string', 'required': 0, 'description': 'Country code'},
        {'name': 'location', 'type': 'string', 'required': 0, 'description': 'Geographic location'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'tbs', 'type': 'string', 'required': 0, 'description': 'Time period filter'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
    ],
    'google_search_scholar': [
        {'name': 'q', 'type': 'string', 'required': 1, 'description': 'The query to search for'},
        {'name': 'hl', 'type': 'string', 'required': 0, 'description': 'Language code'},
        {'name': 'page', 'type': 'string', 'required': 0, 'description': 'Page number', 'default_value': '1'},
        {'name': 'num', 'type': 'string', 'required': 0, 'description': 'Results count (max 100)', 'default_value': '10'},
    ],
}

def enrich_serper():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 2.4: ENRICH SERPER-MCP-SERVER")
    print("="*75)

    # Get serper server ID
    cursor.execute("""
        SELECT id, name
        FROM servers
        WHERE name LIKE '%Serper%'
    """)

    server = cursor.fetchone()
    if not server:
        print("\n❌ Serper server not found")
        conn.close()
        return

    server_id, server_name = server
    print(f"\n✅ Found server: {server_name}")

    # Get all tools
    cursor.execute("""
        SELECT id, name, display_name
        FROM tools
        WHERE server_id = ?
        ORDER BY name
    """, (server_id,))

    tools = cursor.fetchall()
    print(f"\n📊 Tools found: {len(tools)}")

    # Create tool_id lookup
    tools_dict = {tool_name: tool_id for tool_id, tool_name, _ in tools}

    total_params_added = 0
    total_params_updated = 0

    for tool_name, params in SERPER_PARAMS.items():
        if tool_name not in tools_dict:
            print(f"\n⚠️  Tool '{tool_name}' not found in DB, skipping...")
            continue

        tool_id = tools_dict[tool_name]
        print(f"\n📝 Processing {tool_name} ({len(params)} params)...")

        for param in params:
            # Check if parameter already exists
            cursor.execute("""
                SELECT id FROM tool_parameters
                WHERE tool_id = ? AND name = ?
            """, (tool_id, param['name']))

            existing = cursor.fetchone()

            if existing:
                # Update existing
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
                total_params_updated += 1
            else:
                # Insert new
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

        print(f"   ✅ {len(params)} parameters processed")

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
    total_params = 0
    for tool_name, param_count in results:
        print(f"   {tool_name}: {param_count} parameters")
        total_params += param_count

    conn.close()

    print("\n" + "="*75)
    print(f"✅ PHASE 2.4 COMPLETE")
    print(f"   Added: {total_params_added} parameters")
    print(f"   Updated: {total_params_updated} parameters")
    print(f"   Total: {total_params} parameters in serper")
    print("="*75)

if __name__ == "__main__":
    enrich_serper()
