#!/usr/bin/env python3
"""
Backfill MCP Configuration Tables from Existing READMEs

This script parses existing README content stored in the markdown_content table
and extracts NPM/Docker installation configurations using the ReadmeParser.

Usage:
    python scripts/backfill_configs_from_readme.py [--dry-run] [--limit N]

Options:
    --dry-run    : Don't save to database, just show what would be extracted
    --limit N    : Process only N servers (for testing)
    --verbose    : Show detailed parsing results
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from src.parsers.readme_parser import ReadmeParser
from src.database.models_normalized import (
    Server,
    MarkdownContent,
    McpConfigNpm,
    McpConfigDocker,
)
from loguru import logger


# Database configuration
DB_PATH = Path(__file__).parent.parent / "data" / "mcp_servers.db"


class ConfigBackfiller:
    """Backfill configuration tables from existing README content"""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
        self.Session = sessionmaker(bind=self.engine)

        # Statistics
        self.stats = {
            "total_processed": 0,
            "npm_extracted": 0,
            "docker_extracted": 0,
            "no_config": 0,
            "parse_errors": 0,
            "already_exists": 0,
        }
        self.failures: List[Dict] = []

    def get_servers_needing_backfill(self, session, limit: Optional[int] = None):
        """Get servers with READMEs but no config entries"""
        from sqlalchemy.orm import joinedload

        # Get servers with README content
        servers_with_readme = (
            session.query(Server)
            .join(MarkdownContent, Server.id == MarkdownContent.server_id)
            .filter(MarkdownContent.content_type == "readme")
            .filter(MarkdownContent.content.isnot(None))
            .options(joinedload(Server.markdown_contents))  # Eager load markdown_contents
        )

        # Exclude servers that already have npm OR docker config
        servers_with_npm = session.query(McpConfigNpm.server_id).subquery()
        servers_with_docker = session.query(McpConfigDocker.server_id).subquery()

        servers_needing_backfill = servers_with_readme.filter(
            ~Server.id.in_(select(servers_with_npm)),
            ~Server.id.in_(select(servers_with_docker)),
        )

        if limit:
            servers_needing_backfill = servers_needing_backfill.limit(limit)

        result = servers_needing_backfill.all()
        logger.info(f"Found {len(result)} servers needing config backfill")
        return result

    def extract_config_from_readme(
        self, server: Server, readme_content: str
    ) -> Optional[Dict]:
        """Parse README and extract configuration"""
        try:
            parser = ReadmeParser(readme_content)
            config_data = parser.parse_all()

            if not config_data or not config_data.get("installation_config"):
                return None

            return config_data

        except Exception as e:
            logger.warning(f"Failed to parse README for {server.slug}: {e}")
            return None

    def save_npm_config(self, session, server: Server, config_data: Dict) -> bool:
        """Save NPM configuration to database"""
        install_config = config_data.get("installation_config", {})

        if install_config.get("type") != "npm":
            return False

        try:
            # Check if already exists
            existing = (
                session.query(McpConfigNpm)
                .filter(McpConfigNpm.server_id == server.id)
                .first()
            )

            if existing:
                self.stats["already_exists"] += 1
                logger.warning(f"NPM config already exists for {server.slug}")
                return False

            # Create new config
            mcp_config = McpConfigNpm(
                server_id=server.id,
                command=install_config.get("command", "npx"),
                args=json.dumps(install_config.get("args", [])),
                env_required=json.dumps(config_data.get("env_required", [])),
                env_descriptions=json.dumps(config_data.get("env_descriptions", {})),
                runtime=install_config.get("runtime", "node"),
            )

            if not self.dry_run:
                session.add(mcp_config)
                session.flush()

            self.stats["npm_extracted"] += 1

            if self.verbose:
                logger.success(
                    f"NPM config extracted for {server.slug}:\n"
                    f"   Command: {mcp_config.command} {json.loads(mcp_config.args)}\n"
                    f"   Env vars: {json.loads(mcp_config.env_required)}"
                )
            else:
                logger.success(f"NPM: {server.slug}")

            return True

        except Exception as e:
            logger.error(f"Failed to save NPM config for {server.slug}: {e}")
            self.failures.append(
                {"server": server.slug, "type": "npm", "error": str(e)}
            )
            self.stats["parse_errors"] += 1
            return False

    def save_docker_config(self, session, server: Server, config_data: Dict) -> bool:
        """Save Docker configuration to database"""
        install_config = config_data.get("installation_config", {})

        if install_config.get("type") != "docker":
            return False

        try:
            # Check if already exists
            existing = (
                session.query(McpConfigDocker)
                .filter(McpConfigDocker.server_id == server.id)
                .first()
            )

            if existing:
                self.stats["already_exists"] += 1
                logger.warning(f"Docker config already exists for {server.slug}")
                return False

            # Create new config
            docker_config = McpConfigDocker(
                server_id=server.id,
                docker_image=install_config.get("docker_image"),
                docker_tag=install_config.get("docker_tag", "latest"),
                docker_command=json.dumps(install_config.get("docker_command", [])),
                env_required=json.dumps(config_data.get("env_required", [])),
                env_descriptions=json.dumps(config_data.get("env_descriptions", {})),
                ports=json.dumps(install_config.get("ports", {})),
                volumes=json.dumps(install_config.get("volumes", {})),
                network_mode=install_config.get("network_mode"),
                runtime="docker",
            )

            if not self.dry_run:
                session.add(docker_config)
                session.flush()

            self.stats["docker_extracted"] += 1

            if self.verbose:
                logger.success(
                    f"Docker config extracted for {server.slug}:\n"
                    f"   Image: {docker_config.docker_image}:{docker_config.docker_tag}\n"
                    f"   Env vars: {json.loads(docker_config.env_required)}"
                )
            else:
                logger.success(f"Docker: {server.slug}")

            return True

        except Exception as e:
            logger.error(f"Failed to save Docker config for {server.slug}: {e}")
            self.failures.append(
                {"server": server.slug, "type": "docker", "error": str(e)}
            )
            self.stats["parse_errors"] += 1
            return False

    def process_server(self, session, server: Server) -> bool:
        """Process a single server"""
        self.stats["total_processed"] += 1

        # Get README content
        readme = next(
            (
                mc
                for mc in server.markdown_contents
                if mc.content_type == "readme" and mc.content
            ),
            None,
        )

        if not readme:
            logger.warning(f"No README content for {server.slug}")
            self.stats["no_config"] += 1
            return False

        # Extract configuration
        config_data = self.extract_config_from_readme(server, readme.content)

        if not config_data:
            if self.verbose:
                logger.info(f"No config found for {server.slug}")
            self.stats["no_config"] += 1
            return False

        # Save configuration based on type
        install_config = config_data.get("installation_config", {})
        config_type = install_config.get("type")

        if config_type == "npm":
            return self.save_npm_config(session, server, config_data)
        elif config_type == "docker":
            return self.save_docker_config(session, server, config_data)
        else:
            if self.verbose:
                logger.warning(
                    f"Unknown config type '{config_type}' for {server.slug}"
                )
            self.stats["no_config"] += 1
            return False

    def run(self, limit: Optional[int] = None):
        """Run the backfill process"""
        logger.info("=" * 70)
        logger.info("MCP Configuration Backfill")
        logger.info("=" * 70)

        if self.dry_run:
            logger.warning("DRY RUN MODE - No changes will be saved to database")

        # Process each server
        session = self.Session()
        try:
            # Get servers needing backfill (within same session)
            servers = self.get_servers_needing_backfill(session, limit)

            if not servers:
                logger.info("No servers need backfilling")
                return

            logger.info(f"Processing {len(servers)} servers...\n")

            for idx, server in enumerate(servers, 1):
                if not self.verbose:
                    logger.info(f"[{idx}/{len(servers)}] Processing {server.slug}...")

                try:
                    self.process_server(session, server)

                    if not self.dry_run:
                        session.commit()

                except Exception as e:
                    session.rollback()
                    logger.error(f"Error processing {server.slug}: {e}")
                    self.failures.append(
                        {"server": server.slug, "type": "unknown", "error": str(e)}
                    )
                    self.stats["parse_errors"] += 1

        finally:
            session.close()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print backfill summary"""
        logger.info("\n" + "=" * 70)
        logger.info("BACKFILL SUMMARY")
        logger.info("=" * 70)

        logger.info(f"Total servers processed: {self.stats['total_processed']}")
        logger.success(f"NPM configs extracted: {self.stats['npm_extracted']}")
        logger.success(f"Docker configs extracted: {self.stats['docker_extracted']}")
        logger.info(f"No config found: {self.stats['no_config']}")
        logger.warning(f"Parse errors: {self.stats['parse_errors']}")

        if self.stats["already_exists"] > 0:
            logger.info(f"Already existed: {self.stats['already_exists']}")

        # Success rate
        total_extracted = self.stats["npm_extracted"] + self.stats["docker_extracted"]
        if self.stats["total_processed"] > 0:
            success_rate = (total_extracted / self.stats["total_processed"]) * 100
            logger.info(f"\nSuccess rate: {success_rate:.2f}%")

        # Show failures
        if self.failures and self.verbose:
            logger.warning(f"\nFailed extractions ({len(self.failures)}):")
            for failure in self.failures[:10]:  # Show first 10
                logger.warning(
                    f"  - {failure['server']} ({failure['type']}): {failure['error']}"
                )
            if len(self.failures) > 10:
                logger.warning(f"  ... and {len(self.failures) - 10} more")

        if self.dry_run:
            logger.warning("\nDRY RUN - No changes were saved to database")

        logger.info("=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Backfill MCP configurations from existing README content"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save to database, just show what would be extracted",
    )
    parser.add_argument(
        "--limit", type=int, help="Process only N servers (for testing)", default=None
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed parsing results"
    )

    args = parser.parse_args()

    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG" if args.verbose else "INFO",
    )

    # Check database exists
    if not DB_PATH.exists():
        logger.error(f"❌ Database not found at: {DB_PATH}")
        sys.exit(1)

    # Run backfill
    backfiller = ConfigBackfiller(dry_run=args.dry_run, verbose=args.verbose)
    backfiller.run(limit=args.limit)


if __name__ == "__main__":
    main()
