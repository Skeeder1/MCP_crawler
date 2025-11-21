"""
Manual validation: Verify 100% accuracy on successful servers
Compare parser output with manually verified tool lists
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.tools_parser import ToolsParser


# MANUALLY VERIFIED TOOLS FOR EACH SERVER
# (obtained by reading the README and listing all documented tools)
EXPECTED_TOOLS = {
    'firecrawl-mcp-server': [
        'firecrawl_scrape',
        'firecrawl_batch_scrape',
        'firecrawl_check_batch_status',
        'firecrawl_map',
        'firecrawl_search',
        'firecrawl_crawl',
        'firecrawl_check_crawl_status',
        'firecrawl_extract'
    ],
    'mcp-server-flomo': [
        'write_note'
    ],
    'minimax-mcp': [
        'text_to_audio',
        'list_voices',
        'voice_clone',
        'generate_video',
        'text_to_image',
        'query_video_generation',
        'music_generation',
        'voice_design'
    ],
    'playwright-mcp': [
        'browser_click',
        'browser_close',
        'browser_console_messages',
        'browser_drag',
        'browser_evaluate',
        'browser_file_upload',
        'browser_fill_form',
        'browser_handle_dialog',
        'browser_hover',
        'browser_navigate',
        'browser_navigate_back',
        'browser_network_requests',
        'browser_press_key',
        'browser_resize',
        'browser_run_code',
        'browser_select_option',
        'browser_snapshot',
        'browser_take_screenshot',
        'browser_type',
        'browser_wait_for',
        'browser_tabs',
        'browser_install',
        'browser_mouse_click_xy',
        'browser_mouse_drag_xy',
        'browser_mouse_move_xy',
        'browser_pdf_save',
        'browser_generate_locator',
        'browser_verify_element_visible',
        'browser_verify_list_visible',
        'browser_verify_text_visible',
        'browser_verify_value',
        'browser_start_tracing',
        'browser_stop_tracing'
    ],
    'serper-mcp-server': [
        'google_search',
        'google_search_images',
        'google_search_videos',
        'google_search_places',
        'google_search_maps',
        'google_search_reviews',
        'google_search_news',
        'google_search_shopping',
        'google_search_lens',
        'google_search_scholar',
        'google_search_patents',
        'google_search_autocomplete',
        'webpage_scrape'
    ],
    'perplexity': [
        'perplexity_search',
        'perplexity_ask',
        'perplexity_research',
        'perplexity_reason'
    ]
}


def validate_parser():
    """Validate parser against manually verified tool lists"""

    db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    parser = ToolsParser()
    results = []

    print("=" * 80)
    print("100% ACCURACY VALIDATION")
    print("=" * 80)
    print("Comparing parser output with manually verified tool lists")
    print()

    for slug, expected in EXPECTED_TOOLS.items():
        print(f"📄 Server: {slug}")
        print("-" * 80)

        # Get README content
        cursor.execute("""
            SELECT mc.content
            FROM servers s
            INNER JOIN markdown_content mc ON mc.server_id = s.id
            WHERE s.slug = ?
            AND mc.content_type = 'readme'
        """, (slug,))

        row = cursor.fetchone()
        if not row:
            print(f"❌ ERROR: No README found for {slug}")
            results.append({'slug': slug, 'success': False, 'error': 'No README'})
            print()
            continue

        content = row[0]

        # Parse tools
        parsed = parser.parse_tools(content)
        parsed_names = [t['name'] for t in parsed]

        # Compare
        expected_set = set(expected)
        parsed_set = set(parsed_names)

        missing = expected_set - parsed_set  # Tools we should have found but didn't
        extra = parsed_set - expected_set     # Tools we found but shouldn't have

        perfect_match = (missing == set() and extra == set())

        # Display results
        print(f"Expected: {len(expected)} tools")
        print(f"Parsed:   {len(parsed_names)} tools")
        print()

        if perfect_match:
            print("✅ PERFECT MATCH - 100% accuracy")
            print("\nAll tools:")
            for i, name in enumerate(expected, 1):
                print(f"  {i:2d}. {name}")
        else:
            print("❌ MISMATCH DETECTED")

            if missing:
                print(f"\n⚠️  MISSING ({len(missing)} tools) - Parser failed to extract:")
                for name in sorted(missing):
                    print(f"  ✗ {name}")

            if extra:
                print(f"\n⚠️  EXTRA ({len(extra)} tools) - Parser extracted incorrectly:")
                for name in sorted(extra):
                    print(f"  + {name}")

            if not missing and not extra:
                print("\nExpected tools:")
                for name in expected:
                    print(f"  ✓ {name}")

        results.append({
            'slug': slug,
            'success': perfect_match,
            'expected': len(expected),
            'parsed': len(parsed_names),
            'missing': len(missing),
            'extra': len(extra)
        })

        print()

    conn.close()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    total = len(results)
    perfect = sum(1 for r in results if r['success'])
    accuracy = (perfect / total * 100) if total > 0 else 0

    print(f"Servers tested: {total}")
    print(f"Perfect matches: {perfect}")
    print(f"Accuracy: {accuracy:.1f}%")
    print()

    print("Details:")
    for r in results:
        if r['success']:
            status = "✅"
            details = f"Expected: {r['expected']:2d} | Parsed: {r['parsed']:2d}"
        else:
            status = "❌"
            if 'error' in r:
                details = r['error']
            else:
                details = f"Expected: {r['expected']:2d} | Parsed: {r['parsed']:2d} | Missing: {r['missing']} | Extra: {r['extra']}"

        print(f"  {status} {r['slug']:30s} | {details}")

    print()

    if accuracy == 100:
        print("✅ SUCCESS: Parser achieves 100% accuracy on all tested servers!")
        print("   → Ready to scale to larger dataset")
        return True
    else:
        print(f"❌ FAILURE: Parser accuracy is {accuracy:.1f}% (required: 100%)")
        print("   → Must fix parser before proceeding")
        return False


if __name__ == '__main__':
    success = validate_parser()
    sys.exit(0 if success else 1)
