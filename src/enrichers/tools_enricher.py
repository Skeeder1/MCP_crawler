"""
Tools enricher - Extract tools from READMEs and populate tools table
"""
import sys
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.tools_parser import ToolsParser


class ToolsEnricher:
    """
    Extract tools from server READMEs and populate the tools table
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.parser = ToolsParser()
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_servers_with_readmes(self, limit: Optional[int] = None) -> List[Dict]:
        """Get servers that have README content"""

        query = """
            SELECT
                s.id as server_id,
                s.slug,
                s.name,
                mc.content
            FROM servers s
            INNER JOIN markdown_content mc ON mc.server_id = s.id
            WHERE mc.content_type = 'readme'
            AND mc.content IS NOT NULL
            AND LENGTH(mc.content) > 100
            ORDER BY s.slug
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)

        servers = []
        for row in self.cursor.fetchall():
            servers.append({
                'server_id': row[0],
                'slug': row[1],
                'name': row[2],
                'content': row[3]
            })

        return servers

    def extract_tools_for_server(self, server: Dict) -> List[Dict]:
        """Extract tools from server README"""
        tools = self.parser.parse_tools(server['content'])

        # Add server_id to each tool
        for tool in tools:
            tool['server_id'] = server['server_id']

        return tools

    def save_tool(self, tool: Dict):
        """
        Save tool to database
        Updates if tool already exists (by server_id + name)
        """

        # Check if tool exists
        self.cursor.execute("""
            SELECT id FROM tools
            WHERE server_id = ? AND name = ?
        """, (tool['server_id'], tool['name']))

        existing = self.cursor.fetchone()

        now = datetime.utcnow().isoformat()

        if existing:
            # Update existing tool
            tool_id = existing[0]
            self.cursor.execute("""
                UPDATE tools
                SET
                    display_name = ?,
                    description = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                tool.get('display_name', ''),
                tool.get('description', ''),
                now,
                tool_id
            ))
        else:
            # Insert new tool
            tool_id = str(uuid.uuid4())
            # Provide defaults for NOT NULL columns
            input_schema = tool.get('input_schema', '{}')
            if isinstance(input_schema, dict):
                import json
                input_schema = json.dumps(input_schema)

            self.cursor.execute("""
                INSERT INTO tools (
                    id,
                    server_id,
                    name,
                    display_name,
                    description,
                    input_schema,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool_id,
                tool['server_id'],
                tool['name'],
                tool.get('display_name', ''),
                tool.get('description', ''),
                input_schema,
                now,
                now
            ))

        return tool_id

    def enrich(self, limit: Optional[int] = None, commit: bool = True) -> Dict:
        """
        Main enrichment process

        Args:
            limit: Maximum number of servers to process
            commit: Whether to commit changes to DB (False for dry-run)

        Returns:
            Statistics dictionary
        """

        self.connect()

        stats = {
            'servers_processed': 0,
            'servers_with_tools': 0,
            'tools_extracted': 0,
            'tools_inserted': 0,
            'tools_updated': 0,
            'errors': 0,
            'server_details': []
        }

        try:
            # Get servers with READMEs
            servers = self.get_servers_with_readmes(limit=limit)
            stats['servers_total'] = len(servers)

            print(f"Processing {len(servers)} servers...")
            print()

            for server in servers:
                stats['servers_processed'] += 1

                try:
                    # Extract tools
                    tools = self.extract_tools_for_server(server)
                    stats['tools_extracted'] += len(tools)

                    if tools:
                        stats['servers_with_tools'] += 1

                    # Save tools
                    inserted = 0
                    updated = 0

                    for tool in tools:
                        # Check if exists before saving
                        self.cursor.execute("""
                            SELECT id FROM tools
                            WHERE server_id = ? AND name = ?
                        """, (tool['server_id'], tool['name']))

                        if self.cursor.fetchone():
                            updated += 1
                        else:
                            inserted += 1

                        self.save_tool(tool)

                    stats['tools_inserted'] += inserted
                    stats['tools_updated'] += updated

                    # Log details
                    status = "✅" if tools else "⚠️ "
                    print(f"{status} {server['slug']:30s} | {len(tools):2d} tools | +{inserted} -{updated}")

                    stats['server_details'].append({
                        'slug': server['slug'],
                        'tools_count': len(tools),
                        'inserted': inserted,
                        'updated': updated
                    })

                except Exception as e:
                    stats['errors'] += 1
                    print(f"❌ {server['slug']:30s} | ERROR: {str(e)}")

            # Commit or rollback
            if commit:
                self.conn.commit()
                print("\n✅ Changes committed to database")
            else:
                self.conn.rollback()
                print("\n⚠️  Dry-run mode: changes rolled back")

        finally:
            self.close()

        return stats

    def print_summary(self, stats: Dict):
        """Print enrichment summary"""

        print()
        print("=" * 70)
        print("ENRICHMENT SUMMARY")
        print("=" * 70)

        total = stats['servers_total']
        processed = stats['servers_processed']
        with_tools = stats['servers_with_tools']
        success_rate = (with_tools / processed * 100) if processed > 0 else 0

        print(f"Servers processed: {processed}/{total}")
        print(f"Servers with tools found: {with_tools}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total tools extracted: {stats['tools_extracted']}")
        print(f"  • New tools inserted: {stats['tools_inserted']}")
        print(f"  • Existing tools updated: {stats['tools_updated']}")
        print(f"Errors: {stats['errors']}")
        print()

        if success_rate >= 80:
            print("✅ SUCCESS: Enrichment achieves ≥80% success rate!")
        else:
            print(f"⚠️  WARNING: Success rate is {success_rate:.1f}% (target: 80%)")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Enrich tools from READMEs')
    parser.add_argument('--limit', type=int, help='Limit number of servers to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run mode (no commit)')
    parser.add_argument('--db', default='data/mcp_servers.db', help='Database path')

    args = parser.parse_args()

    db_path = Path(__file__).parent.parent.parent / args.db

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    print("=" * 70)
    print("TOOLS ENRICHER")
    print("=" * 70)
    print(f"Database: {db_path}")
    print(f"Limit: {args.limit or 'None (all servers)'}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'COMMIT'}")
    print("=" * 70)
    print()

    enricher = ToolsEnricher(str(db_path))
    stats = enricher.enrich(limit=args.limit, commit=not args.dry_run)
    enricher.print_summary(stats)


if __name__ == '__main__':
    main()
