#!/usr/bin/env python3
"""
Test the improved ReadmeParser with various patterns
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.readme_parser import ReadmeParser
import json


def test_json_config():
    """Test JSON configuration block extraction"""
    readme = """
# Test Server

## Installation

```json
{
  "mcpServers": {
    "test-server": {
      "command": "npx",
      "args": ["-y", "@test/server"],
      "env": {
        "API_KEY": "your_key"
      }
    }
  }
}
```
"""
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()
    print("[OK] JSON Config Test:")
    print(f"   Command: {config['command']}")
    print(f"   Args: {config['args']}")
    print(f"   Env vars: {config.get('env_vars', [])}")
    assert config['command'] == 'npx'
    assert config['args'] == ['-y', '@test/server']
    print()


def test_npm_install():
    """Test npm install pattern"""
    readme = """
# Test Server

Install globally:

```bash
npm install -g @test/server
```
"""
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()
    print("[OK] NPM Install Test:")
    print(f"   Command: {config['command']}")
    print(f"   Args: {config['args']}")
    print(f"   Runtime: {config.get('runtime', 'node')}")
    assert config['command'] == 'npm'
    assert 'install' in config['args']
    print()


def test_uvx():
    """Test uvx support"""
    readme = """
# Test Server

```bash
uvx mcp-server-package
```
"""
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()
    print("[OK] UVX Test:")
    print(f"   Command: {config['command']}")
    print(f"   Args: {config['args']}")
    print(f"   Runtime: {config.get('runtime', 'node')}")
    assert config['command'] == 'uvx'
    assert config['runtime'] == 'python'
    print()


def test_pip_install():
    """Test pip install pattern"""
    readme = """
# Test Server

```bash
pip install mcp-server-package
```
"""
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()
    print("[OK] Pip Install Test:")
    print(f"   Command: {config['command']}")
    print(f"   Args: {config['args']}")
    print(f"   Runtime: {config.get('runtime', 'node')}")
    assert config['command'] == 'pip'
    assert config['runtime'] == 'python'
    print()


def test_python_m():
    """Test python -m pattern"""
    readme = """
# Test Server

```bash
python -m mcp_server.main
```
"""
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()
    print("[OK] Python -m Test:")
    print(f"   Command: {config['command']}")
    print(f"   Args: {config['args']}")
    print(f"   Runtime: {config.get('runtime', 'node')}")
    assert config['command'] == 'python'
    assert config['args'] == ['-m', 'mcp_server.main']
    print()


def test_git_clone():
    """Test git clone + install pattern"""
    readme = """
# Test Server

Clone and install:

```bash
git clone https://github.com/user/repo
cd repo
npm install
npm start
```
"""
    parser = ReadmeParser(readme)
    config = parser.extract_installation_config()
    print("[OK] Git Clone Test:")
    print(f"   Command: {config['command']}")
    print(f"   Args: {config['args'][:2]}...")
    print(f"   Runtime: {config.get('runtime', 'node')}")
    print(f"   Requires clone: {config.get('requires_clone', False)}")
    assert config['command'] == 'git'
    assert 'clone' in config['args']
    print()


if __name__ == '__main__':
    print("=" * 70)
    print("Testing Improved ReadmeParser - Phases 1 & 2")
    print("=" * 70)
    print()

    try:
        test_json_config()
        test_npm_install()
        test_uvx()
        test_pip_install()
        test_python_m()
        test_git_clone()

        print("=" * 70)
        print("[SUCCESS] All tests passed! Parser is ready for backfill.")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
