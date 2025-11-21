"""
Complete MCP Scraping Pipeline
Orchestrates the full workflow: scrape -> enrich -> parse -> save -> migrate
"""
import sys
import asyncio
import uuid
import json
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
from src.database.models_normalized import (
    Base, Server, MarkdownContent, GithubInfo, NpmInfo,
    McpConfigNpm, Tag, ServerTag
)
from src.enrichers.github_enricher import GitHubEnricher
from src.enrichers.npm_enricher import NpmEnricher
from src.parsers.readme_parser import ReadmeParser
import scripts.scrape_mcp_so as mcp_scraper
import scripts.clean_database as db_cleaner

# Configuration
DB_PATH = project_root / 'data' / 'mcp_servers.db'
MAX_SERVERS = 100


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def slugify(text):
    """Convert text to slug format"""
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


async def main(max_servers=MAX_SERVERS):
    """
    Main pipeline workflow
    """
    print_header("🚀 MCP Full Scraping Pipeline")
    print(f"Target: {max_servers} servers with complete enrichment")

    stats = {
        'scraped': 0,
        'github_enriched': 0,
        'npm_enriched': 0,
        'configs_parsed': 0,
        'saved': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    # ========================================================================
    # Phase 1: Clean Database
    # ========================================================================
    print_header("Phase 1: Cleaning Database 🧹")
    db_cleaner.clean_sqlite_database(DB_PATH)

    # ========================================================================
    # Phase 2: Scrape mcp.so
    # ========================================================================
    print_header("Phase 2: Scraping mcp.so 🌐")

    # Get server URLs
    server_urls = await mcp_scraper.scrape_server_list(max_servers=max_servers)
    if not server_urls:
        print("❌ No servers found")
        return

    print(f"✅ Found {len(server_urls)} server URLs")

    # ========================================================================
    # Phase 3: Scrape + Enrich Each Server
    # ========================================================================
    print_header(f"Phase 3: Scraping & Enriching {len(server_urls)} Servers 🔍")

    # Initialize enrichers
    github_enricher = GitHubEnricher()
    npm_enricher = NpmEnricher()
    await github_enricher.start()
    await npm_enricher.start()

    # Initialize database
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Scraper for individual pages
    scraper = mcp_scraper.BaseScraper(headless=True)
    await scraper.start()

    tags_map = {}

    try:
        for i, url in enumerate(server_urls, 1):
            print(f"\n[{i}/{len(server_urls)}] Processing: {url}")

            try:
                # Step 1: Scrape basic info from mcp.so
                print("  📄 Scraping mcp.so...")
                data = await mcp_scraper.scrape_single_server(scraper, url)

                if not data:
                    print(f"  ❌ Failed to scrape")
                    stats['errors'] += 1
                    continue

                stats['scraped'] += 1

                # Step 2: Enrich with GitHub data
                github_data = None
                readme_content = None

                if data.get('github_url'):
                    owner, repo = mcp_scraper.parse_github_url(data['github_url'])
                    if owner and repo:
                        github_enrichment = await github_enricher.enrich_server(owner, repo)
                        if github_enrichment:
                            github_data = github_enrichment['github_info']
                            readme_content = github_enrichment.get('readme')
                            stats['github_enriched'] += 1

                # Step 3: Enrich with npm data
                npm_data = None
                if data.get('npm_url'):
                    import re
                    npm_match = re.search(r'npmjs\.com/package/(.+)', data['npm_url'])
                    if npm_match:
                        package_name = npm_match.group(1).rstrip('/')
                        npm_data = await npm_enricher.fetch_package_info(package_name)
                        if npm_data:
                            stats['npm_enriched'] += 1

                # Step 4: Parse installation config from README
                config_data = None
                if readme_content:
                    try:
                        parser = ReadmeParser(readme_content['content'])
                        config_data = parser.parse_all()
                        stats['configs_parsed'] += 1
                    except Exception as e:
                        print(f"    ⚠️  Config parsing failed: {e}")

                # Step 5: Save to database
                print("  💾 Saving to database...")
                saved = save_enriched_server(
                    session,
                    data,
                    github_data,
                    npm_data,
                    readme_content,
                    config_data,
                    tags_map
                )

                if saved:
                    session.commit()
                    stats['saved'] += 1
                    print(f"  ✅ Saved: {data.get('name', 'Unknown')}")
                else:
                    session.rollback()
                    stats['errors'] += 1

                # Small delay between servers
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats['errors'] += 1
                session.rollback()
                continue

    finally:
        await scraper.close()
        await github_enricher.close()
        await npm_enricher.close()
        session.close()

    # ========================================================================
    # Final Stats
    # ========================================================================
    print_header("✅ Pipeline Complete!")

    elapsed = (datetime.now() - stats['start_time']).total_seconds()

    print(f"""
    📊 Statistics:
    ──────────────────────────────────────────────────────────────────────
    Servers scraped:          {stats['scraped']:>5}
    GitHub enriched:          {stats['github_enriched']:>5}
    npm enriched:             {stats['npm_enriched']:>5}
    Configs parsed:           {stats['configs_parsed']:>5}
    Servers saved:            {stats['saved']:>5}
    Errors:                   {stats['errors']:>5}
    ──────────────────────────────────────────────────────────────────────
    Time elapsed:             {elapsed/60:.1f} minutes
    Average per server:       {elapsed/max(stats['scraped'], 1):.1f} seconds
    ──────────────────────────────────────────────────────────────────────
    """)

    print(f"✅ Database ready: {DB_PATH}")
    print("\n📌 Next steps:")
    print("   1. Review data in SQLite: python -c \"import sqlite3; ...\"")
    print("   2. Migrate to Supabase: python scripts/migrate_to_supabase_mcp.py")


def save_enriched_server(session, data, github_data, npm_data, readme_content, config_data, tags_map):
    """
    Save server with all enriched data to database
    """
    try:
        # Create server
        server = Server(
            id=str(uuid.uuid4()),
            slug=data['slug'],
            name=data['name'],
            display_name=data['name'],
            tagline=data['description'][:200] if data.get('description') else '',
            short_description=data.get('description', ''),
            creator_name=data.get('author'),
            creator_username=data.get('author') or 'unknown',
            status='approved',
            verification_status='unverified',
            created_at=datetime.utcnow(),
            published_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(server)
        session.flush()

        # Save GitHub info
        if github_data:
            github_info = GithubInfo(
                id=str(uuid.uuid4()),
                server_id=server.id,
                github_url=github_data.get('github_url', ''),
                github_owner=github_data.get('github_owner', ''),
                github_repo=github_data.get('github_repo', ''),
                github_stars=github_data.get('github_stars', 0),
                github_forks=github_data.get('github_forks', 0),
                github_watchers=github_data.get('github_watchers', 0),
                github_open_issues=github_data.get('github_open_issues', 0),
                github_last_commit=github_data.get('github_last_commit'),
                github_created_at=github_data.get('github_created_at'),
                default_branch=github_data.get('default_branch', 'main'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_synced_at=datetime.utcnow()
            )
            session.add(github_info)

        # Save README content
        if readme_content:
            markdown = MarkdownContent(
                id=str(uuid.uuid4()),
                server_id=server.id,
                content_type='readme',
                content=readme_content.get('content', ''),
                word_count=readme_content.get('word_count', 0),
                estimated_reading_time_minutes=readme_content.get('estimated_reading_time_minutes', 0),
                extracted_from=readme_content.get('extracted_from'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(markdown)

        # Save npm info
        if npm_data:
            npm_info = NpmInfo(
                id=str(uuid.uuid4()),
                server_id=server.id,
                npm_package=npm_data.get('npm_package', ''),
                npm_version=npm_data.get('npm_version', '1.0.0'),
                npm_downloads_weekly=npm_data.get('npm_downloads_weekly', 0),
                npm_downloads_monthly=npm_data.get('npm_downloads_monthly', 0),
                npm_license=npm_data.get('npm_license'),
                npm_homepage=npm_data.get('npm_homepage'),
                npm_repository_url=npm_data.get('npm_repository_url'),
                latest_version=npm_data.get('latest_version'),
                latest_version_published_at=npm_data.get('latest_version_published_at'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_synced_at=datetime.utcnow()
            )
            session.add(npm_info)

        # Save MCP config (from parsed README)
        if config_data and config_data.get('installation_config'):
            install_config = config_data['installation_config']

            if install_config.get('type') == 'npm':
                mcp_config = McpConfigNpm(
                    id=str(uuid.uuid4()),
                    server_id=server.id,
                    command=install_config.get('command', 'npx'),
                    args=json.dumps(install_config.get('args', [])),
                    env_required=json.dumps(config_data.get('env_required', [])),
                    env_descriptions=json.dumps(config_data.get('env_descriptions', {})),
                    runtime='node',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(mcp_config)

        # Save tags
        if data.get('tags'):
            for tag_name in data['tags'][:5]:
                tag_slug = slugify(tag_name)

                if tag_slug not in tags_map:
                    tag = Tag(
                        id=str(uuid.uuid4()),
                        slug=tag_slug,
                        name=tag_name.strip(),
                        color='#3B82F6',
                        created_at=datetime.utcnow()
                    )
                    session.add(tag)
                    session.flush()
                    tags_map[tag_slug] = tag
                else:
                    tag = tags_map[tag_slug]

                server_tag = ServerTag(
                    server_id=server.id,
                    tag_id=tag.id,
                    display_order=0,
                    added_at=datetime.utcnow()
                )
                session.add(server_tag)

        session.flush()
        return True

    except Exception as e:
        print(f"    ❌ Error saving: {e}")
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run full MCP scraping pipeline')
    parser.add_argument('--max-servers', type=int, default=MAX_SERVERS,
                        help=f'Maximum number of servers to scrape (default: {MAX_SERVERS})')
    args = parser.parse_args()

    asyncio.run(main(max_servers=args.max_servers))
