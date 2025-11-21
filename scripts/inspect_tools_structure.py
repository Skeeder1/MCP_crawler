"""
Inspect mcp.so structure to understand how to extract tools information
"""
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.base_scraper import BaseScraper

# Test servers - diverse mix
TEST_SERVERS = [
    "https://mcp.so/server/perplexity",           # Popular, likely has tools
    "https://mcp.so/server/brave-search",         # Search tool
    "https://mcp.so/server/gitlab",               # Git operations
    "https://mcp.so/server/puppeteer",            # Browser automation
    "https://mcp.so/server/postgres",             # Database operations
]

async def inspect_server_page(scraper, url, index):
    """Inspect a single server page for tools structure"""
    print(f"\n{'='*70}")
    print(f"[{index+1}/5] Inspecting: {url}")
    print(f"{'='*70}")

    try:
        # Navigate to page
        print(f"  Navigating to {url}...")
        await scraper.navigate(url)
        await asyncio.sleep(2)  # Wait for page to load

        # Get server slug from URL
        slug = url.split('/')[-1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save screenshot
        screenshot_path = project_root / 'data' / 'inspection' / f"{slug}_{timestamp}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await scraper.page.screenshot(path=str(screenshot_path))
        print(f"  Screenshot saved: {screenshot_path}")

        # Save HTML
        html_path = project_root / 'data' / 'inspection' / f"{slug}_{timestamp}.html"
        html_content = await scraper.page.content()
        html_path.write_text(html_content, encoding='utf-8')
        print(f"  HTML saved: {html_path}")

        # Try to find tools section with various selectors
        print(f"\n  Searching for tools section...")

        tools_selectors = [
            # ID-based
            "#tools",
            "[id*='tool']",
            "[id*='Tools']",

            # Class-based
            ".tools",
            "[class*='tool']",
            "[class*='Tools']",

            # Heading-based
            "h2:has-text('Tools')",
            "h3:has-text('Tools')",

            # Section-based
            "section:has-text('Tools')",
            "div:has-text('Tools')",

            # Data attributes
            "[data-section='tools']",
            "[data-component*='tool']",
        ]

        found_selectors = []
        for selector in tools_selectors:
            try:
                element = await scraper.page.query_selector(selector)
                if element:
                    # Check if element has meaningful content
                    text = await element.text_content()
                    if text and len(text.strip()) > 0:
                        found_selectors.append({
                            'selector': selector,
                            'text_preview': text[:100].strip()
                        })
            except Exception as e:
                # Some selectors might not work, that's ok
                pass

        if found_selectors:
            print(f"  Found {len(found_selectors)} potential tools sections:")
            for item in found_selectors[:5]:  # Show first 5
                print(f"    Selector: {item['selector']}")
                print(f"    Content:  {item['text_preview']}")
                print()
        else:
            print(f"  NO tools sections found with standard selectors")

        # Try to extract any list items that might be tools
        print(f"\n  Searching for list items...")
        list_selectors = [
            "ul > li",
            "ol > li",
            "[role='listitem']",
            ".list-item",
        ]

        for selector in list_selectors:
            try:
                items = await scraper.page.query_selector_all(selector)
                if len(items) > 0:
                    print(f"    {selector}: {len(items)} items")

                    # Sample first 3 items
                    for i, item in enumerate(items[:3]):
                        text = await item.text_content()
                        if text:
                            print(f"      [{i+1}] {text[:60].strip()}...")
            except:
                pass

        # Check for JSON-LD structured data
        print(f"\n  Checking for JSON-LD structured data...")
        json_ld_selector = 'script[type="application/ld+json"]'
        json_scripts = await scraper.page.query_selector_all(json_ld_selector)
        if json_scripts:
            print(f"    Found {len(json_scripts)} JSON-LD scripts")
            for i, script in enumerate(json_scripts[:2]):
                content = await script.text_content()
                if content and 'tool' in content.lower():
                    print(f"      Script {i+1} contains 'tool':")
                    print(f"      {content[:150]}...")
        else:
            print(f"    No JSON-LD found")

        # Get page title for reference
        title = await scraper.page.title()
        print(f"\n  Page title: {title}")

        print(f"\n  Inspection complete for {slug}")

        return {
            'url': url,
            'slug': slug,
            'screenshot': str(screenshot_path),
            'html': str(html_path),
            'found_selectors': found_selectors,
            'has_json_ld': len(json_scripts) > 0 if json_scripts else False
        }

    except Exception as e:
        print(f"  ERROR inspecting {url}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("="*70)
    print("INSPECTION DE LA STRUCTURE HTML DE MCP.SO POUR TOOLS")
    print("="*70)
    print()
    print(f"Serveurs a inspecter: {len(TEST_SERVERS)}")
    print()

    # Create inspection directory
    inspection_dir = project_root / 'data' / 'inspection'
    inspection_dir.mkdir(parents=True, exist_ok=True)

    # Initialize scraper
    scraper = BaseScraper()
    results = []

    try:
        await scraper.start()

        # Inspect each server
        for i, url in enumerate(TEST_SERVERS):
            result = await inspect_server_page(scraper, url, i)
            if result:
                results.append(result)

            # Small delay between requests
            if i < len(TEST_SERVERS) - 1:
                await asyncio.sleep(1)

    finally:
        await scraper.close()

    # Summary
    print(f"\n{'='*70}")
    print("RESUME DE L'INSPECTION")
    print(f"{'='*70}\n")

    print(f"Pages inspectees: {len(results)}/{len(TEST_SERVERS)}")
    print(f"\nFichiers sauvegardes dans: {inspection_dir}")
    print(f"  - {len(results)} screenshots (.png)")
    print(f"  - {len(results)} fichiers HTML (.html)")

    # Count pages with potential tools sections
    pages_with_tools = sum(1 for r in results if r and r['found_selectors'])
    print(f"\nPages avec sections 'tools' detectees: {pages_with_tools}/{len(results)}")

    # Show most common selectors
    all_selectors = {}
    for result in results:
        if result and result['found_selectors']:
            for item in result['found_selectors']:
                selector = item['selector']
                all_selectors[selector] = all_selectors.get(selector, 0) + 1

    if all_selectors:
        print(f"\nSelecteurs les plus frequents:")
        sorted_selectors = sorted(all_selectors.items(), key=lambda x: x[1], reverse=True)
        for selector, count in sorted_selectors[:10]:
            print(f"  {selector:40} {count} pages")

    print(f"\n{'='*70}")
    print("PROCHAINES ETAPES:")
    print(f"{'='*70}\n")
    print("1. Ouvrir les fichiers HTML dans un editeur")
    print("2. Chercher la section 'Tools' manuellement")
    print("3. Identifier les selecteurs CSS qui fonctionnent")
    print("4. Noter les variations entre serveurs")
    print("5. Implementer l'extracteur dans tools_enricher.py")

    print(f"\nFichiers a analyser:")
    for result in results:
        if result:
            print(f"  - {result['html']}")

if __name__ == "__main__":
    asyncio.run(main())
