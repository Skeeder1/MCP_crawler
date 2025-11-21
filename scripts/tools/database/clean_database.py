"""
Database Cleanup Utility
Truncates all tables in the mcp_hub database in the correct order
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def clean_sqlite_database(db_path):
    """Clean all tables in SQLite database"""
    import sqlite3

    print("\n" + "=" * 70)
    print("Cleaning SQLite Database")
    print("=" * 70)
    print(f"Database: {db_path}")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Tables in correct deletion order (respecting foreign keys)
        tables = [
            'server_tags',
            'server_categories',
            'tools',
            'mcp_config_npm',
            'mcp_config_docker',
            'npm_info',
            'github_info',
            'markdown_content',
            'tags',
            'categories',
            'servers'
        ]

        print("\nDeleting data from tables...")
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                deleted = cursor.rowcount
                print(f"  ✅ {table:25} - Deleted {deleted} rows")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    print(f"  ⚠️  {table:25} - Table does not exist")
                else:
                    raise

        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        conn.commit()
        print("\n✅ Database cleaned successfully")
        return True

    except Exception as e:
        print(f"\n❌ Error cleaning database: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def clean_supabase_database():
    """Clean all tables in Supabase mcp_hub schema"""
    print("\n" + "=" * 70)
    print("Cleaning Supabase Database (mcp_hub schema)")
    print("=" * 70)

    # SQL to truncate all tables in correct order
    truncate_sql = """
-- Disable triggers temporarily
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

-- Re-enable triggers
SET session_replication_role = DEFAULT;
"""

    print("\nSQL to execute on Supabase:")
    print("-" * 70)
    print(truncate_sql)
    print("-" * 70)

    return truncate_sql


def main():
    """Main cleanup function"""
    import argparse

    parser = argparse.ArgumentParser(description='Clean MCP database')
    parser.add_argument('--sqlite', action='store_true', help='Clean SQLite database')
    parser.add_argument('--supabase', action='store_true', help='Generate Supabase cleanup SQL')
    parser.add_argument('--both', action='store_true', help='Clean both databases')
    args = parser.parse_args()

    if not any([args.sqlite, args.supabase, args.both]):
        # Default: clean both
        args.both = True

    success = True

    if args.sqlite or args.both:
        db_path = project_root / 'data' / 'mcp_servers.db'
        if not clean_sqlite_database(db_path):
            success = False

    if args.supabase or args.both:
        sql = clean_supabase_database()
        print("\nℹ️  To execute on Supabase, copy the SQL above and run it using:")
        print("   python scripts/migrate_to_supabase_mcp.py --execute-sql")

    print("\n" + "=" * 70)
    if success:
        print("✅ Cleanup complete!")
    else:
        print("❌ Cleanup completed with errors")
    print("=" * 70)


if __name__ == '__main__':
    main()
