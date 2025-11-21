"""
Scrape 1000 servers from mcp.so and extract GitHub URLs
Lightweight script focused on GitHub URL collection
"""
import sys
import asyncio
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.scrapers.base_scraper import BaseScraper

# Configuration
DB_PATH = project_root / 'data' / 'mcp_servers.db'
OUTPUT_FILE = project_root / 'data' / 'github_urls_1000.json'
MCP_SO_BASE_URL = "https://mcp.so"
TARGET_SERVERS = 1000


async def scrape_server_links(max_servers=TARGET_SERVERS):
    """
    Scrape server links from mcp.so with pagination

    Returns:
        List of server URLs
    """
    print("\n" + "=" * 70)
    print(f"🔍 Scraping up to {max_servers} servers from mcp.so...")
    print("=" * 70)

    scraper = BaseScraper(headless=True)
    server_links = set()
    page = 1
    consecutive_empty = 0

    try:
        await scraper.start()

        while len(server_links) < max_servers:
            url = f"{MCP_SO_BASE_URL}/?page={page}"
            print(f"\n📄 Page {page} - Collected: {len(server_links)}/{max_servers}")

            await scraper.navigate(url)
            await asyncio.sleep(2)  # Wait for page load

            # Extract server links
            html = await scraper.get_html()

            # Find all server links (pattern: /servers/slug)
            import re
            links = re.findall(r'href="(/servers/[^"]+)"', html)

            if not links:
                consecutive_empty += 1
                print(f"  ⚠️  No links found on page {page}")

                if consecutive_empty >= 3:
                    print("\n⛔ Stopped: 3 consecutive empty pages")
                    break
            else:
                consecutive_empty = 0
                new_links = 0

                for link in links:
                    full_url = f"{MCP_SO_BASE_URL}{link}"
                    if full_url not in server_links:
                        server_links.add(full_url)
                        new_links += 1

                        if len(server_links) >= max_servers:
                            break

                print(f"  ✅ Found {new_links} new server(s)")

            page += 1

            # Anti-detection delay
            await asyncio.sleep(3)

        print(f"\n✅ Total servers found: {len(server_links)}")
        return list(server_links)

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        return list(server_links)
    finally:
        await scraper.close()


async def extract_github_url_from_server(scraper, server_url):
    """
    Extract GitHub URL from a single server page

    Args:
        scraper: BaseScraper instance
        server_url: URL of server page

    Returns:
        Dict with server info and GitHub URL
    """
    try:
        await scraper.navigate(server_url)
        await asyncio.sleep(1)

        html = await scraper.get_html()

        # Extract server slug from URL
        slug = server_url.split('/servers/')[-1].split('?')[0]

        # Find GitHub URL (pattern: https://github.com/...)
        import re
        github_match = re.search(r'https://github\.com/[^"\'<>\s]+', html)
        github_url = github_match.group(0) if github_match else None

        # Extract server name
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        name = name_match.group(1).strip() if name_match else slug

        return {
            'slug': slug,
            'name': name,
            'mcp_so_url': server_url,
            'github_url': github_url,
            'scraped_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"  ❌ Error extracting from {server_url}: {e}")
        return None


async def scrape_all_github_urls(server_urls):
    """
    Scrape GitHub URLs from all server pages

    Args:
        server_urls: List of server URLs

    Returns:
        List of server data dicts
    """
    print("\n" + "=" * 70)
    print(f"📥 Extracting GitHub URLs from {len(server_urls)} servers...")
    print("=" * 70)

    scraper = BaseScraper(headless=True)
    results = []

    try:
        await scraper.start()

        for i, server_url in enumerate(server_urls, 1):
            print(f"\n[{i}/{len(server_urls)}] Processing: {server_url}")

            data = await extract_github_url_from_server(scraper, server_url)

            if data:
                results.append(data)

                if data['github_url']:
                    print(f"  ✅ GitHub: {data['github_url']}")
                else:
                    print(f"  ⚠️  No GitHub URL found")

            # Anti-detection delay
            await asyncio.sleep(2)

            # Progress update every 50 servers
            if i % 50 == 0:
                github_count = sum(1 for r in results if r.get('github_url'))
                print(f"\n📊 Progress: {i}/{len(server_urls)} | GitHub URLs: {github_count}")

        return results

    except Exception as e:
        print(f"\n❌ Error during GitHub URL extraction: {e}")
        return results
    finally:
        await scraper.close()


def save_results(results, output_file):
    """Save results to JSON file"""
    print("\n" + "=" * 70)
    print("💾 Saving results...")
    print("=" * 70)

    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)

    # Calculate statistics
    total = len(results)
    with_github = sum(1 for r in results if r.get('github_url'))
    without_github = total - with_github

    output_data = {
        'metadata': {
            'scraped_at': datetime.utcnow().isoformat(),
            'total_servers': total,
            'servers_with_github': with_github,
            'servers_without_github': without_github,
            'github_coverage': f"{(with_github/total*100):.1f}%" if total > 0 else "0%"
        },
        'servers': results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {output_file}")
    print(f"\n📊 Statistics:")
    print(f"  • Total servers: {total}")
    print(f"  • With GitHub URL: {with_github} ({with_github/total*100:.1f}%)")
    print(f"  • Without GitHub URL: {without_github} ({without_github/total*100:.1f}%)")

    # Also save GitHub URLs only to a simple text file
    github_urls_only = [r['github_url'] for r in results if r.get('github_url')]
    urls_file = output_file.parent / 'github_urls_only.txt'

    with open(urls_file, 'w', encoding='utf-8') as f:
        for url in github_urls_only:
            f.write(url + '\n')

    print(f"\n✅ GitHub URLs list saved to: {urls_file}")


async def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("🚀 MCP GitHub URLs Scraper")
    print("=" * 70)
    print(f"Target: {TARGET_SERVERS} servers")
    print(f"Output: {OUTPUT_FILE}")

    start_time = datetime.now()

    # Step 1: Scrape server links
    server_urls = await scrape_server_links(max_servers=TARGET_SERVERS)

    if not server_urls:
        print("\n❌ No servers found. Exiting.")
        return

    # Step 2: Extract GitHub URLs from each server
    results = await scrape_all_github_urls(server_urls)

    # Step 3: Save results
    save_results(results, OUTPUT_FILE)

    # Summary
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("✅ SCRAPING COMPLETED")
    print("=" * 70)
    print(f"⏱️  Total time: {elapsed}")
    print(f"📁 Output files:")
    print(f"   • JSON (full data): {OUTPUT_FILE}")
    print(f"   • TXT (URLs only): {OUTPUT_FILE.parent / 'github_urls_only.txt'}")
    print("=" * 70)


if __name__ == '__main__':
    asyncio.run(main())
