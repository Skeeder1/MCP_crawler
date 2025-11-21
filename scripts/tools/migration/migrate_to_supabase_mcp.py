"""
Migrate SQLite data to Supabase using direct SQL execution
Generates PostgreSQL INSERT statements and prints them for execution
"""
import sqlite3
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
PROJECT_ID = 'fthimebrhmafyqezefkd'


def escape_sql(text):
    """Escape single quotes for SQL"""
    if text is None:
        return 'NULL'
    return "'" + str(text).replace("'", "''") + "'"


def generate_server_inserts():
    """Generate INSERT statements for servers table"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM servers")
    servers = cursor.fetchall()

    print(f"\n-- Migrating {len(servers)} servers to mcp_hub.servers")

    inserts = []
    for row in servers:
        sql = f"""INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    {escape_sql(row['id'])},
    {escape_sql(row['slug'])},
    {escape_sql(row['name'])},
    {escape_sql(row['display_name'])},
    {escape_sql(row['tagline'])},
    {escape_sql(row['short_description'])},
    {escape_sql(row['logo_url'])},
    {escape_sql(row['homepage_url'])},
    {row['install_count']},
    {row['favorite_count']},
    {row['tools_count']},
    {escape_sql(row['status'])},
    {escape_sql(row['verification_status'])},
    {escape_sql(row['creator_id'])},
    {escape_sql(row['creator_name'])},
    {escape_sql(row['creator_username'])},
    {escape_sql(row['created_at'])},
    {escape_sql(row['published_at'])},
    {escape_sql(row['updated_at'])}
) ON CONFLICT (id) DO NOTHING;"""
        inserts.append(sql)

    conn.close()
    return inserts


def generate_github_info_inserts():
    """Generate INSERT statements for github_info table"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM github_info")
    rows = cursor.fetchall()

    print(f"\n-- Migrating {len(rows)} github_info entries to mcp_hub.github_info")

    inserts = []
    for row in rows:
        sql = f"""INSERT INTO mcp_hub.github_info
(id, server_id, github_url, github_owner, github_repo, github_stars, github_forks,
 github_watchers, github_open_issues, github_last_commit, github_created_at,
 default_branch, created_at, updated_at, last_synced_at)
VALUES (
    {escape_sql(row['id'])},
    {escape_sql(row['server_id'])},
    {escape_sql(row['github_url'])},
    {escape_sql(row['github_owner'])},
    {escape_sql(row['github_repo'])},
    {row['github_stars']},
    {row['github_forks']},
    {row['github_watchers']},
    {row['github_open_issues']},
    {escape_sql(row['github_last_commit'])},
    {escape_sql(row['github_created_at'])},
    {escape_sql(row['default_branch'])},
    {escape_sql(row['created_at'])},
    {escape_sql(row['updated_at'])},
    {escape_sql(row['last_synced_at'])}
) ON CONFLICT (id) DO NOTHING;"""
        inserts.append(sql)

    conn.close()
    return inserts


def generate_truncate_sql():
    """Generate TRUNCATE statements for clean migration"""
    return """-- =====================================================================
-- CLEANUP: Truncate all tables before migration
-- =====================================================================
SET session_replication_role = replica;

-- Truncate junction tables first
TRUNCATE TABLE mcp_hub.server_tags CASCADE;
TRUNCATE TABLE mcp_hub.server_categories CASCADE;

-- Truncate dependent tables
TRUNCATE TABLE mcp_hub.tools CASCADE;
TRUNCATE TABLE mcp_hub.mcp_config_npm CASCADE;
TRUNCATE TABLE mcp_hub.mcp_config_docker CASCADE;
TRUNCATE TABLE mcp_hub.npm_info CASCADE;
TRUNCATE TABLE mcp_hub.github_info CASCADE;
TRUNCATE TABLE mcp_hub.markdown_content CASCADE;

-- Truncate standalone tables
TRUNCATE TABLE mcp_hub.tags CASCADE;
TRUNCATE TABLE mcp_hub.categories CASCADE;

-- Truncate main table last
TRUNCATE TABLE mcp_hub.servers CASCADE;

SET session_replication_role = DEFAULT;

-- =====================================================================
-- INSERT: Add new data
-- =====================================================================
"""


def generate_all_inserts():
    """Generate INSERT statements for all tables"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    all_inserts = []

    # Check which tables have data
    tables_to_migrate = [
        ('servers', generate_server_inserts),
        ('github_info', generate_github_info_inserts),
        ('npm_info', 'npm_info'),
        ('markdown_content', 'markdown_content'),
        ('mcp_config_npm', 'mcp_config_npm'),
        ('tags', 'tags'),
        ('server_tags', 'server_tags'),
    ]

    for table_name, generator_or_table in tables_to_migrate:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"\n📦 Migrating {count} rows from {table_name}...")

            if callable(generator_or_table):
                # Use existing generator function
                all_inserts.extend(generator_or_table())
            else:
                # Generate generic INSERT statements
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                for row in rows:
                    columns = ', '.join(row.keys())
                    values = ', '.join([escape_sql(row[col]) for col in row.keys()])
                    sql = f"INSERT INTO mcp_hub.{table_name} ({columns}) VALUES ({values}) ON CONFLICT DO NOTHING;"
                    all_inserts.append(sql)

    conn.close()
    return all_inserts


if __name__ == '__main__':
    print("=" * 70)
    print("SQLite to Supabase Migration Script")
    print("=" * 70)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Schema: mcp_hub")
    print(f"SQLite DB: {DB_PATH}")

    # Generate TRUNCATE statements
    truncate_sql = generate_truncate_sql()

    # Generate all INSERT statements
    print("\n" + "=" * 70)
    print("Generating INSERT statements...")
    print("=" * 70)
    all_inserts = generate_all_inserts()

    print(f"\n-- Total INSERT statements: {len(all_inserts)}")
    print("\n-- Combined SQL for execution:")
    print("-" * 70)

    # Combine TRUNCATE + INSERTs into one transaction
    combined_sql = "BEGIN;\n\n" + truncate_sql + "\n" + "\n".join(all_inserts) + "\n\nCOMMIT;"

    # Save to file
    output_file = Path(__file__).parent.parent / 'migration.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_sql)

    print(f"\n✅ SQL written to: {output_file}")
    print(f"   File size: {len(combined_sql):,} bytes")
    print(f"\nExecute this SQL using:")
    print(f'  mcp__supabase__execute_sql(project_id="{PROJECT_ID}", query=<SQL>)')
