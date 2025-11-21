"""
Extract sample READMEs from Supabase to understand tools documentation format
"""
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

from supabase import create_client
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Servers known to have tools
servers_with_tools = ['gitlab', 'brave-search', 'perplexity', 'puppeteer', 'postgres']

print("="*70)
print("EXTRACTION DES READMEs POUR ANALYSE")
print("="*70)
print()

inspection_dir = project_root / 'data' / 'inspection'
inspection_dir.mkdir(parents=True, exist_ok=True)

for slug in servers_with_tools:
    print(f"Extracting README for: {slug}")

    # Get server
    result = supabase.table('servers').select('id, slug').eq('slug', slug).limit(1).execute()

    if not result.data:
        print(f"  Server not found: {slug}")
        continue

    server = result.data[0]

    # Get markdown content
    md_result = supabase.table('markdown_content').select('content').eq('server_id', server['id']).limit(1).execute()

    if md_result.data and md_result.data[0].get('content'):
        content = md_result.data[0]['content']

        # Save to file
        path = inspection_dir / f'{slug}_README.md'
        path.write_text(content, encoding='utf-8')

        # Count "tool" mentions
        tool_mentions = content.lower().count('tool')

        print(f"  ✅ Saved: {path.name} ({len(content):,} chars, {tool_mentions} 'tool' mentions)")
    else:
        print(f"  ❌ No README content")

    print()

print("="*70)
print("NEXT: Manually inspect these files to identify tools documentation patterns")
print("="*70)
