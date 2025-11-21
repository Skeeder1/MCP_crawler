"""
Migrate SQLite to Supabase in manageable chunks
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Read migration SQL
migration_file = project_root / 'migration.sql'
with open(migration_file, 'r', encoding='utf-8') as f:
    full_sql = f.read()

print("=" * 70)
print("Supabase Migration - Chunked Execution")
print("=" * 70)
print(f"Total SQL size: {len(full_sql):,} characters\n")

# Split into manageable parts
parts = []

# Part 1: TRUNCATE statements (cleanup)
truncate_start = full_sql.find('SET session_replication_role = replica;')
truncate_end = full_sql.find('SET session_replication_role = DEFAULT;') + len('SET session_replication_role = DEFAULT;')
if truncate_start >= 0 and truncate_end > truncate_start:
    truncate_sql = full_sql[truncate_start:truncate_end]
    parts.append(('TRUNCATE_TABLES', truncate_sql))
    print(f"✅ Part 1: TRUNCATE ({len(truncate_sql):,} chars)")

# Part 2: Server INSERTs
servers_pattern = "INSERT INTO mcp_hub.servers"
servers_start = full_sql.find(servers_pattern)
if servers_start >= 0:
    # Find all server inserts
    server_inserts = []
    pos = servers_start
    while pos >= 0:
        next_pos = full_sql.find("INSERT INTO mcp_hub.servers", pos + 1)
        github_pos = full_sql.find("INSERT INTO mcp_hub.github_info", pos)

        if next_pos >= 0 and next_pos < github_pos:
            server_inserts.append(full_sql[pos:next_pos])
            pos = next_pos
        else:
            # Last server insert
            server_inserts.append(full_sql[pos:github_pos])
            break

    servers_sql = ''.join(server_inserts)
    parts.append(('SERVERS', servers_sql))
    print(f"✅ Part 2: SERVERS ({len(servers_sql):,} chars, {len(server_inserts)} inserts)")

# Part 3: GitHub info INSERTs
github_pattern = "INSERT INTO mcp_hub.github_info"
github_start = full_sql.find(github_pattern)
if github_start >= 0:
    markdown_start = full_sql.find("INSERT INTO mcp_hub.markdown_content")
    if markdown_start >= 0:
        github_sql = full_sql[github_start:markdown_start]
        parts.append(('GITHUB_INFO', github_sql))
        print(f"✅ Part 3: GITHUB_INFO ({len(github_sql):,} chars)")

# Part 4: Markdown content (READMEs) - THIS IS THE BIG ONE
markdown_pattern = "INSERT INTO mcp_hub.markdown_content"
markdown_start = full_sql.find(markdown_pattern)
if markdown_start >= 0:
    config_start = full_sql.find("INSERT INTO mcp_hub.mcp_config_npm")
    if config_start >= 0:
        markdown_sql = full_sql[markdown_start:config_start]

        # Split markdown into smaller chunks (max 500KB per chunk)
        MAX_CHUNK_SIZE = 500000
        markdown_inserts = markdown_sql.split('INSERT INTO mcp_hub.markdown_content')

        current_chunk = ""
        chunk_num = 1
        for insert in markdown_inserts:
            if not insert.strip():
                continue

            full_insert = f"INSERT INTO mcp_hub.markdown_content{insert}"

            if len(current_chunk) + len(full_insert) > MAX_CHUNK_SIZE and current_chunk:
                parts.append((f'MARKDOWN_{chunk_num}', current_chunk))
                print(f"✅ Part 4.{chunk_num}: MARKDOWN ({len(current_chunk):,} chars)")
                current_chunk = full_insert
                chunk_num += 1
            else:
                current_chunk += full_insert

        if current_chunk:
            parts.append((f'MARKDOWN_{chunk_num}', current_chunk))
            print(f"✅ Part 4.{chunk_num}: MARKDOWN ({len(current_chunk):,} chars)")

# Part 5: MCP Config NPM
config_pattern = "INSERT INTO mcp_hub.mcp_config_npm"
config_start = full_sql.find(config_pattern)
if config_start >= 0:
    commit_pos = full_sql.find("COMMIT;")
    if commit_pos >= 0:
        config_sql = full_sql[config_start:commit_pos]
        parts.append(('MCP_CONFIG_NPM', config_sql))
        print(f"✅ Part 5: MCP_CONFIG_NPM ({len(config_sql):,} chars)")

print(f"\n📦 Total parts: {len(parts)}")
print("\n" + "=" * 70)
print("Execution Instructions")
print("=" * 70)
print("""
To execute the migration:

1. Run each part sequentially using Supabase MCP tool
2. For each part, use:

   mcp__supabase__execute_sql(
       project_id="fthimebrhmafyqezefkd",
       query="<SQL_FROM_PART>"
   )

3. Order of execution:
   - Part 1: TRUNCATE (cleanup)
   - Part 2: SERVERS (base data)
   - Part 3: GITHUB_INFO (GitHub stats)
   - Parts 4.x: MARKDOWN (READMEs)
   - Part 5: MCP_CONFIG_NPM (configs)
""")

# Save parts to separate files
parts_dir = project_root / 'migration_parts'
parts_dir.mkdir(exist_ok=True)

for i, (name, sql) in enumerate(parts, 1):
    part_file = parts_dir / f"{i:02d}_{name}.sql"
    with open(part_file, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"💾 Saved: {part_file.name} ({len(sql):,} chars)")

print(f"\n✅ All parts saved to: {parts_dir}")
print("\nYou can now execute each part file manually or use the Supabase MCP tool.")
