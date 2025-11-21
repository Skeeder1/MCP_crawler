"""
Scrape MCPMarket.com and populate normalized database
Simple script to scrape all servers from MCPMarket
"""
import sys
import asyncio
import sqlite3
import uuid
import json
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.scrapers.mcpmarket_scraper import MCPMarketScraper
from src.database.models_normalized import (
    Base, Server, MarkdownContent, GithubInfo, NpmInfo,
    McpConfigNpm, Tool, Tag, ServerTag
)

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Configuration
DB_PATH = project_root / 'data' / 'mcp_servers.db'
SCHEMA_PATH = project_root / 'migrations' / '001_sqlite_normalized_schema.sql'
MCPMARKET_BASE_URL = "https://mcpmarket.com"


def init_database():
    """Initialize database with normalized schema"""
    print("\n" + "=" * 70)
    print("Initializing database...")
    print("=" * 70)

    # Create data directory if needed
    DB_PATH.parent.mkdir(exist_ok=True)

    # Remove old database if exists
    if DB_PATH.exists():
        print(f"Removing existing database: {DB_PATH}")
        try:
            DB_PATH.unlink()
        except PermissionError:
            print("Warning: Could not delete database (file is open)")
            print("Please close any database tools and try again")
            sys.exit(1)

    # Apply schema using raw SQLite
    print(f"Applying schema from: {SCHEMA_PATH.name}")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql_content)
        conn.commit()
        print("✅ Database initialized successfully")
    finally:
        conn.close()

    # Create SQLAlchemy engine
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
    return engine


def parse_github_url(github_url):
    """Extract owner and repo from GitHub URL"""
    if not github_url:
        return None, None

    github_url = github_url.rstrip('.git')
    match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
    if match:
        return match.group(1), match.group(2)
    return None, None


def slugify(text):
    """Convert text to slug format"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def extract_npm_package(npm_url):
    """Extract package name from npm URL"""
    if not npm_url:
        return None

    match = re.search(r'npmjs\.com/package/(.+)', npm_url)
    if match:
        return match.group(1).rstrip('/')
    return None


async def scrape_server_list():
    """Scrape list of all servers from MCPMarket"""
    print("\n" + "=" * 70)
    print("Scraping server list from MCPMarket...")
    print("=" * 70)

    scraper = MCPMarketScraper(headless=True)

    try:
        await scraper.start()
        await scraper.navigate(MCPMARKET_BASE_URL)

        # Wait for page to load (increased timeout)
        await asyncio.sleep(3)  # Give extra time for JS to load
        await scraper.wait_for_selector("a[href^='/server/']", timeout=30000)

        # Get all server links
        server_links = await scraper.get_all_hrefs("a[href^='/server/']")

        # Deduplicate and create full URLs
        unique_links = list(set(server_links))
        server_urls = [f"{MCPMARKET_BASE_URL}{link}" if link.startswith('/') else link
                      for link in unique_links]

        print(f"✅ Found {len(server_urls)} servers")
        return server_urls

    finally:
        await scraper.close()


async def scrape_servers(server_urls, session):
    """Scrape detailed information for each server"""
    print("\n" + "=" * 70)
    print(f"Scraping {len(server_urls)} servers...")
    print("=" * 70)

    scraper = MCPMarketScraper(headless=True)
    stats = {
        'scraped': 0,
        'saved': 0,
        'errors': 0
    }

    # Track unique tags
    tags_map = {}  # tag_slug -> Tag object

    try:
        await scraper.start()

        for i, url in enumerate(server_urls, 1):
            print(f"\n[{i}/{len(server_urls)}] Scraping: {url}")

            try:
                # Scrape server data
                data = await scraper.scrape_server(url)

                if not data:
                    print(f"  ❌ Failed to scrape")
                    stats['errors'] += 1
                    continue

                stats['scraped'] += 1

                # Save to database
                saved = save_server_to_db(session, data, tags_map)
                if saved:
                    stats['saved'] += 1
                    print(f"  ✅ Saved to database")
                else:
                    stats['errors'] += 1
                    print(f"  ❌ Failed to save")

                # Small delay between requests
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats['errors'] += 1
                continue

        # Commit all changes
        session.commit()

        return stats

    finally:
        await scraper.close()


def save_server_to_db(session, data, tags_map):
    """Save scraped server data to normalized database"""
    try:
        # 1. Create server
        server = Server(
            id=str(uuid.uuid4()),
            slug=data['slug'],
            name=data['name'],
            display_name=data['name'],
            tagline=data['description'][:200] if data.get('description') else '',
            short_description=data.get('description', ''),
            logo_url=None,
            homepage_url=None,
            install_count=0,
            favorite_count=0,
            tools_count=0,
            status='approved',
            verification_status='unverified',
            creator_id=None,
            creator_name=data.get('author'),
            creator_username=data.get('author') or 'unknown',
            created_at=datetime.utcnow(),
            published_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(server)
        session.flush()  # Get the server ID

        # 2. Save markdown content (if available)
        content_types = {
            'about': data.get('about'),
            'readme': data.get('readme'),
            'faq': data.get('faq')
        }

        for content_type, content_text in content_types.items():
            if content_text and len(content_text.strip()) > 0:
                markdown = MarkdownContent(
                    id=str(uuid.uuid4()),
                    server_id=server.id,
                    content_type=content_type,
                    content=content_text,
                    word_count=len(content_text.split()),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(markdown)

        # 3. Save GitHub info (if available)
        if data.get('github_url'):
            owner, repo = parse_github_url(data['github_url'])
            if owner and repo:
                github_info = GithubInfo(
                    id=str(uuid.uuid4()),
                    server_id=server.id,
                    github_url=data['github_url'],
                    github_owner=owner,
                    github_repo=repo,
                    github_stars=data.get('stars', 0),
                    github_forks=0,
                    github_watchers=0,
                    github_open_issues=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_synced_at=datetime.utcnow()
                )
                session.add(github_info)

        # 4. Save NPM info (if available)
        npm_package = None
        if data.get('npm_url'):
            npm_package = extract_npm_package(data['npm_url'])

        if npm_package:
            npm_info = NpmInfo(
                id=str(uuid.uuid4()),
                server_id=server.id,
                npm_package=npm_package,
                npm_version='1.0.0',  # Default
                npm_downloads_weekly=0,
                npm_downloads_monthly=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_synced_at=datetime.utcnow()
            )
            session.add(npm_info)

            # 5. Create MCP config (npm)
            mcp_config = McpConfigNpm(
                id=str(uuid.uuid4()),
                server_id=server.id,
                command='npx',
                args=json.dumps(['-y', npm_package]),
                env_required=json.dumps([]),
                env_descriptions=json.dumps({}),
                runtime='node',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(mcp_config)

        # 6. Save tools (if available)
        if data.get('tools') and isinstance(data['tools'], list):
            for tool_data in data['tools']:
                if isinstance(tool_data, dict):
                    tool = Tool(
                        id=str(uuid.uuid4()),
                        server_id=server.id,
                        name=tool_data.get('name', 'unknown'),
                        display_name=tool_data.get('name', 'unknown'),
                        description=tool_data.get('description', ''),
                        input_schema=json.dumps({}),
                        display_order=0,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(tool)

        # 7. Save tags (if available)
        if data.get('tags') and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                tag_slug = slugify(tag_name)

                # Get or create tag
                if tag_slug not in tags_map:
                    tag = Tag(
                        id=str(uuid.uuid4()),
                        slug=tag_slug,
                        name=tag_name.strip(),
                        color='#3B82F6',
                        created_at=datetime.utcnow()
                    )
                    session.add(tag)
                    session.flush()  # Get the tag ID
                    tags_map[tag_slug] = tag
                else:
                    tag = tags_map[tag_slug]

                # Create server-tag relationship
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
        print(f"  Error saving to database: {e}")
        session.rollback()
        return False


def print_stats(engine):
    """Print database statistics"""
    print("\n" + "=" * 70)
    print("Database Statistics")
    print("=" * 70)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        tables = [
            ('servers', Server),
            ('markdown_content', MarkdownContent),
            ('github_info', GithubInfo),
            ('npm_info', NpmInfo),
            ('mcp_config_npm', McpConfigNpm),
            ('tools', Tool),
            ('tags', Tag),
            ('server_tags', ServerTag)
        ]

        for table_name, model in tables:
            count = session.query(model).count()
            print(f"  {table_name:20} : {count:4} rows")

    finally:
        session.close()


async def main():
    """Main scraping workflow"""
    print("=" * 70)
    print("MCPMarket Scraper - Normalized Database")
    print("=" * 70)

    # Step 1: Initialize database
    engine = init_database()

    # Step 2: Scrape server list
    server_urls = await scrape_server_list()

    if not server_urls:
        print("❌ No servers found")
        return

    # Step 3: Scrape each server
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        stats = await scrape_servers(server_urls, session)

        print("\n" + "=" * 70)
        print("Scraping Complete!")
        print("=" * 70)
        print(f"  Servers found:    {len(server_urls)}")
        print(f"  Servers scraped:  {stats['scraped']}")
        print(f"  Servers saved:    {stats['saved']}")
        print(f"  Errors:           {stats['errors']}")

        # Print database stats
        print_stats(engine)

        print("\n✅ Database ready at: data/mcp_servers.db")

    finally:
        session.close()


if __name__ == '__main__':
    asyncio.run(main())
