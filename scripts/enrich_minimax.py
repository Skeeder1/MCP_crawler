"""
Phase 2.3: Enrich minimax-mcp parameters
9 tools with ~46 parameters total
Source: https://github.com/MiniMax-AI/MiniMax-MCP server.py
"""
import sys
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Complete parameter definitions from GitHub source
MINIMAX_PARAMS = {
    'text_to_audio': [
        {'name': 'text', 'type': 'string', 'required': 1, 'description': 'Text to convert to speech'},
        {'name': 'voice_id', 'type': 'string', 'required': 0, 'description': 'Voice identifier (e.g., "male-qn-qingse")', 'default_value': 'DEFAULT_VOICE_ID'},
        {'name': 'model', 'type': 'string', 'required': 0, 'description': 'Model to use', 'default_value': 'DEFAULT_SPEECH_MODEL'},
        {'name': 'speed', 'type': 'number', 'required': 0, 'description': 'Speech speed: 0.5-2.0', 'default_value': 'DEFAULT_SPEED'},
        {'name': 'vol', 'type': 'number', 'required': 0, 'description': 'Volume level: 0-10', 'default_value': 'DEFAULT_VOLUME'},
        {'name': 'pitch', 'type': 'integer', 'required': 0, 'description': 'Pitch adjustment: -12 to 12', 'default_value': 'DEFAULT_PITCH'},
        {'name': 'emotion', 'type': 'string', 'required': 0, 'description': 'Emotion: happy, sad, angry, fearful, disgusted, surprised, neutral', 'default_value': 'DEFAULT_EMOTION'},
        {'name': 'sample_rate', 'type': 'integer', 'required': 0, 'description': 'Values: 8000, 16000, 22050, 24000, 32000, 44100', 'default_value': 'DEFAULT_SAMPLE_RATE'},
        {'name': 'bitrate', 'type': 'integer', 'required': 0, 'description': 'Values: 32000, 64000, 128000, 256000', 'default_value': 'DEFAULT_BITRATE'},
        {'name': 'channel', 'type': 'integer', 'required': 0, 'description': 'Channels: 1 or 2', 'default_value': 'DEFAULT_CHANNEL'},
        {'name': 'format', 'type': 'string', 'required': 0, 'description': 'Values: pcm, mp3, flac', 'default_value': 'DEFAULT_FORMAT'},
        {'name': 'language_boost', 'type': 'string', 'required': 0, 'description': 'Language: Chinese, English, Arabic, Russian, Spanish, French, Portuguese, German, Turkish, Dutch, Ukrainian, Vietnamese, Indonesian, Japanese, Italian, Korean, Thai, Polish, Romanian, Greek, Czech, Finnish, Hindi, auto', 'default_value': 'DEFAULT_LANGUAGE_BOOST'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
    ],
    'list_voices': [
        {'name': 'voice_type', 'type': 'string', 'required': 0, 'description': 'Filter: all, system, voice_cloning', 'default_value': 'all'},
    ],
    'voice_clone': [
        {'name': 'voice_id', 'type': 'string', 'required': 1, 'description': 'Voice identifier for cloned voice'},
        {'name': 'file', 'type': 'string', 'required': 1, 'description': 'Audio file path or URL'},
        {'name': 'text', 'type': 'string', 'required': 0, 'description': 'Text for demo audio'},
        {'name': 'is_url', 'type': 'boolean', 'required': 0, 'description': 'Whether file is a URL', 'default_value': 'false'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
    ],
    'generate_video': [
        {'name': 'prompt', 'type': 'string', 'required': 1, 'description': 'Video generation prompt; Director model supports camera movement instructions'},
        {'name': 'model', 'type': 'string', 'required': 0, 'description': 'Values: T2V-01, T2V-01-Director, I2V-01, I2V-01-Director, I2V-01-live, MiniMax-Hailuo-02', 'default_value': 'DEFAULT_T2V_MODEL'},
        {'name': 'first_frame_image', 'type': 'string', 'required': 0, 'description': 'Image path or URL for I2V models'},
        {'name': 'duration', 'type': 'integer', 'required': 0, 'description': 'Video length (6 or 10 seconds, MiniMax-Hailuo-02 only)'},
        {'name': 'resolution', 'type': 'string', 'required': 0, 'description': 'Values: 768P, 1080P (MiniMax-Hailuo-02 only)'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
        {'name': 'async_mode', 'type': 'boolean', 'required': 0, 'description': 'Submit asynchronously; use query_video_generation to check status', 'default_value': 'false'},
    ],
    'query_video_generation': [
        {'name': 'task_id', 'type': 'string', 'required': 1, 'description': 'Task identifier from generate_video'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
    ],
    'text_to_image': [
        {'name': 'prompt', 'type': 'string', 'required': 1, 'description': 'Image generation prompt'},
        {'name': 'model', 'type': 'string', 'required': 0, 'description': 'Values: image-01', 'default_value': 'DEFAULT_T2I_MODEL'},
        {'name': 'aspect_ratio', 'type': 'string', 'required': 0, 'description': 'Values: 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9', 'default_value': '1:1'},
        {'name': 'n', 'type': 'integer', 'required': 0, 'description': 'Number of images: 1-9', 'default_value': '1'},
        {'name': 'prompt_optimizer', 'type': 'boolean', 'required': 0, 'description': 'Optimize the prompt', 'default_value': 'true'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
    ],
    'music_generation': [
        {'name': 'prompt', 'type': 'string', 'required': 1, 'description': 'Music inspiration (10-300 characters)'},
        {'name': 'lyrics', 'type': 'string', 'required': 1, 'description': 'Song lyrics with optional structure tags (10-600 characters)'},
        {'name': 'sample_rate', 'type': 'integer', 'required': 0, 'description': 'Values: 16000, 24000, 32000, 44100', 'default_value': 'DEFAULT_SAMPLE_RATE'},
        {'name': 'bitrate', 'type': 'integer', 'required': 0, 'description': 'Values: 32000, 64000, 128000, 256000', 'default_value': 'DEFAULT_BITRATE'},
        {'name': 'format', 'type': 'string', 'required': 0, 'description': 'Values: mp3, wav, pcm', 'default_value': 'DEFAULT_FORMAT'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
    ],
    'voice_design': [
        {'name': 'prompt', 'type': 'string', 'required': 1, 'description': 'Voice generation prompt'},
        {'name': 'preview_text', 'type': 'string', 'required': 1, 'description': 'Text to preview the generated voice'},
        {'name': 'voice_id', 'type': 'string', 'required': 0, 'description': 'Base voice identifier (optional refinement)'},
        {'name': 'output_directory', 'type': 'string', 'required': 0, 'description': 'Destination directory', 'default_value': '~/Desktop'},
    ],
}

def enrich_minimax():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 2.3: ENRICH MINIMAX-MCP")
    print("="*75)

    # Get minimax server ID
    cursor.execute("""
        SELECT id, name
        FROM servers
        WHERE name LIKE '%MiniMax%'
    """)

    server = cursor.fetchone()
    if not server:
        print("\n❌ Minimax server not found")
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

    for tool_name, params in MINIMAX_PARAMS.items():
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
    print(f"✅ PHASE 2.3 COMPLETE")
    print(f"   Added: {total_params_added} parameters")
    print(f"   Updated: {total_params_updated} parameters")
    print(f"   Total: {total_params} parameters in minimax")
    print("="*75)

if __name__ == "__main__":
    enrich_minimax()
