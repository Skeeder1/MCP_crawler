"""
Scrape mcp.so and populate normalized database
Scrapes MCP servers from mcp.so marketplace
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

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.scrapers.base_scraper import BaseScraper
from src.database.models_normalized import (
    Base, Server, MarkdownContent, GithubInfo, NpmInfo,
    McpConfigNpm, Tool, ToolParameter, Tag, ServerTag
)
from src.parsers.tools_parser import ToolsParser
from src.parsers.parameters_parser import ParametersParser
from src.enrichers.github_enricher import GitHubEnricher

# Configuration
DB_PATH = project_root / 'data' / 'mcp_servers.db'
SCHEMA_PATH = project_root / 'migrations' / '001_sqlite_normalized_schema.sql'
MIGRATION_003_PATH = project_root / 'migrations' / '003_add_tool_parameters.sql'
MCP_SO_BASE_URL = "https://mcp.so"
MAX_SERVERS = 300  # Increased buffer to find 100 new servers


def init_database():
    """Initialize database with normalized schema"""
    print("\n" + "=" * 70)
    print("Initializing database...")
    print("=" * 70)

    DB_PATH.parent.mkdir(exist_ok=True)

    if DB_PATH.exists():
        print(f"Removing existing database: {DB_PATH}")
        try:
            DB_PATH.unlink()
        except PermissionError:
            print("Warning: Could not delete database (file is open)")
            print("Please close any database tools and try again")
            sys.exit(1)

    print(f"Applying schema from: {SCHEMA_PATH.name}")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql_content)
        conn.commit()
        print("✅ Base schema applied")

        # Apply migration 003 for tool_parameters table
        print(f"Applying migration: {MIGRATION_003_PATH.name}")
        with open(MIGRATION_003_PATH, 'r', encoding='utf-8') as f:
            migration_content = f.read()
        conn.executescript(migration_content)
        conn.commit()
        print("✅ Database initialized successfully with all migrations")
    finally:
        conn.close()

    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
    return engine


def slugify(text):
    """Convert text to slug format"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def parse_github_url(github_url):
    """Extract owner and repo from GitHub URL"""
    if not github_url:
        return None, None

    github_url = github_url.rstrip('.git')
    match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
    if match:
        return match.group(1), match.group(2)
    return None, None


def server_exists_in_db(session, slug, github_url=None):
    """
    Check if a server already exists in database

    Args:
        session: SQLAlchemy session
        slug: Server slug
        github_url: Optional GitHub URL

    Returns:
        bool: True if server exists, False otherwise
    """
    from sqlalchemy import or_

    # Check by slug first (primary identifier)
    server = session.query(Server).filter(Server.slug == slug).first()
    if server:
        return True

    # If GitHub URL provided, also check github_info table
    if github_url:
        github_info = session.query(GithubInfo).filter(
            GithubInfo.github_url == github_url
        ).first()
        if github_info:
            return True

    return False


async def fetch_readme_from_github(owner, repo):
    """
    Fetch README content from GitHub API

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        README content as string, or None if failed
    """
    try:
        async with GitHubEnricher() as enricher:
            readme_data = await enricher.fetch_readme(owner, repo)
            if readme_data and readme_data.get('content'):
                return readme_data['content']
    except Exception as e:
        print(f"  ⚠️  Could not fetch README from {owner}/{repo}: {e}")
    return None


def extract_tool_section(readme, tool_name):
    """
    Extract specific tool section from README for parameter parsing

    Args:
        readme: Full README content
        tool_name: Name of the tool to extract section for

    Returns:
        Tool section as string, or None if not found
    """
    if not readme or not tool_name:
        return None

    # Try multiple patterns to find the tool section
    patterns = [
        rf'###\s+{re.escape(tool_name)}\s*\n',
        rf'###\s+[^#\n]*{re.escape(tool_name)}[^#\n]*\n',
        rf'\*\*{re.escape(tool_name)}\*\*',
        rf'`{re.escape(tool_name)}`',
    ]

    for pattern in patterns:
        match = re.search(pattern, readme, re.IGNORECASE)
        if match:
            start = match.start()
            # Extract context around the match (200 chars before, 2000 chars after)
            context_start = max(0, start - 200)
            context_end = min(len(readme), start + 2000)
            return readme[context_start:context_end]

    return None


async def scrape_server_list(max_servers=MAX_SERVERS):
    """Scrape list of all server links from mcp.so"""
    print("\n" + "=" * 70)
    print(f"Loading server list from mcp.so (up to {max_servers})...")
    print("=" * 70)

    scraper = BaseScraper(headless=True)
    server_links = set()

    try:
        await scraper.start()
        await scraper.navigate(MCP_SO_BASE_URL)
        await asyncio.sleep(3)

        # Click "Load More" button several times to get more servers
        for i in range(20):  # Increased from 10 to load more servers
            # Get current server links
            current_links = await scraper.get_all_hrefs("a[href^='/server/']")
            server_links.update(current_links)

            print(f"  Loaded {len(server_links)} servers so far...")

            if len(server_links) >= max_servers:
                print(f"  Reached max limit of {max_servers} servers")
                break

            # Try to click "Load More" button
            try:
                load_more = scraper.page.locator("button:has-text('More')")
                if await load_more.count() > 0:
                    await load_more.click()
                    await asyncio.sleep(2)
                else:
                    print("  ℹ️  No more 'Load More' button found")
                    break
            except Exception as e:
                print(f"  ℹ️  Could not click 'Load More': {e}")
                break

        # Convert to full URLs
        server_urls = [f"{MCP_SO_BASE_URL}{link}" if link.startswith('/') else link
                      for link in list(server_links)[:max_servers]]

        print(f"✅ Found {len(server_urls)} server URLs")
        return server_urls

    finally:
        await scraper.close()


async def scrape_servers(server_urls, session, target_new_servers=100):
    """
    Scrape detailed information for each server
    Continues until target_new_servers new servers are collected

    Args:
        server_urls: List of server URLs to scrape
        session: SQLAlchemy session
        target_new_servers: Number of new servers to collect (default: 100)

    Returns:
        dict: Statistics about the scraping process
    """
    print("\n" + "=" * 70)
    print(f"Scraping servers until {target_new_servers} new ones found...")
    print("=" * 70)

    scraper = BaseScraper(headless=True)
    stats = {
        'processed': 0,      # Total URLs examined
        'new_servers': 0,    # New servers successfully saved
        'skipped': 0,        # Servers already in DB
        'errors': 0          # Errors during scraping
    }

    tags_map = {}
    url_index = 0

    try:
        await scraper.start()

        # Continue until we have enough new servers OR run out of URLs
        while stats['new_servers'] < target_new_servers and url_index < len(server_urls):
            url = server_urls[url_index]
            url_index += 1
            stats['processed'] += 1

            print(f"\n[{stats['processed']}] Checking: {url}")
            print(f"  Progress: {stats['new_servers']}/{target_new_servers} new | "
                  f"{stats['skipped']} skipped | {stats['errors']} errors")

            try:
                # Quick check: extract slug from URL
                parts = url.split('/')
                if len(parts) < 5:
                    print(f"  ❌ Invalid URL format")
                    stats['errors'] += 1
                    continue

                server_name = parts[-2]
                preliminary_slug = slugify(server_name)

                # Check if server already exists (by slug only at this stage)
                if server_exists_in_db(session, preliminary_slug):
                    print(f"  ⏭️  SKIPPED: Already in database (slug: {preliminary_slug})")
                    stats['skipped'] += 1
                    continue

                # Server is potentially new, do full scrape
                print(f"  🔍 Scraping details...")
                data = await scrape_single_server(scraper, url)

                if not data:
                    print(f"  ❌ Failed to scrape")
                    stats['errors'] += 1
                    continue

                # Double-check with GitHub URL if available
                if data.get('github_url'):
                    if server_exists_in_db(session, data['slug'], data['github_url']):
                        print(f"  ⏭️  SKIPPED: Already in database (GitHub URL match)")
                        stats['skipped'] += 1
                        continue

                # Server is truly new, save it
                saved = save_server_to_db(session, data, tags_map)
                if saved:
                    session.commit()
                    stats['new_servers'] += 1
                    print(f"  ✅ SAVED: {data.get('name', 'Unknown')} "
                          f"({stats['new_servers']}/{target_new_servers})")
                else:
                    session.rollback()
                    stats['errors'] += 1

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats['errors'] += 1
                session.rollback()
                continue

        # Check if we reached the target
        if stats['new_servers'] >= target_new_servers:
            print(f"\n🎯 Target reached: {stats['new_servers']} new servers collected!")
        else:
            print(f"\n⚠️  Ran out of servers! Only {stats['new_servers']}/{target_new_servers} new servers found.")

        return stats

    finally:
        await scraper.close()


async def scrape_single_server(scraper, url):
    """Scrape a single server page"""
    try:
        success = await scraper.navigate(url)
        if not success:
            return None

        await asyncio.sleep(2)

        # Extract server name from URL: /server/{name}/{owner}
        parts = url.split('/')
        if len(parts) < 5:
            return None

        server_name = parts[-2]
        owner = parts[-1]

        # Get title/name
        name = await scraper.get_text("h1")
        if not name:
            name = server_name

        # Get creator username (from paragraph after h1, format: @username)
        creator_text = await scraper.get_text("h1 + p") or ""
        creator = creator_text.strip('@').strip() if creator_text.startswith('@') else owner

        # Get description (from paragraph after h2)
        description = await scraper.get_text("h2 + p") or ""
        if not description:
            # Fallback to first paragraph in main
            description = await scraper.get_text("main p") or ""

        # Look for GitHub link (inside main content only, exclude issues/pulls)
        # Use main content to avoid navigation/footer links
        github_links = await scraper.get_all_hrefs("main a[href*='github.com']")
        if not github_links:
            # Fallback: exclude issues/pulls links
            github_links = await scraper.get_all_hrefs("a[href*='github.com']:not([href*='/issues']):not([href*='/pulls'])")

        github_url = github_links[0] if github_links else None

        # Clean GitHub URL: remove blob/tree paths for monorepos
        if github_url and ('/blob/' in github_url or '/tree/' in github_url):
            # Extract base repository URL
            # Example: https://github.com/owner/repo/blob/main/src/postgres -> https://github.com/owner/repo
            parts = github_url.split('/blob/')[0] if '/blob/' in github_url else github_url.split('/tree/')[0]
            github_url = parts

        # Look for npm link
        npm_links = await scraper.get_all_hrefs("a[href*='npmjs.com']")
        npm_url = npm_links[0] if npm_links else None

        # Get tags (look for badge/tag elements)
        tags = []
        tag_elements = await scraper.get_all_text("[class*='tag'], [class*='badge']")
        tags = [t.strip() for t in tag_elements if t.strip() and len(t) < 50]

        # Fetch README and extract tools if GitHub URL available
        readme_content = None
        tools = []

        if github_url:
            owner, repo = parse_github_url(github_url)
            if owner and repo:
                print(f"  📖 Fetching README from {owner}/{repo}...")
                readme_content = await fetch_readme_from_github(owner, repo)

                if readme_content:
                    print(f"  🔧 Parsing tools from README...")
                    tools_parser = ToolsParser()
                    parsed_tools = tools_parser.parse_tools(readme_content)

                    if parsed_tools:
                        print(f"  ✅ Found {len(parsed_tools)} tools")
                        params_parser = ParametersParser()

                        for tool_data in parsed_tools:
                            # Extract tool section for parameter parsing
                            tool_section = extract_tool_section(readme_content, tool_data['name'])
                            if tool_section:
                                params = params_parser.parse_parameters(tool_section)
                                tool_data['parameters'] = params
                                if params:
                                    print(f"    └─ {tool_data['name']}: {len(params)} parameters")
                            else:
                                tool_data['parameters'] = []

                        tools = parsed_tools
                    else:
                        print(f"  ⚠️  No tools found in README")

        return {
            'url': url,
            'slug': slugify(server_name),
            'name': name,
            'author': creator,
            'description': description,
            'github_url': github_url,
            'npm_url': npm_url,
            'tags': tags,
            'source': 'mcp.so',
            'readme': readme_content,
            'tools': tools
        }

    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None


def save_server_to_db(session, data, tags_map):
    """Save scraped server data to normalized database"""
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
        if data.get('github_url'):
            owner, repo = parse_github_url(data['github_url'])
            if owner and repo:
                github_info = GithubInfo(
                    id=str(uuid.uuid4()),
                    server_id=server.id,
                    github_url=data['github_url'],
                    github_owner=owner,
                    github_repo=repo,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_synced_at=datetime.utcnow()
                )
                session.add(github_info)

        # Save README as MarkdownContent
        if data.get('readme'):
            markdown_content = MarkdownContent(
                id=str(uuid.uuid4()),
                server_id=server.id,
                content_type='readme',
                content=data['readme'],
                word_count=len(data['readme'].split()),
                estimated_reading_time_minutes=max(1, len(data['readme'].split()) // 200),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(markdown_content)

        # Save tools and parameters
        if data.get('tools'):
            for tool_data in data['tools']:
                tool = Tool(
                    id=str(uuid.uuid4()),
                    server_id=server.id,
                    name=tool_data['name'],
                    display_name=tool_data.get('display_name', tool_data['name']),
                    description=tool_data.get('description', ''),
                    input_schema=json.dumps(tool_data.get('input_schema', {})),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(tool)
                session.flush()  # Flush to get tool.id

                # Save parameters for this tool
                if tool_data.get('parameters'):
                    for param_data in tool_data['parameters']:
                        param = ToolParameter(
                            id=str(uuid.uuid4()),
                            tool_id=tool.id,
                            name=param_data['name'],
                            type=param_data.get('type'),
                            description=param_data.get('description'),
                            required=1 if param_data.get('required') else 0,
                            default_value=param_data.get('default_value'),
                            example_value=param_data.get('example_value'),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        session.add(param)

        # Save npm info
        if data.get('npm_url'):
            npm_match = re.search(r'npmjs\.com/package/(.+)', data['npm_url'])
            if npm_match:
                npm_package = npm_match.group(1).rstrip('/')
                npm_info = NpmInfo(
                    id=str(uuid.uuid4()),
                    server_id=server.id,
                    npm_package=npm_package,
                    npm_version='1.0.0',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_synced_at=datetime.utcnow()
                )
                session.add(npm_info)

                # Create MCP config
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

        # Save tags
        if data.get('tags'):
            for tag_name in data['tags'][:5]:  # Limit to 5 tags
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
        print(f"  Error saving to database: {e}")
        return False


async def main():
    """Main scraping workflow - incremental mode"""
    print("=" * 70)
    print("mcp.so Incremental Scraper → SQLite Database")
    print("=" * 70)

    # Check if database exists
    if not DB_PATH.exists():
        print("\n📦 Database not found, creating new one...")
        engine = init_database()
    else:
        print(f"\n✅ Using existing database: {DB_PATH}")
        print("   (Existing servers will be skipped)")
        engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

    # Scrape server list (load more than needed as buffer)
    print("\n🔍 Step 1: Loading server list from mcp.so...")
    server_urls = await scrape_server_list(max_servers=300)

    if not server_urls:
        print("❌ No servers found on mcp.so")
        return

    print(f"✅ Found {len(server_urls)} total server URLs")

    # Scrape servers until we have 100 new ones
    print("\n🚀 Step 2: Scraping servers (target: 100 new servers)...")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        TARGET_NEW_SERVERS = 100
        stats = await scrape_servers(server_urls, session, target_new_servers=TARGET_NEW_SERVERS)

        print("\n" + "=" * 70)
        print("SCRAPING COMPLETE!")
        print("=" * 70)
        print(f"  Total URLs examined:   {stats['processed']}")
        print(f"  🆕 New servers saved:   {stats['new_servers']}/{TARGET_NEW_SERVERS}")
        print(f"  ⏭️  Servers skipped:     {stats['skipped']} (already in DB)")
        print(f"  ❌ Errors:              {stats['errors']}")
        print("-" * 70)

        if stats['new_servers'] >= TARGET_NEW_SERVERS:
            print(f"✅ SUCCESS: Collected {stats['new_servers']} new servers!")
        else:
            print(f"⚠️  WARNING: Only {stats['new_servers']}/{TARGET_NEW_SERVERS} new servers found.")
            print(f"   This might mean most servers are already in the database,")
            print(f"   or there aren't enough servers on mcp.so.")

        print(f"\n💾 Database: {DB_PATH}")

    finally:
        session.close()


if __name__ == '__main__':
    asyncio.run(main())
