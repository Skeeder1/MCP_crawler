"""
Rescrape Failed Phase 2 Entries
Resets entries with github_url=NULL to retry with new multi-server detection logic
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models_normalized import McpSoServerUrl

# Database configuration
DB_PATH = project_root / 'data' / 'mcp_servers.db'


def reset_failed_urls(dry_run=False):
    """
    Reset entries with github_url=NULL to pending status for retry

    Args:
        dry_run: If True, only show what would be reset without making changes

    Returns:
        int: Number of entries reset
    """
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Find all entries with no GitHub URL (failed to extract)
        failed_urls = session.query(McpSoServerUrl).filter(
            McpSoServerUrl.github_url == None
        ).all()

        total_found = len(failed_urls)

        print("=" * 70)
        print("RESET FAILED PHASE 2 ENTRIES")
        print("=" * 70)
        print(f"\nFound {total_found} entries with github_url=NULL")

        if total_found == 0:
            print("\n✅ Nothing to reset!")
            return 0

        # Show details
        print(f"\nThese entries will be reset to 'pending' status:\n")
        for idx, url in enumerate(failed_urls[:10], 1):  # Show first 10
            print(f"  {idx}. {url.server_name}")
            print(f"     URL: {url.mcp_so_url}")
            print(f"     Current status: {url.phase2_status}")
            print(f"     Attempts: {url.phase2_attempts}")
            if url.phase2_error:
                print(f"     Error: {url.phase2_error}")
            print()

        if total_found > 10:
            print(f"  ... and {total_found - 10} more")
            print()

        if dry_run:
            print("\n🔍 DRY RUN MODE - No changes made")
            print(f"\nTo actually reset these entries, run:")
            print(f"  python scripts/rescrape_failed_phase2.py --confirm")
            return 0

        # Ask for confirmation
        print("=" * 70)
        print("⚠️  CONFIRMATION REQUIRED")
        print("=" * 70)
        print(f"\nThis will:")
        print(f"  1. Reset phase2_status to 'pending' for {total_found} entries")
        print(f"  2. Reset phase2_attempts to 0")
        print(f"  3. Clear phase2_error messages")
        print(f"\nThese entries will be re-scraped when you run Phase 2 again.")
        print(f"\nType 'yes' to continue, or anything else to cancel:")

        confirmation = input("> ").strip().lower()

        if confirmation != 'yes':
            print("\n❌ Cancelled - No changes made")
            return 0

        # Reset entries
        reset_count = 0
        for url in failed_urls:
            url.phase2_status = 'pending'
            url.phase2_attempts = 0
            url.phase2_error = None
            url.phase2_last_attempt = None
            url.updated_at = datetime.utcnow()
            reset_count += 1

        session.commit()

        print(f"\n✅ SUCCESS: Reset {reset_count} entries to 'pending'")
        print(f"\nNext steps:")
        print(f"  1. Run Phase 2 to re-scrape these entries:")
        print(f"     python scripts/scrape_mcp_so_phase2.py")
        print(f"  2. The new multi-server detection will find additional GitHub URLs")
        print(f"\n💾 Database: {DB_PATH}")

        return reset_count

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 0

    finally:
        session.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Reset failed Phase 2 entries for re-scraping'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually reset entries (without this, runs in dry-run mode)'
    )

    args = parser.parse_args()

    reset_failed_urls(dry_run=not args.confirm)


if __name__ == '__main__':
    main()
