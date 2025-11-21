"""
npm Enricher - Fetches package metadata from npm registry
Uses npm Registry API (no authentication required)
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional, List


NPM_REGISTRY_BASE = 'https://registry.npmjs.org'


class NpmEnricher:
    """
    Enriches server data with npm package information
    """

    def __init__(self):
        """Initialize npm enricher"""
        self.session: Optional[aiohttp.ClientSession] = None
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
            'Accept': 'application/json',
            'User-Agent': 'MCP-Hub-Scraper/1.0'
        }
        self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(self, package_name: str) -> Optional[Dict]:
        """
        Make API request to npm registry

        Args:
            package_name: Package name (can include scope, e.g. @org/package)

        Returns:
            JSON response or None if failed
        """
        if not self.session:
            await self.start()

        # URL encode the package name (handles scoped packages)
        url = f"{NPM_REGISTRY_BASE}/{package_name}"
        self.request_count += 1

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    print(f"    ⚠️  Package not found: {package_name}")
                    return None
                else:
                    print(f"    ⚠️  HTTP {response.status}: {package_name}")
                    return None

        except Exception as e:
            print(f"    ❌ Request failed for {package_name}: {e}")
            return None

    async def fetch_package_info(self, package_name: str) -> Optional[Dict]:
        """
        Fetch package metadata from npm registry

        Args:
            package_name: npm package name (e.g., '@modelcontextprotocol/server-brave-search')

        Returns:
            Package info dict or None if failed
        """
        print(f"    📦 Fetching npm data: {package_name}")

        data = await self._make_request(package_name)
        if not data:
            return None

        try:
            # Get latest version info
            latest_version = data.get('dist-tags', {}).get('latest', '')
            versions = data.get('versions', {})
            latest_version_data = versions.get(latest_version, {})

            # Get time info
            time_data = data.get('time', {})
            latest_published = time_data.get(latest_version)

            # Get repository URL
            repository = data.get('repository', {})
            repo_url = None
            if isinstance(repository, dict):
                repo_url = repository.get('url', '')
            elif isinstance(repository, str):
                repo_url = repository

            # Clean repository URL
            if repo_url:
                repo_url = repo_url.replace('git+', '').replace('.git', '')

            # Get homepage
            homepage = data.get('homepage') or latest_version_data.get('homepage')

            # Get license
            license_info = data.get('license') or latest_version_data.get('license')
            license_name = None
            if isinstance(license_info, dict):
                license_name = license_info.get('type') or license_info.get('name')
            elif isinstance(license_info, str):
                license_name = license_info

            # Get download stats (we'll need to make a separate call for this)
            downloads_weekly, downloads_monthly = await self._fetch_download_stats(package_name)

            return {
                'npm_package': package_name,
                'npm_version': latest_version,
                'npm_downloads_weekly': downloads_weekly or 0,
                'npm_downloads_monthly': downloads_monthly or 0,
                'npm_license': license_name,
                'npm_homepage': homepage,
                'npm_repository_url': repo_url,
                'latest_version': latest_version,
                'latest_version_published_at': self._parse_datetime(latest_published),
                'npm_description': data.get('description', ''),
                'npm_keywords': data.get('keywords', []),
                'npm_maintainers': data.get('maintainers', []),
                'last_synced_at': datetime.utcnow()
            }

        except Exception as e:
            print(f"    ❌ Error parsing npm data: {e}")
            return None

    async def _fetch_download_stats(self, package_name: str) -> tuple[Optional[int], Optional[int]]:
        """
        Fetch download statistics from npm download counts API

        Args:
            package_name: npm package name

        Returns:
            Tuple of (weekly_downloads, monthly_downloads) or (None, None) if failed
        """
        try:
            # npm download counts API
            # last-week and last-month endpoints
            weekly_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
            monthly_url = f"https://api.npmjs.org/downloads/point/last-month/{package_name}"

            async with self.session.get(weekly_url) as response:
                if response.status == 200:
                    data = await response.json()
                    weekly = data.get('downloads', 0)
                else:
                    weekly = None

            async with self.session.get(monthly_url) as response:
                if response.status == 200:
                    data = await response.json()
                    monthly = data.get('downloads', 0)
                else:
                    monthly = None

            return weekly, monthly

        except Exception:
            return None, None

    async def enrich_multiple(self, packages: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Enrich multiple packages concurrently

        Args:
            packages: List of package names

        Returns:
            Dict mapping package name to enrichment data
        """
        results = {}

        for package in packages:
            try:
                data = await self.fetch_package_info(package)
                results[package] = data

                # Small delay between requests
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"    ❌ Failed to enrich {package}: {e}")
                results[package] = None

        return results

    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """
        Parse npm datetime string

        Args:
            dt_string: ISO 8601 datetime string

        Returns:
            datetime object or None
        """
        if not dt_string:
            return None

        try:
            # npm uses ISO 8601 format
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except Exception:
            return None

    def get_stats(self) -> Dict:
        """Get enricher statistics"""
        return {
            'requests_made': self.request_count
        }


# Example usage
if __name__ == '__main__':
    async def test():
        async with NpmEnricher() as enricher:
            # Test with a known package
            data = await enricher.fetch_package_info('@modelcontextprotocol/server-brave-search')

            if data:
                print("\n✅ Package Info:")
                print(f"  Package: {data['npm_package']}")
                print(f"  Version: {data['npm_version']}")
                print(f"  License: {data['npm_license']}")
                print(f"  Downloads (weekly): {data['npm_downloads_weekly']:,}")
                print(f"  Downloads (monthly): {data['npm_downloads_monthly']:,}")
                print(f"  Homepage: {data['npm_homepage']}")
                print(f"  Repository: {data['npm_repository_url']}")

            # Show stats
            stats = enricher.get_stats()
            print(f"\n📊 Stats:")
            print(f"  Requests: {stats['requests_made']}")

    asyncio.run(test())
