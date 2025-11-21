#!/usr/bin/env python3
"""
Validate backfill results and generate statistics
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "mcp_servers.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("BACKFILL RESULTS VALIDATION")
print("=" * 70)
print()

# Total servers
cursor.execute("SELECT COUNT(*) FROM servers")
total_servers = cursor.fetchone()[0]
print(f"Total servers: {total_servers}")

# Servers with README
cursor.execute("""
    SELECT COUNT(DISTINCT server_id)
    FROM markdown_content
    WHERE content_type = 'readme' AND content IS NOT NULL
""")
servers_with_readme = cursor.fetchone()[0]
print(f"Servers with README: {servers_with_readme}")

# Servers with NPM config
cursor.execute("SELECT COUNT(*) FROM mcp_config_npm")
servers_with_npm = cursor.fetchone()[0]
print(f"Servers with NPM config: {servers_with_npm}")

# Servers with Docker config
cursor.execute("SELECT COUNT(*) FROM mcp_config_docker")
servers_with_docker = cursor.fetchone()[0]
print(f"Servers with Docker config: {servers_with_docker}")

# Total servers with ANY config
cursor.execute("""
    SELECT COUNT(DISTINCT id) FROM servers
    WHERE id IN (SELECT server_id FROM mcp_config_npm)
       OR id IN (SELECT server_id FROM mcp_config_docker)
""")
servers_with_config = cursor.fetchone()[0]
print(f"\n[OK] Total servers with config: {servers_with_config}")

# Calculate success rates
if servers_with_readme > 0:
    success_rate = (servers_with_config / servers_with_readme) * 100
    print(f"Success rate (with README): {success_rate:.2f}%")

overall_rate = (servers_with_config / total_servers) * 100
print(f"Overall coverage: {overall_rate:.2f}%")

print("\n" + "=" * 70)
print("COMMAND BREAKDOWN")
print("=" * 70)
print()

# Breakdown by command
cursor.execute("""
    SELECT command, COUNT(*) as count
    FROM mcp_config_npm
    GROUP BY command
    ORDER BY count DESC
""")

for command, count in cursor.fetchall():
    print(f"  {command}: {count} servers")

print("\n" + "=" * 70)
print("RUNTIME BREAKDOWN")
print("=" * 70)
print()

# Breakdown by runtime
cursor.execute("""
    SELECT runtime, COUNT(*) as count
    FROM mcp_config_npm
    GROUP BY runtime
    ORDER BY count DESC
""")

for runtime, count in cursor.fetchall():
    print(f"  {runtime}: {count} servers")

print("\n" + "=" * 70)
print("NEW PATTERNS DETECTED")
print("=" * 70)
print()

# Check for new command patterns (stored in args)
cursor.execute("""
    SELECT args, COUNT(*) as count
    FROM mcp_config_npm
    WHERE args LIKE '%uvx%'
       OR args LIKE '%pip%'
       OR args LIKE '%python%'
       OR args LIKE '%git%'
       OR args LIKE '%docker%'
    GROUP BY substr(args, 1, 30)
    LIMIT 10
""")

results = cursor.fetchall()
if results:
    print("Sample of new patterns extracted:")
    for args, count in results:
        # Truncate long args
        args_display = args[:60] + "..." if len(args) > 60 else args
        print(f"  {args_display} ({count}x)")
else:
    print("  No new patterns detected in args")

print("\n" + "=" * 70)
print("BEFORE vs AFTER COMPARISON")
print("=" * 70)
print()

# These numbers are from the analysis report
print("BEFORE improvements:")
print(f"  Servers with config: 77")
print(f"  Success rate: 38.89%")
print()
print("AFTER Phase 1 & 2 improvements:")
print(f"  Servers with config: {servers_with_config}")
print(f"  Success rate: {success_rate:.2f}%")
print()
improvement = servers_with_config - 77
improvement_pct = ((servers_with_config - 77) / 77) * 100 if 77 > 0 else 0
print(f"Improvement: +{improvement} servers (+{improvement_pct:.1f}%)")

print("\n" + "=" * 70)

conn.close()
