"""
Phase 1.4: Verify all Phase 1 corrections
"""
import sys
import sqlite3
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("PHASE 1.4: VERIFICATION DES CORRECTIONS")
print("=" * 80)
print()

# Expected state after Phase 1
expected_state = {
    'firecrawl_map': {
        'params': [('url', 'string', True)]
    },
    'firecrawl_check_crawl_status': {
        'params': [('id', 'string', True)]
    },
    'firecrawl_search': {
        'params': [
            ('query', 'string', True),
            ('limit', 'integer', False),
            ('lang', 'string', False),
            ('country', 'string', False),
            ('scrapeOptions', 'object', False)
        ]
    }
}

all_ok = True

for tool_name, expected in expected_state.items():
    print(f"Checking {tool_name}...")
    print("-" * 80)

    # Get tool and its parameters
    cursor.execute("""
        SELECT tp.name, tp.type, tp.required
        FROM tool_parameters tp
        INNER JOIN tools t ON t.id = tp.tool_id
        INNER JOIN servers s ON s.id = t.server_id
        WHERE s.slug = 'firecrawl-mcp-server' AND t.name = ?
        ORDER BY tp.required DESC, tp.name
    """, (tool_name,))

    actual_params = cursor.fetchall()
    expected_params = expected['params']

    # Check count
    if len(actual_params) != len(expected_params):
        print(f"  ❌ FAIL: Expected {len(expected_params)} params, got {len(actual_params)}")
        all_ok = False
    else:
        print(f"  ✅ Count OK: {len(actual_params)} parameters")

    # Check each parameter
    expected_set = set(expected_params)
    actual_set = set(actual_params)

    if expected_set == actual_set:
        print(f"  ✅ Parameters match perfectly!")
        for param in actual_params:
            name, type_, required = param
            req_str = "REQUIRED" if required else "OPTIONAL"
            print(f"     • {name:20s} ({type_:10s}) {req_str}")
    else:
        print(f"  ❌ FAIL: Parameters don't match")

        missing = expected_set - actual_set
        if missing:
            print(f"     Missing:")
            for param in missing:
                print(f"       - {param}")

        extra = actual_set - expected_set
        if extra:
            print(f"     Extra:")
            for param in extra:
                print(f"       + {param}")

        all_ok = False

    print()

print("=" * 80)
if all_ok:
    print("✅ PHASE 1 VALIDATION: SUCCESS!")
    print()
    print("All 3 critical fixes verified:")
    print("  ✅ firecrawl_map: url (REQUIRED)")
    print("  ✅ firecrawl_check_crawl_status: id (REQUIRED)")
    print("  ✅ firecrawl_search: query, limit, lang, country, scrapeOptions")
    print()
    print("Impact:")
    print("  • 2 broken tools fixed (map, check_crawl_status)")
    print("  • 1 incomplete tool fixed (search)")
    print("  • +5 parameters added")
    print("  • -8 incorrect parameters removed")
else:
    print("❌ PHASE 1 VALIDATION: FAILED")
    print("Some corrections were not applied correctly")

print("=" * 80)

conn.close()
