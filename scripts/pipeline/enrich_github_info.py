"""
Enrich GitHub Info - Fetch comprehensive GitHub data for all servers
Uses GitHub API to populate enhanced github_info table
"""
import sys
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.enrichers.github_enricher import GitHubEnricher
from src.database.models_normalized import GithubInfo

# Configuration
DB_PATH = project_root / 'data' / 'mcp_servers.db'


async def enrich_github_info(limit: int = None, force: bool = False):
    """
    Enrich GitHub information for all servers

    Args:
        limit: Maximum number of servers to enrich (None = all)
        force: Re-enrich even if already enriched
    """
    print("=" * 80)
    print("GitHub Info Enrichment")
    print("=" * 80)

    # Connect to database
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get all servers with GitHub info
    query = session.query(GithubInfo)

    if not force:
        # Only enrich if not already enriched (github_stars = 0)
        query = query.filter(GithubInfo.github_stars == 0)

    if limit:
        query = query.limit(limit)

    github_infos = query.all()

    if not github_infos:
        print("\n[OK] No servers to enrich!")
        print("   Use --force to re-enrich all servers")
        session.close()
        return

    print(f"\n[INFO] Found {len(github_infos)} server(s) to enrich")
    if limit:
        print(f"   (limited to {limit})")

    stats = {
        'total': len(github_infos),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    # Enrich each server
    async with GitHubEnricher() as enricher:
        for idx, gh_info in enumerate(github_infos, 1):
            owner = gh_info.github_owner
            repo = gh_info.github_repo

            print(f"\n[{idx}/{stats['total']}] Enriching: {owner}/{repo}")

            try:
                # Fetch comprehensive GitHub data
                data = await enricher.fetch_comprehensive_info(owner, repo)

                if data:
                    # Update github_info with comprehensive data
                    gh_info.github_full_name = data.get('github_full_name')
                    gh_info.github_description = data.get('github_description')
                    gh_info.github_stars = data.get('github_stars', 0)
                    gh_info.github_forks = data.get('github_forks', 0)
                    gh_info.github_watchers = data.get('github_watchers', 0)
                    gh_info.github_open_issues = data.get('github_open_issues', 0)
                    gh_info.github_last_commit = data.get('github_last_commit')
                    gh_info.github_created_at = data.get('github_created_at')
                    gh_info.github_updated_at = datetime.utcnow()
                    gh_info.commit_frequency = data.get('commit_frequency', 0)

                    # Languages
                    gh_info.primary_language = data.get('primary_language')
                    gh_info.languages = json.dumps(data.get('languages', {}))
                    gh_info.github_topics = json.dumps(data.get('github_topics', []))

                    # License
                    gh_info.license_name = data.get('license_name')

                    # Contributors
                    gh_info.top_contributors = json.dumps(data.get('top_contributors', []))
                    gh_info.contributors_count = data.get('contributors_count', 0)

                    # Release
                    gh_info.latest_github_version = data.get('latest_github_version')
                    gh_info.latest_release_date = data.get('latest_release_date')
                    gh_info.release_notes = data.get('release_notes')
                    gh_info.is_prerelease = 1 if data.get('is_prerelease') else 0

                    # Community files
                    gh_info.has_readme = 1 if data.get('has_readme') else 0
                    gh_info.has_license = 1 if data.get('has_license') else 0
                    gh_info.has_contributing = 1 if data.get('has_contributing') else 0
                    gh_info.has_code_of_conduct = 1 if data.get('has_code_of_conduct') else 0

                    # Health score
                    gh_info.github_health_score = data.get('github_health_score', 0)

                    # Sync timestamp
                    gh_info.last_synced_at = datetime.utcnow()

                    session.commit()
                    stats['success'] += 1
                    print(f"      [OK] Enriched successfully")

                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"{owner}/{repo}: No data returned")
                    print(f"      [ERROR] Failed to fetch data")

            except Exception as e:
                stats['failed'] += 1
                error_msg = f"{owner}/{repo}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"      [ERROR] Error: {e}")
                session.rollback()

            # Small delay between requests
            if idx < stats['total']:
                await asyncio.sleep(0.5)

        # Show final stats
        print("\n" + "=" * 80)
        print("Enrichment Complete!")
        print("=" * 80)
        print(f"  Total servers:    {stats['total']}")
        print(f"  Successful:       {stats['success']}")
        print(f"  Failed:           {stats['failed']}")

        if stats['errors']:
            print(f"\n[ERROR] Errors ({len(stats['errors'])}):")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"   - {error}")
            if len(stats['errors']) > 10:
                print(f"   ... and {len(stats['errors']) - 10} more")

        # Show rate limit info
        enricher_stats = enricher.get_stats()
        print(f"\n[INFO] API Stats:")
        print(f"  Requests made:    {enricher_stats['requests_made']}")
        print(f"  Rate limit left:  {enricher_stats['rate_limit_remaining']}")

    session.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enrich GitHub information for MCP servers')
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of servers to enrich (default: all)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-enrich all servers even if already enriched'
    )

    args = parser.parse_args()

    # Run async enrichment
    asyncio.run(enrich_github_info(limit=args.limit, force=args.force))


if __name__ == '__main__':
    main()
