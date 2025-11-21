"""
Enrichers for MCP server data
"""
from .github_enricher import GitHubEnricher
from .npm_enricher import NpmEnricher

__all__ = ['GitHubEnricher', 'NpmEnricher']
