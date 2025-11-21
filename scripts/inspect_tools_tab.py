"""
Inspect tools tab specifically on mcp.so server pages
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

# Test servers that likely have tools
TEST_SERVERS = [
    "perplexity",
    "brave-search",
    "gitlab",
]

async def inspect_tools_tab(scraper, slug):
    """Inspect the tools tab for a server"""
    print(f"\n{'='*70}")
    print(f"Inspecting tools for: {slug}")
    print(f"{'='*70}")

    # Navigate to server page with tools tab
    url = f"https://mcp.so/server/{slug}?tab=tools"
    print(f"  URL: {url}")

    try:
        await scraper.navigate(url)
        await asyncio.sleep(3)  # Wait for dynamic content to load

        # Take screenshot
        screenshot_path = project_root / 'data' / 'inspection' / f"{slug}_tools.png"
        await scraper.page.screenshot(path=str(screenshot_path))
        print(f"  Screenshot: {screenshot_path.name}")

        # Try to find tools
        # Look for common patterns in tool lists
        selectors_to_try = [
            # Generic list patterns
            "ul li",
            "ol li",
            "[role='listitem']",

            # Tool-specific patterns
            "[data-tool]",
            ".tool-item",
            "[class*='tool']",

            # Card patterns
            ".card",
            "[class*='card']",

            # Table patterns
            "table tr",
            "tbody tr",
        ]

        print(f"\n  Analyzing page structure...")

        # Get all text content first
        body_text = await scraper.page.text_content("body")
        has_no_tools = "no tools" in body_text.lower() or "0 tools" in body_text.lower()

        if has_no_tools:
            print(f"  Page indicates NO TOOLS available")
            return None

        # Try each selector
        found_items = []
        for selector in selectors_to_try:
            try:
                elements = await scraper.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Get text from first few elements
                    sample_texts = []
                    for i, elem in enumerate(elements[:5]):
                        text = await elem.text_content()
                        if text and len(text.strip()) > 0:
                            sample_texts.append(text.strip()[:80])

                    if sample_texts:
                        found_items.append({
                            'selector': selector,
                            'count': len(elements),
                            'samples': sample_texts
                        })
            except:
                pass

        if found_items:
            print(f"\n  Found {len(found_items)} potential tool containers:")
            for item in found_items[:3]:  # Show top 3
                print(f"\n    Selector: {item['selector']}")
                print(f"    Count: {item['count']} elements")
                print(f"    Samples:")
                for i, sample in enumerate(item['samples'][:2], 1):
                    print(f"      [{i}] {sample}")

        # Check for specific tool attributes
        print(f"\n  Checking for tool names/descriptions...")

        # Common patterns for tool data
        tool_patterns = [
            ("h2", "Tool headings"),
            ("h3", "Tool headings"),
            ("[class*='name']", "Name fields"),
            ("[class*='description']", "Description fields"),
            ("code", "Code blocks (may contain schemas)"),
            ("pre", "Pre-formatted text"),
        ]

        tool_data_found = []
        for selector, description in tool_patterns:
            try:
                elements = await scraper.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Sample first element
                    text = await elements[0].text_content()
                    if text:
                        tool_data_found.append({
                            'type': description,
                            'selector': selector,
                            'count': len(elements),
                            'sample': text.strip()[:100]
                        })
            except:
                pass

        if tool_data_found:
            print(f"  Found {len(tool_data_found)} types of tool data:")
            for data in tool_data_found[:5]:
                print(f"    - {data['type']}: {data['count']} ({data['selector']})")
                print(f"      Sample: {data['sample']}")

        return {
            'slug': slug,
            'url': url,
            'screenshot': str(screenshot_path),
            'has_tools': not has_no_tools,
            'containers': found_items,
            'tool_data': tool_data_found
        }

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("="*70)
    print("INSPECTION DE L'ONGLET TOOLS SUR MCP.SO")
    print("="*70)

    scraper = BaseScraper()
    results = []

    try:
        await scraper.start()

        for slug in TEST_SERVERS:
            result = await inspect_tools_tab(scraper, slug)
            if result:
                results.append(result)
            await asyncio.sleep(1)

    finally:
        await scraper.close()

    # Summary
    print(f"\n{'='*70}")
    print("RESUME")
    print(f"{'='*70}\n")

    servers_with_tools = [r for r in results if r and r.get('has_tools')]
    print(f"Serveurs avec tools: {len(servers_with_tools)}/{len(results)}")

    if servers_with_tools:
        print(f"\nServeurs a analyser en detail:")
        for r in servers_with_tools:
            print(f"  - {r['slug']}: {r['screenshot']}")

    print(f"\nPROCHAINE ETAPE:")
    print(f"  Ouvrir les screenshots et identifier les selecteurs exacts")
    print(f"  pour extraire: name, description, input_schema")

if __name__ == "__main__":
    asyncio.run(main())
