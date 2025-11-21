#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze Servers Without Config

This script analyzes the 121 servers that don't have extracted configs
to identify common patterns that the ReadmeParser missed.

Usage:
    python scripts/analyze_missing_configs.py [--sample N] [--output report.md]
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models_normalized import (
    Server,
    MarkdownContent,
    McpConfigNpm,
    McpConfigDocker,
)

# Database configuration
DB_PATH = Path(__file__).parent.parent / "data" / "mcp_servers.db"


class MissingConfigAnalyzer:
    """Analyze servers without extracted configs"""

    def __init__(self):
        self.engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
        self.Session = sessionmaker(bind=self.engine)

        # Patterns to detect
        self.patterns = {
            "npm_install": [],
            "pip_install": [],
            "docker_run": [],
            "docker_compose": [],
            "go_install": [],
            "cargo_install": [],
            "git_clone": [],
            "python_m": [],
            "uvx": [],
            "deno": [],
            "configuration_json": [],
            "has_installation_section": [],
            "has_usage_section": [],
            "no_clear_instructions": [],
        }

        self.statistics = {
            "total_without_config": 0,
            "total_analyzed": 0,
            "readme_lengths": [],
            "common_words": Counter(),
        }

    def get_servers_without_config(self) -> List[Server]:
        """Get all servers without npm or docker config"""
        session = self.Session()
        try:
            from sqlalchemy.orm import joinedload

            # Get servers with config
            servers_with_npm = set(
                session.query(McpConfigNpm.server_id).all()
            )
            servers_with_docker = set(
                session.query(McpConfigDocker.server_id).all()
            )
            configured_ids = servers_with_npm.union(servers_with_docker)
            configured_ids = {sid[0] for sid in configured_ids}

            # Get servers with README but no config
            servers = (
                session.query(Server)
                .join(MarkdownContent, Server.id == MarkdownContent.server_id)
                .filter(MarkdownContent.content_type == "readme")
                .filter(MarkdownContent.content.isnot(None))
                .filter(~Server.id.in_(configured_ids))
                .options(joinedload(Server.markdown_contents))
                .all()
            )

            return servers
        finally:
            session.close()

    def analyze_readme(self, readme_content: str) -> Dict:
        """Analyze a single README for patterns"""
        if not readme_content:
            return {"type": "no_readme"}

        content_lower = readme_content.lower()
        analysis = {
            "length": len(readme_content),
            "patterns_found": [],
        }

        # Check for various installation patterns
        if re.search(r"npm\s+install", content_lower):
            analysis["patterns_found"].append("npm_install")
            self.patterns["npm_install"].append(readme_content[:500])

        if re.search(r"pip\s+install", content_lower):
            analysis["patterns_found"].append("pip_install")
            self.patterns["pip_install"].append(readme_content[:500])

        if re.search(r"docker\s+run", content_lower):
            analysis["patterns_found"].append("docker_run")
            self.patterns["docker_run"].append(readme_content[:500])

        if re.search(r"docker-compose", content_lower):
            analysis["patterns_found"].append("docker_compose")
            self.patterns["docker_compose"].append(readme_content[:500])

        if re.search(r"go\s+install", content_lower):
            analysis["patterns_found"].append("go_install")
            self.patterns["go_install"].append(readme_content[:500])

        if re.search(r"cargo\s+install", content_lower):
            analysis["patterns_found"].append("cargo_install")
            self.patterns["cargo_install"].append(readme_content[:500])

        if re.search(r"git\s+clone", content_lower):
            analysis["patterns_found"].append("git_clone")
            self.patterns["git_clone"].append(readme_content[:500])

        if re.search(r"python\s+-m", content_lower):
            analysis["patterns_found"].append("python_m")
            self.patterns["python_m"].append(readme_content[:500])

        if re.search(r"uvx\s+", content_lower):
            analysis["patterns_found"].append("uvx")
            self.patterns["uvx"].append(readme_content[:500])

        if re.search(r"deno\s+", content_lower):
            analysis["patterns_found"].append("deno")
            self.patterns["deno"].append(readme_content[:500])

        # Check for JSON configuration blocks
        if re.search(r'"mcpServers"', readme_content) or re.search(r"claude_desktop_config", content_lower):
            analysis["patterns_found"].append("configuration_json")
            self.patterns["configuration_json"].append(readme_content[:500])

        # Check for sections
        if re.search(r"##?\s*install", content_lower):
            analysis["patterns_found"].append("has_installation_section")
            self.patterns["has_installation_section"].append(readme_content[:500])

        if re.search(r"##?\s*usage", content_lower):
            analysis["patterns_found"].append("has_usage_section")
            self.patterns["has_usage_section"].append(readme_content[:500])

        # If no clear patterns found
        if not analysis["patterns_found"]:
            analysis["patterns_found"].append("no_clear_instructions")
            self.patterns["no_clear_instructions"].append(readme_content[:500])

        return analysis

    def run_analysis(self, sample_size: int = None) -> Dict:
        """Run analysis on all servers without config"""
        print("=" * 70)
        print("ANALYZING SERVERS WITHOUT CONFIG")
        print("=" * 70)

        servers = self.get_servers_without_config()
        self.statistics["total_without_config"] = len(servers)

        if sample_size:
            servers = servers[:sample_size]

        print(f"\nTotal servers without config: {self.statistics['total_without_config']}")
        print(f"Analyzing: {len(servers)} servers\n")

        results = []

        for idx, server in enumerate(servers, 1):
            print(f"[{idx}/{len(servers)}] Analyzing {server.slug}...")

            readme = next(
                (
                    mc
                    for mc in server.markdown_contents
                    if mc.content_type == "readme" and mc.content
                ),
                None,
            )

            if not readme:
                results.append(
                    {"server": server.slug, "analysis": {"type": "no_readme"}}
                )
                continue

            analysis = self.analyze_readme(readme.content)
            results.append({"server": server.slug, "analysis": analysis})

            self.statistics["total_analyzed"] += 1
            self.statistics["readme_lengths"].append(analysis["length"])

        return results

    def generate_report(self, results: List[Dict]) -> str:
        """Generate analysis report"""
        report = []

        report.append("# Analysis Report: Servers Without Config\n")
        report.append(f"**Date:** {Path(__file__).name}\n")
        report.append(f"**Total Servers Without Config:** {self.statistics['total_without_config']}\n")
        report.append(f"**Analyzed:** {self.statistics['total_analyzed']}\n")
        report.append("\n---\n\n")

        # Pattern frequency
        report.append("## Pattern Frequency\n\n")
        report.append("| Pattern | Count | % |\n")
        report.append("|---------|-------|---|\n")

        pattern_counts = {}
        for pattern_name in self.patterns.keys():
            count = len(self.patterns[pattern_name])
            if count > 0:
                pct = (count / self.statistics['total_analyzed'] * 100) if self.statistics['total_analyzed'] > 0 else 0
                pattern_counts[pattern_name] = count
                report.append(f"| {pattern_name.replace('_', ' ').title()} | {count} | {pct:.1f}% |\n")

        report.append("\n")

        # Top patterns
        report.append("## Most Common Patterns (Missed by Parser)\n\n")
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

        for pattern_name, count in sorted_patterns[:10]:
            if count > 0 and pattern_name != "no_clear_instructions":
                report.append(f"### {pattern_name.replace('_', ' ').title()} ({count} servers)\n\n")
                report.append("**Example README excerpts:**\n\n")

                # Show first 3 examples
                for i, example in enumerate(self.patterns[pattern_name][:3], 1):
                    report.append(f"**Example {i}:**\n```\n{example[:300]}...\n```\n\n")

        # Servers without clear instructions
        no_instructions_count = len(self.patterns["no_clear_instructions"])
        if no_instructions_count > 0:
            report.append(f"## Servers Without Clear Installation Instructions ({no_instructions_count})\n\n")
            report.append("These servers have READMEs but no clear installation commands detected.\n\n")
            report.append("**Example excerpts:**\n\n")
            for i, example in enumerate(self.patterns["no_clear_instructions"][:5], 1):
                report.append(f"**Example {i}:**\n```\n{example[:300]}...\n```\n\n")

        # README statistics
        if self.statistics["readme_lengths"]:
            avg_length = sum(self.statistics["readme_lengths"]) / len(self.statistics["readme_lengths"])
            report.append("## README Statistics\n\n")
            report.append(f"- **Average Length:** {int(avg_length):,} characters\n")
            report.append(f"- **Shortest:** {min(self.statistics['readme_lengths']):,} characters\n")
            report.append(f"- **Longest:** {max(self.statistics['readme_lengths']):,} characters\n")
            report.append("\n")

        # Recommendations
        report.append("## Recommendations for Parser Improvements\n\n")

        recommendations = []

        if pattern_counts.get("pip_install", 0) > 5:
            recommendations.append("1. **Add Python/pip support**: Detect `pip install` and `python -m` patterns")

        if pattern_counts.get("uvx", 0) > 3:
            recommendations.append("2. **Add uvx support**: Detect `uvx` package manager (Python)")

        if pattern_counts.get("go_install", 0) > 3:
            recommendations.append("3. **Add Go support**: Detect `go install` patterns")

        if pattern_counts.get("cargo_install", 0) > 3:
            recommendations.append("4. **Add Rust support**: Detect `cargo install` patterns")

        if pattern_counts.get("deno", 0) > 3:
            recommendations.append("5. **Add Deno support**: Detect `deno` runtime commands")

        if pattern_counts.get("git_clone", 0) > 10:
            recommendations.append("6. **Detect git clone patterns**: Many servers require cloning first")

        if pattern_counts.get("configuration_json", 0) > 5:
            recommendations.append("7. **Improve JSON config parsing**: Better detection of Claude Desktop config blocks")

        if pattern_counts.get("no_clear_instructions", 0) > 20:
            recommendations.append("8. **Manual review needed**: Many servers lack standardized installation instructions")

        for rec in recommendations:
            report.append(f"{rec}\n")

        report.append("\n---\n\n")
        report.append("*Report generated by analyze_missing_configs.py*\n")

        return "".join(report)

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 70)
        print("ANALYSIS SUMMARY")
        print("=" * 70)

        print(f"\nTotal servers without config: {self.statistics['total_without_config']}")
        print(f"Analyzed: {self.statistics['total_analyzed']}")

        print("\nPattern Frequency:")
        print("-" * 70)

        pattern_counts = {name: len(examples) for name, examples in self.patterns.items() if len(examples) > 0}
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

        for pattern_name, count in sorted_patterns:
            pct = (count / self.statistics['total_analyzed'] * 100) if self.statistics['total_analyzed'] > 0 else 0
            print(f"  {pattern_name.replace('_', ' ').title():<30} {count:>5} ({pct:>5.1f}%)")

        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze servers without extracted configs"
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Analyze only N servers (for testing)",
        default=None,
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output report file (markdown)",
        default="reports/missing-configs-analysis.md",
    )

    args = parser.parse_args()

    # Check database exists
    if not DB_PATH.exists():
        print(f"Error: Database not found at: {DB_PATH}")
        sys.exit(1)

    # Run analysis
    analyzer = MissingConfigAnalyzer()
    results = analyzer.run_analysis(sample_size=args.sample)

    # Print summary
    analyzer.print_summary()

    # Generate report
    report = analyzer.generate_report(results)

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
