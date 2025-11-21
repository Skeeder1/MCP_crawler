"""
GitHub Enricher - Fetches repository metadata and README content
Uses GitHub REST API v3 with authentication
"""
import os
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / 'config' / '.env')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_BASE = 'https://api.github.com'


class GitHubEnricher:
    """
    Enriches server data with GitHub repository information
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub enricher

        Args:
            token: GitHub personal access token (optional, uses env var if not provided)
        """
        self.token = token or GITHUB_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        self.request_count = 0

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start HTTP session"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'MCP-Hub-Scraper/1.0'
        }

        if self.token:
            headers['Authorization'] = f'token {self.token}'

        self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _check_rate_limit(self):
        """Check and wait if rate limit is exceeded"""
        if self.rate_limit_remaining <= 1:
            # Wait until rate limit resets
            wait_time = max(0, self.rate_limit_reset - time.time())
            if wait_time > 0:
                print(f"  ⏳ Rate limit reached. Waiting {wait_time:.0f}s...")
                await asyncio.sleep(wait_time + 1)

    async def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Make authenticated API request with rate limit handling

        Args:
            endpoint: API endpoint (e.g., '/repos/owner/repo')

        Returns:
            JSON response or None if failed
        """
        if not self.session:
            await self.start()

        await self._check_rate_limit()

        url = f"{GITHUB_API_BASE}{endpoint}"
        self.request_count += 1

        try:
            async with self.session.get(url) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
                self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))

                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    print(f"    ⚠️  Repository not found: {endpoint}")
                    return None
                elif response.status == 403:
                    print(f"    ⚠️  Rate limit exceeded or access forbidden")
                    return None
                elif response.status == 401:
                    print(f"    ⚠️  Unauthorized - check your GitHub token")
                    return None
                else:
                    print(f"    ⚠️  HTTP {response.status}: {endpoint}")
                    return None

        except Exception as e:
            print(f"    [ERROR] Request failed: {e}")
            return None

    async def fetch_repository_info(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch repository metadata

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository info dict or None if failed
        """
        endpoint = f'/repos/{owner}/{repo}'
        data = await self._make_request(endpoint)

        if not data:
            return None

        # Extract relevant fields
        try:
            return {
                'github_owner': owner,
                'github_repo': repo,
                'github_url': data.get('html_url'),
                'github_stars': data.get('stargazers_count', 0),
                'github_forks': data.get('forks_count', 0),
                'github_watchers': data.get('subscribers_count', 0),
                'github_open_issues': data.get('open_issues_count', 0),
                'github_last_commit': self._parse_datetime(data.get('pushed_at')),
                'github_created_at': self._parse_datetime(data.get('created_at')),
                'default_branch': data.get('default_branch', 'main'),
                'github_description': data.get('description', ''),
                'github_topics': data.get('topics', []),
                'github_language': data.get('language'),
                'github_license': data.get('license', {}).get('name') if data.get('license') else None,
                'last_synced_at': datetime.utcnow()
            }
        except Exception as e:
            print(f"    [ERROR] Error parsing repository data: {e}")
            return None

    async def fetch_readme(self, owner: str, repo: str, branch: str = 'main') -> Optional[Dict]:
        """
        Fetch README.md content

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)

        Returns:
            README info dict or None if failed
        """
        endpoint = f'/repos/{owner}/{repo}/readme'
        data = await self._make_request(endpoint)

        if not data:
            return None

        try:
            # README content is base64 encoded
            import base64
            content_b64 = data.get('content', '')
            content = base64.b64decode(content_b64).decode('utf-8', errors='ignore')

            # Calculate word count
            word_count = len(content.split())

            # Estimate reading time (200 words per minute)
            reading_time = max(1, word_count // 200)

            return {
                'content': content,
                'content_type': 'readme',
                'word_count': word_count,
                'estimated_reading_time_minutes': reading_time,
                'extracted_from': data.get('html_url'),
                'encoding': data.get('encoding', 'base64'),
                'size': data.get('size', 0)
            }
        except Exception as e:
            print(f"    [ERROR] Error parsing README: {e}")
            return None

    async def enrich_server(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch both repository info and README

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Combined enrichment data or None if failed
        """
        print(f"    🐙 Fetching GitHub data: {owner}/{repo}")

        # Fetch repository info
        repo_info = await self.fetch_repository_info(owner, repo)
        if not repo_info:
            return None

        # Fetch README
        branch = repo_info.get('default_branch', 'main')
        readme = await self.fetch_readme(owner, repo, branch)

        return {
            'github_info': repo_info,
            'readme': readme,
            'enrichment_timestamp': datetime.utcnow()
        }

    async def enrich_multiple(self, repositories: List[Dict[str, str]]) -> Dict[str, Optional[Dict]]:
        """
        Enrich multiple repositories concurrently (with rate limiting)

        Args:
            repositories: List of {'owner': str, 'repo': str} dicts

        Returns:
            Dict mapping 'owner/repo' to enrichment data
        """
        results = {}

        for repo_info in repositories:
            owner = repo_info['owner']
            repo = repo_info['repo']
            key = f"{owner}/{repo}"

            try:
                data = await self.enrich_server(owner, repo)
                results[key] = data

                # Be nice to GitHub API - small delay between requests
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"    [ERROR] Failed to enrich {key}: {e}")
                results[key] = None

        return results

    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """
        Parse GitHub datetime string

        Args:
            dt_string: ISO 8601 datetime string

        Returns:
            datetime object or None
        """
        if not dt_string:
            return None

        try:
            # GitHub uses ISO 8601 format: 2024-01-15T10:30:00Z
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except Exception:
            return None

    def get_stats(self) -> Dict:
        """Get enricher statistics"""
        return {
            'requests_made': self.request_count,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': datetime.fromtimestamp(self.rate_limit_reset) if self.rate_limit_reset else None,
            'has_token': bool(self.token)
        }

    async def fetch_languages(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch programming languages used in repository

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dict with language stats or None
        """
        endpoint = f'/repos/{owner}/{repo}/languages'
        data = await self._make_request(endpoint)

        if not data:
            return None

        # Find primary language (most bytes)
        primary = max(data.items(), key=lambda x: x[1])[0] if data else None

        return {
            'languages': data,  # {"TypeScript": 89456, "JavaScript": 12345}
            'primary_language': primary
        }

    async def fetch_contributors(self, owner: str, repo: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Fetch top contributors

        Args:
            owner: Repository owner
            repo: Repository name
            limit: Number of top contributors to fetch

        Returns:
            List of contributor dicts or None
        """
        endpoint = f'/repos/{owner}/{repo}/contributors?per_page={limit}'
        data = await self._make_request(endpoint)

        if not data:
            return None

        contributors = []
        for contrib in data[:limit]:
            contributors.append({
                'login': contrib.get('login'),
                'contributions': contrib.get('contributions', 0),
                'avatar_url': contrib.get('avatar_url')
            })

        return contributors

    async def fetch_latest_release(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch latest release information

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Release info dict or None
        """
        endpoint = f'/repos/{owner}/{repo}/releases/latest'
        data = await self._make_request(endpoint)

        if not data:
            return None

        return {
            'version': data.get('tag_name'),
            'name': data.get('name'),
            'published_at': self._parse_datetime(data.get('published_at')),
            'is_prerelease': data.get('prerelease', False),
            'release_notes': data.get('body', '')
        }

    async def fetch_commits_activity(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch recent commits activity (last 30 days)

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Activity stats or None
        """
        # Get commits from last 30 days
        from datetime import timedelta
        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        endpoint = f'/repos/{owner}/{repo}/commits?since={since}&per_page=100'
        data = await self._make_request(endpoint)

        if not data:
            return None

        return {
            'commit_frequency': len(data)  # Number of commits in last 30 days
        }

    async def fetch_community_files(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Check for community health files

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dict with boolean flags or None
        """
        endpoint = f'/repos/{owner}/{repo}/community/profile'
        data = await self._make_request(endpoint)

        if not data:
            # Fallback: check individually
            return {
                'has_readme': True,  # Assume true if we got this far
                'has_license': False,
                'has_contributing': False,
                'has_code_of_conduct': False
            }

        files = data.get('files', {})
        return {
            'has_readme': files.get('readme') is not None,
            'has_license': files.get('license') is not None,
            'has_contributing': files.get('contributing') is not None,
            'has_code_of_conduct': files.get('code_of_conduct') is not None,
            'health_percentage': data.get('health_percentage', 0)
        }

    def calculate_health_score(self, repo_data: Dict) -> int:
        """
        Calculate project health score (0-100)

        Args:
            repo_data: Comprehensive repository data

        Returns:
            Health score 0-100
        """
        score = 0

        # Stars (max 20 points)
        stars = repo_data.get('github_stars', 0)
        score += min(20, stars // 10)

        # Recent activity (max 20 points)
        commit_freq = repo_data.get('commit_frequency', 0)
        score += min(20, commit_freq * 2)

        # Community files (max 20 points)
        if repo_data.get('has_readme'): score += 5
        if repo_data.get('has_license'): score += 5
        if repo_data.get('has_contributing'): score += 5
        if repo_data.get('has_code_of_conduct'): score += 5

        # Contributors (max 15 points)
        contrib_count = repo_data.get('contributors_count', 0)
        score += min(15, contrib_count * 3)

        # Recent release (max 15 points)
        if repo_data.get('latest_github_version'):
            score += 10
            # Bonus for recent release (within 6 months)
            release_date = repo_data.get('latest_release_date')
            if release_date:
                # Make both datetimes timezone-naive for comparison
                now = datetime.utcnow().replace(tzinfo=None)
                release_naive = release_date.replace(tzinfo=None) if hasattr(release_date, 'tzinfo') else release_date
                days_since = (now - release_naive).days
                if days_since < 180:
                    score += 5

        # Not archived (max 10 points)
        if not repo_data.get('is_archived'):
            score += 10

        return min(100, score)

    async def fetch_comprehensive_info(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch all GitHub information for comprehensive enrichment

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Complete repository data dict or None
        """
        print(f"    [INFO] Fetching comprehensive GitHub data: {owner}/{repo}")

        # Fetch basic repository info (includes stars, forks, etc.)
        repo_info = await self.fetch_repository_info(owner, repo)
        if not repo_info:
            return None

        # Fetch additional data in parallel where possible
        languages_data = await self.fetch_languages(owner, repo)
        contributors_data = await self.fetch_contributors(owner, repo)
        release_data = await self.fetch_latest_release(owner, repo)
        activity_data = await self.fetch_commits_activity(owner, repo)
        community_data = await self.fetch_community_files(owner, repo)

        # Combine all data
        comprehensive_data = {
            # Basic info from fetch_repository_info
            'github_url': repo_info.get('github_url'),
            'github_owner': owner,
            'github_repo': repo,
            'github_full_name': f"{owner}/{repo}",
            'github_description': repo_info.get('github_description'),
            'github_stars': repo_info.get('github_stars', 0),
            'github_forks': repo_info.get('github_forks', 0),
            'github_watchers': repo_info.get('github_watchers', 0),
            'github_open_issues': repo_info.get('github_open_issues', 0),
            'github_last_commit': repo_info.get('github_last_commit'),
            'github_created_at': repo_info.get('github_created_at'),
            'default_branch': repo_info.get('default_branch', 'main'),

            # Languages
            'primary_language': languages_data.get('primary_language') if languages_data else None,
            'languages': languages_data.get('languages') if languages_data else {},
            'github_topics': repo_info.get('github_topics', []),

            # License
            'license_name': repo_info.get('github_license'),

            # Contributors
            'top_contributors': contributors_data if contributors_data else [],
            'contributors_count': len(contributors_data) if contributors_data else 0,

            # Release
            'latest_github_version': release_data.get('version') if release_data else None,
            'latest_release_date': release_data.get('published_at') if release_data else None,
            'release_notes': release_data.get('release_notes') if release_data else None,
            'is_prerelease': release_data.get('is_prerelease', False) if release_data else False,

            # Activity
            'commit_frequency': activity_data.get('commit_frequency', 0) if activity_data else 0,

            # Community files
            'has_readme': community_data.get('has_readme', True) if community_data else True,
            'has_license': community_data.get('has_license', False) if community_data else False,
            'has_contributing': community_data.get('has_contributing', False) if community_data else False,
            'has_code_of_conduct': community_data.get('has_code_of_conduct', False) if community_data else False,

            # Sync timestamp
            'last_synced_at': datetime.utcnow()
        }

        # Calculate health score
        comprehensive_data['github_health_score'] = self.calculate_health_score(comprehensive_data)

        print(f"      [OK] Health score: {comprehensive_data['github_health_score']}/100")
        print(f"      [OK] Stars: {comprehensive_data['github_stars']}")
        print(f"      [OK] Commits (30d): {comprehensive_data['commit_frequency']}")

        return comprehensive_data


# Example usage
if __name__ == '__main__':
    async def test():
        async with GitHubEnricher() as enricher:
            # Test single repository
            data = await enricher.enrich_server('modelcontextprotocol', 'servers')

            if data:
                print("\n✅ Repository Info:")
                print(f"  Stars: {data['github_info']['github_stars']}")
                print(f"  Forks: {data['github_info']['github_forks']}")
                print(f"  Last commit: {data['github_info']['github_last_commit']}")

                if data['readme']:
                    print(f"\n✅ README:")
                    print(f"  Words: {data['readme']['word_count']}")
                    print(f"  Reading time: {data['readme']['estimated_reading_time_minutes']} min")
                    print(f"  Content preview: {data['readme']['content'][:200]}...")

            # Show stats
            stats = enricher.get_stats()
            print(f"\n📊 Stats:")
            print(f"  Requests: {stats['requests_made']}")
            print(f"  Rate limit remaining: {stats['rate_limit_remaining']}")

    asyncio.run(test())
