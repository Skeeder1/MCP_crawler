"""
Phase 5: Fix incorrect required/optional flags
"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Parameters that should be required (tool.param -> should be required)
SHOULD_BE_REQUIRED = [
    'firecrawl_scrape.url',  # Can't scrape without URL
    'firecrawl_crawl.url',  # Can't crawl without start URL
    'firecrawl_batch_scrape.urls',  # Can't batch scrape without URLs
    'firecrawl_check_batch_status.id',  # Can't check status without ID
    'firecrawl_extract.urls',  # Can't extract without URLs
]

def fix_required_flags():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 5: FIX REQUIRED/OPTIONAL FLAGS")
    print("="*75)

    fixed_count = 0
    skipped_count = 0

    for tool_param in SHOULD_BE_REQUIRED:
        tool_name, param_name = tool_param.split('.')

        # Find the parameter
        cursor.execute("""
            SELECT tp.id, tp.required, s.name
            FROM tool_parameters tp
            JOIN tools t ON tp.tool_id = t.id
            JOIN servers s ON t.server_id = s.id
            WHERE t.name = ? AND tp.name = ?
        """, (tool_name, param_name))

        result = cursor.fetchone()

        if result:
            param_id, current_required, server_name = result

            if current_required == 0:  # Currently optional
                # Update to required
                cursor.execute("""
                    UPDATE tool_parameters
                    SET required = 1, updated_at = ?
                    WHERE id = ?
                """, (datetime.now(timezone.utc).isoformat(), param_id))

                print(f"   ✅ {tool_param}: OPTIONAL → REQUIRED")
                fixed_count += 1
            else:
                print(f"   ℹ️  {tool_param}: Already REQUIRED")
                skipped_count += 1
        else:
            print(f"   ⚠️  {tool_param}: Not found in database")

    conn.commit()

    # Verify
    print("\n" + "="*75)
    print("VERIFICATION")
    print("="*75)

    # Check all URL parameters in firecrawl
    cursor.execute("""
        SELECT
            t.name as tool_name,
            tp.name as param_name,
            tp.required
        FROM tool_parameters tp
        JOIN tools t ON tp.tool_id = t.id
        JOIN servers s ON t.server_id = s.id
        WHERE s.name LIKE '%Firecrawl%' AND (tp.name = 'url' OR tp.name = 'urls' OR tp.name = 'id')
        ORDER BY t.name, tp.name
    """)

    print("\nFirecrawl critical parameters status:")
    all_correct = True
    for tool_name, param_name, required in cursor.fetchall():
        req_str = "REQUIRED" if required else "OPTIONAL"
        # Check if this should be required
        key = f"{tool_name}.{param_name}"
        expected_required = key in SHOULD_BE_REQUIRED or param_name == 'id' and 'status' in tool_name

        if required == 1:
            print(f"   ✅ {key}: {req_str}")
        else:
            if expected_required:
                print(f"   ⚠️  {key}: {req_str} (might need to be REQUIRED)")
                all_correct = False
            else:
                print(f"   ℹ️  {key}: {req_str} (correctly OPTIONAL)")

    conn.close()

    print("\n" + "="*75)
    print(f"SUMMARY")
    print("="*75)
    print(f"   Fixed: {fixed_count}")
    print(f"   Already correct: {skipped_count}")

    if all_correct:
        print("\n✅ PHASE 5 COMPLETE - All critical required flags fixed!")
    else:
        print("\n⚠️  PHASE 5 PARTIAL - Some flags may still need review")
    print("="*75)

if __name__ == "__main__":
    fix_required_flags()
