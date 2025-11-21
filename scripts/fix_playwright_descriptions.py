"""
Phase 4: Fix playwright tool descriptions
Remove "- Title: " prefix and improve descriptions
"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Improved descriptions based on tool names
IMPROVED_DESCRIPTIONS = {
    'browser_click': 'Click on an element in the browser page',
    'browser_close': 'Close the browser instance',
    'browser_console_messages': 'Retrieve console messages from the browser',
    'browser_drag': 'Perform a drag operation with the mouse',
    'browser_evaluate': 'Execute JavaScript code in the browser context',
    'browser_file_upload': 'Upload files to a file input element',
    'browser_fill_form': 'Fill out a form with specified values',
    'browser_generate_locator': 'Generate a locator selector for a specific element',
    'browser_handle_dialog': 'Handle browser dialogs (alert, confirm, prompt)',
    'browser_hover': 'Hover the mouse over an element',
    'browser_install': 'Install the browser specified in the configuration',
    'browser_mouse_click_xy': 'Click at specific X/Y coordinates on the page',
    'browser_mouse_drag_xy': 'Drag mouse from one coordinate to another',
    'browser_mouse_move_xy': 'Move mouse to specific X/Y coordinates',
    'browser_navigate': 'Navigate the browser to a specific URL',
    'browser_navigate_back': 'Navigate back to the previous page',
    'browser_network_requests': 'Retrieve the list of network requests made by the page',
    'browser_pdf_save': 'Save the current page as a PDF file',
    'browser_press_key': 'Press a keyboard key or key combination',
    'browser_resize': 'Resize the browser window to specific dimensions',
    'browser_run_code': 'Execute Playwright automation code directly',
    'browser_select_option': 'Select an option from a dropdown or select element',
    'browser_snapshot': 'Capture a structured snapshot of the page accessibility tree',
    'browser_start_tracing': 'Start recording browser trace for performance analysis',
    'browser_stop_tracing': 'Stop recording browser trace and save the trace file',
    'browser_tabs': 'Manage browser tabs (switch, close, list)',
    'browser_take_screenshot': 'Capture a screenshot of the current page',
    'browser_type': 'Type text into an input field or element',
    'browser_verify_element_visible': 'Verify that a specific element is visible on the page',
    'browser_verify_list_visible': 'Verify that elements in a list are visible',
    'browser_verify_text_visible': 'Verify that specific text is visible on the page',
    'browser_verify_value': 'Verify the value of an input or element',
    'browser_wait_for': 'Wait for a specific condition or timeout',
}

def fix_playwright_descriptions():
    db_path = Path(__file__).parent.parent / 'data' / 'mcp_servers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*75)
    print("PHASE 4: FIX PLAYWRIGHT DESCRIPTIONS")
    print("="*75)

    # Get playwright server
    cursor.execute("""
        SELECT id, name
        FROM servers
        WHERE name LIKE '%Playwright%'
    """)

    server = cursor.fetchone()
    if not server:
        print("\n❌ Playwright server not found")
        conn.close()
        return

    server_id, server_name = server
    print(f"\n✅ Found server: {server_name}")

    # Get all playwright tools with "- Title:" descriptions
    cursor.execute("""
        SELECT id, name, description
        FROM tools
        WHERE server_id = ? AND description LIKE '- Title:%'
        ORDER BY name
    """, (server_id,))

    tools = cursor.fetchall()
    print(f"\n📊 Found {len(tools)} tools with artifact descriptions")

    fixed_count = 0

    for tool_id, tool_name, old_description in tools:
        if tool_name in IMPROVED_DESCRIPTIONS:
            new_description = IMPROVED_DESCRIPTIONS[tool_name]

            # Update the description
            cursor.execute("""
                UPDATE tools
                SET description = ?, updated_at = ?
                WHERE id = ?
            """, (new_description, datetime.now(timezone.utc).isoformat(), tool_id))

            print(f"   ✅ {tool_name}")
            print(f"      Old: {old_description}")
            print(f"      New: {new_description}")
            fixed_count += 1
        else:
            print(f"   ⚠️  {tool_name}: No improved description defined")

    conn.commit()

    # Verify
    print("\n" + "="*75)
    print("VERIFICATION")
    print("="*75)

    cursor.execute("""
        SELECT COUNT(*)
        FROM tools
        WHERE server_id = ? AND description LIKE '- Title:%'
    """, (server_id,))
    remaining = cursor.fetchone()[0]

    print(f"   Fixed: {fixed_count}")
    print(f"   Remaining with artifacts: {remaining}")

    conn.close()

    print("\n" + "="*75)
    if remaining == 0:
        print("✅ PHASE 4 COMPLETE - All playwright descriptions fixed!")
    else:
        print(f"⚠️  PHASE 4 PARTIAL - {remaining} descriptions still have artifacts")
    print("="*75)

if __name__ == "__main__":
    fix_playwright_descriptions()
