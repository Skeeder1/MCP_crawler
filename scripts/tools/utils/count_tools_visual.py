"""Count tools visually from READMEs"""
import sqlite3
import re
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("MANUAL TOOL COUNT FROM READMEs")
print("=" * 70)
print()

# FIRECRAWL
cursor.execute("""SELECT content FROM markdown_content mc JOIN servers s ON s.id = mc.server_id WHERE s.slug = 'firecrawl-mcp-server' AND mc.content_type = 'readme'""")
content = cursor.fetchone()[0]
match = re.search(r'## Available Tools.*?(?=\n##[^#]|\Z)', content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(0)
    tools = re.findall(r'###\s*\d+\.\s*.*?\(`([a-zA-Z0-9_-]+)`\)', section)
    print(f'FIRECRAWL-MCP-SERVER: {len(tools)} tools')
    for i, t in enumerate(tools, 1):
        print(f'  {i}. {t}')
    print()

# PLAYWRIGHT
cursor.execute("""SELECT content FROM markdown_content mc JOIN servers s ON s.id = mc.server_id WHERE s.slug = 'playwright-mcp' AND mc.content_type = 'readme'""")
content = cursor.fetchone()[0]
match = re.search(r'## Tools.*?(?=\n##[^#]|\Z)', content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(0)
    tools = re.findall(r'-\s\*\*([a-zA-Z0-9_-]+)\*\*', section)
    print(f'PLAYWRIGHT-MCP: {len(tools)} tools')
    for i, t in enumerate(tools, 1):
        print(f'  {i:2d}. {t}')
    print()

# SERPER
cursor.execute("""SELECT content FROM markdown_content mc JOIN servers s ON s.id = mc.server_id WHERE s.slug = 'serper-mcp-server' AND mc.content_type = 'readme'""")
content = cursor.fetchone()[0]
match = re.search(r'## Available Tools.*?(?=\n##[^#]|\Z)', content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(0)
    tools = re.findall(r'-\s`([a-zA-Z0-9_-]+)`\s*-', section)
    print(f'SERPER-MCP-SERVER: {len(tools)} tools')
    for i, t in enumerate(tools, 1):
        print(f'  {i:2d}. {t}')
    print()

# MINIMAX
cursor.execute("""SELECT content FROM markdown_content mc JOIN servers s ON s.id = mc.server_id WHERE s.slug = 'minimax-mcp' AND mc.content_type = 'readme'""")
content = cursor.fetchone()[0]
match = re.search(r'## Available Tools.*?(?=\n##[^#]|\Z)', content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(0)
    tools = re.findall(r'\|\s*`([a-zA-Z0-9_-]+)`\s*\|', section)
    print(f'MINIMAX-MCP: {len(tools)} tools')
    for i, t in enumerate(tools, 1):
        print(f'  {i}. {t}')
    print()

# PERPLEXITY
cursor.execute("""SELECT content FROM markdown_content mc JOIN servers s ON s.id = mc.server_id WHERE s.slug = 'perplexity' AND mc.content_type = 'readme'""")
content = cursor.fetchone()[0]
match = re.search(r'## Available Tools.*?(?=\n##[^#]|\Z)', content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(0)
    tools = re.findall(r'###\s*\*\*([a-zA-Z0-9_-]+)\*\*', section)
    print(f'PERPLEXITY: {len(tools)} tools')
    for i, t in enumerate(tools, 1):
        print(f'  {i}. {t}')
    print()

# FLOMO
cursor.execute("""SELECT content FROM markdown_content mc JOIN servers s ON s.id = mc.server_id WHERE s.slug = 'mcp-server-flomo' AND mc.content_type = 'readme'""")
content = cursor.fetchone()[0]
match = re.search(r'## Tools.*?(?=\n##[^#]|\Z)', content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(0)
    tools = re.findall(r'-\s`([a-zA-Z0-9_-]+)`\s*-', section)
    print(f'MCP-SERVER-FLOMO: {len(tools)} tools')
    for i, t in enumerate(tools, 1):
        print(f'  {i}. {t}')
    print()

conn.close()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("All tools extracted manually from READMEs using simple regex.")
print("These counts should match the parser output exactly.")
