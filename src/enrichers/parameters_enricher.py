"""
Parameters enricher - Extract parameters from tool documentation and populate tool_parameters table
"""
import sys
import sqlite3
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.parameters_parser import ParametersParser


class ParametersEnricher:
    """
    Extract parameters from tool documentation and populate the tool_parameters table
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.parser = ParametersParser()
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

    def get_tools_with_readmes(self, limit: Optional[int] = None) -> List[Dict]:
        """Get tools with their server's README content"""

        query = """
            SELECT
                t.id as tool_id,
                t.server_id,
                t.name as tool_name,
                t.display_name,
                s.slug as server_slug,
                s.name as server_name,
                mc.content as readme_content
            FROM tools t
            INNER JOIN servers s ON s.id = t.server_id
            INNER JOIN markdown_content mc ON mc.server_id = s.id
            WHERE mc.content_type = 'readme'
            AND mc.content IS NOT NULL
            AND LENGTH(mc.content) > 100
            ORDER BY s.slug, t.name
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)

        tools = []
        for row in self.cursor.fetchall():
            tools.append({
                'tool_id': row[0],
                'server_id': row[1],
                'tool_name': row[2],
                'display_name': row[3],
                'server_slug': row[4],
                'server_name': row[5],
                'readme_content': row[6]
            })

        return tools

    def extract_tool_section(self, readme: str, tool_name: str) -> Optional[str]:
        """
        Extract the section for a specific tool from README
        Returns ~2000 chars of context around the tool
        """

        # Try multiple patterns to find the tool
        # IMPORTANT: Order matters! Try more specific patterns first
        patterns = [
            rf'###\s+{re.escape(tool_name)}\s*\n',  # Exact heading match (most specific)
            rf'###\s+[^#\n]*{re.escape(tool_name)}[^#\n]*\n',  # Heading with tool name somewhere
            rf'\*\*{re.escape(tool_name)}\*\*',  # Bold format
            rf'`{re.escape(tool_name)}`',  # Backtick format (least specific, matches references)
        ]

        for pattern in patterns:
            match = re.search(pattern, readme, re.IGNORECASE)
            if match:
                start = match.start()
                # Get context: 200 chars before, 2000 chars after
                context_start = max(0, start - 200)
                context_end = min(len(readme), start + 2000)
                return readme[context_start:context_end]

        return None

    def extract_parameters_for_tool(self, tool: Dict) -> List[Dict]:
        """Extract parameters for a specific tool"""

        # Extract the tool's section from README
        tool_section = self.extract_tool_section(
            tool['readme_content'],
            tool['tool_name']
        )

        if not tool_section:
            return []

        # Parse parameters from the section
        params = self.parser.parse_parameters(tool_section)

        # Add tool_id to each parameter
        for param in params:
            param['tool_id'] = tool['tool_id']

        return params

    def save_parameter(self, param: Dict) -> str:
        """
        Save parameter to database
        Updates if parameter already exists (by tool_id + name)
        Returns parameter ID
        """

        # Check if parameter exists
        self.cursor.execute("""
            SELECT id FROM tool_parameters
            WHERE tool_id = ? AND name = ?
        """, (param['tool_id'], param['name']))

        existing = self.cursor.fetchone()

        now = datetime.utcnow().isoformat()

        if existing:
            # Update existing parameter
            param_id = existing[0]
            self.cursor.execute("""
                UPDATE tool_parameters
                SET
                    type = ?,
                    description = ?,
                    required = ?,
                    default_value = ?,
                    example_value = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                param.get('type'),
                param.get('description'),
                1 if param.get('required') is True else (0 if param.get('required') is False else None),
                param.get('default_value'),
                param.get('example_value'),
                now,
                param_id
            ))
        else:
            # Insert new parameter
            param_id = str(uuid.uuid4())
            self.cursor.execute("""
                INSERT INTO tool_parameters (
                    id,
                    tool_id,
                    name,
                    type,
                    description,
                    required,
                    default_value,
                    example_value,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                param_id,
                param['tool_id'],
                param['name'],
                param.get('type'),
                param.get('description'),
                1 if param.get('required') is True else (0 if param.get('required') is False else 0),
                param.get('default_value'),
                param.get('example_value'),
                now,
                now
            ))

        return param_id

    def enrich(self, limit: Optional[int] = None, commit: bool = True) -> Dict:
        """
        Main enrichment process

        Args:
            limit: Maximum number of tools to process
            commit: Whether to commit changes to DB (False for dry-run)

        Returns:
            Statistics dictionary
        """

        self.connect()

        stats = {
            'tools_processed': 0,
            'tools_with_params': 0,
            'params_extracted': 0,
            'params_inserted': 0,
            'params_updated': 0,
            'errors': 0,
            'tool_details': []
        }

        try:
            # Get tools with READMEs
            tools = self.get_tools_with_readmes(limit=limit)
            stats['tools_total'] = len(tools)

            print(f"Processing {len(tools)} tools...")
            print()

            for tool in tools:
                stats['tools_processed'] += 1

                try:
                    # Extract parameters
                    params = self.extract_parameters_for_tool(tool)
                    stats['params_extracted'] += len(params)

                    if params:
                        stats['tools_with_params'] += 1

                    # Save parameters
                    inserted = 0
                    updated = 0

                    for param in params:
                        # Check if exists before saving
                        self.cursor.execute("""
                            SELECT id FROM tool_parameters
                            WHERE tool_id = ? AND name = ?
                        """, (param['tool_id'], param['name']))

                        if self.cursor.fetchone():
                            updated += 1
                        else:
                            inserted += 1

                        self.save_parameter(param)

                    stats['params_inserted'] += inserted
                    stats['params_updated'] += updated

                    # Log details
                    status = "✅" if params else "⚠️ "
                    tool_display = f"{tool['server_slug']}::{tool['tool_name']}"
                    print(f"{status} {tool_display:45s} | {len(params):2d} params | +{inserted} ~{updated}")

                    stats['tool_details'].append({
                        'server_slug': tool['server_slug'],
                        'tool_name': tool['tool_name'],
                        'params_count': len(params),
                        'inserted': inserted,
                        'updated': updated
                    })

                except Exception as e:
                    stats['errors'] += 1
                    tool_display = f"{tool['server_slug']}::{tool['tool_name']}"
                    print(f"❌ {tool_display:45s} | ERROR: {str(e)}")

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
        print("PARAMETERS ENRICHMENT SUMMARY")
        print("=" * 70)

        total = stats['tools_total']
        processed = stats['tools_processed']
        with_params = stats['tools_with_params']
        success_rate = (with_params / processed * 100) if processed > 0 else 0

        print(f"Tools processed: {processed}/{total}")
        print(f"Tools with parameters found: {with_params}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total parameters extracted: {stats['params_extracted']}")
        print(f"  • New parameters inserted: {stats['params_inserted']}")
        print(f"  • Existing parameters updated: {stats['params_updated']}")
        print(f"Errors: {stats['errors']}")
        print()

        # Show top tools by parameter count
        if stats['tool_details']:
            sorted_tools = sorted(
                stats['tool_details'],
                key=lambda x: x['params_count'],
                reverse=True
            )[:10]

            if any(t['params_count'] > 0 for t in sorted_tools):
                print("Top tools by parameter count:")
                for tool in sorted_tools:
                    if tool['params_count'] > 0:
                        print(f"  • {tool['server_slug']:30s} :: {tool['tool_name']:25s} ({tool['params_count']} params)")
                print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Enrich parameters from tool documentation')
    parser.add_argument('--limit', type=int, help='Limit number of tools to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run mode (no commit)')
    parser.add_argument('--db', default='data/mcp_servers.db', help='Database path')

    args = parser.parse_args()

    db_path = Path(__file__).parent.parent.parent / args.db

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    print("=" * 70)
    print("PARAMETERS ENRICHER")
    print("=" * 70)
    print(f"Database: {db_path}")
    print(f"Limit: {args.limit or 'None (all tools)'}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'COMMIT'}")
    print("=" * 70)
    print()

    enricher = ParametersEnricher(str(db_path))
    stats = enricher.enrich(limit=args.limit, commit=not args.dry_run)
    enricher.print_summary(stats)


if __name__ == '__main__':
    main()
