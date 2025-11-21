"""
Parser for extracting tool parameters from README documentation
Supports multiple documentation patterns with priority-based parsing
"""
import re
import json
import sys
from typing import List, Dict, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class ParametersParser:
    """Extract parameters from tool documentation using multiple strategies"""

    def parse_parameters(self, tool_section: str) -> List[Dict]:
        """
        Parse parameters using multiple strategies in priority order

        Args:
            tool_section: The markdown section for a specific tool

        Returns:
            List of parameter dictionaries with: name, type, description, required, default, example
        """
        # Strategy 1: Detailed "Parameters:" section (playwright-mcp style)
        params = self._parse_detailed_parameters(tool_section)
        if params:
            return params

        # Strategy 2: Simple "**Parameters:**" format (jina-mcp-tools style)
        params = self._parse_simple_parameters(tool_section)
        if params:
            return params

        # Strategy 3: "**Arguments:**" section (firecrawl style)
        params = self._parse_arguments_section(tool_section)
        if params:
            return params

        # Strategy 4: Extract from JSON usage examples
        params = self._parse_json_examples(tool_section)
        if params:
            return params

        return []  # No parameters found

    def _parse_detailed_parameters(self, text: str) -> Optional[List[Dict]]:
        """
        Strategy 1: Parse playwright-mcp style parameters
        Format: - Parameters:\n    - `name` (type, optional): description

        Most complete format with all metadata.
        """
        # Look for "- Parameters:" or "  - Parameters:"
        match = re.search(r'- Parameters:\s*\n((?:\s*- `[^`]+`.*\n)+)', text, re.IGNORECASE)
        if not match:
            return None

        params_text = match.group(1)
        params = []

        # Parse each parameter line
        # Pattern: - `name` (type, optional): description
        pattern = r'- `([^`]+)`\s*\(([^)]+)\):?\s*(.+)$'
        for match in re.finditer(pattern, params_text, re.MULTILINE):
            name = match.group(1).strip()
            type_info = match.group(2).strip()
            description = match.group(3).strip()

            # Parse type and optional flag
            # Examples: "string", "boolean, optional", "array, optional"
            type_parts = [p.strip() for p in type_info.split(',')]
            param_type = type_parts[0]
            is_optional = any('optional' in p.lower() for p in type_parts)

            # Extract default value from description
            default = None
            default_patterns = [
                r'[Dd]efaults? to (.+?)[\.\,]',
                r'[Dd]efault:?\s+(.+?)[\.\,]',
                r'[Dd]efault is (.+?)[\.\,]'
            ]
            for pattern in default_patterns:
                default_match = re.search(pattern, description)
                if default_match:
                    default = default_match.group(1).strip()
                    break

            params.append({
                'name': name,
                'type': self._normalize_type(param_type),
                'description': description,
                'required': not is_optional,
                'default_value': default,
                'example_value': None
            })

        return params if params else None

    def _parse_simple_parameters(self, text: str) -> Optional[List[Dict]]:
        """
        Strategy 2: Parse jina-mcp-tools style parameters
        Format: **Parameters:**\n- `name` - description (optional/required/default: value)

        Simpler format with less structure.
        """
        match = re.search(r'\*\*Parameters:\*\*\s*\n((?:- `[^`]+`.*\n)+)', text)
        if not match:
            return None

        params_text = match.group(1)
        params = []

        # Parse each parameter line
        # Pattern: - `name` - description (info)
        pattern = r'- `([^`]+)`\s*-\s*([^(\n]+)(?:\(([^)]+)\))?'
        for match in re.finditer(pattern, params_text):
            name = match.group(1).strip()
            description = match.group(2).strip()
            optional_info = match.group(3).strip() if match.group(3) else ''

            # Parse optional info
            # Examples: "required", "optional", "default: 1"
            info_lower = optional_info.lower()
            is_required = 'required' in info_lower
            is_optional = 'optional' in info_lower

            # Extract default value
            default = None
            default_match = re.search(r'default:\s*(.+)', optional_info, re.IGNORECASE)
            if default_match:
                default = default_match.group(1).strip()

            params.append({
                'name': name,
                'type': None,  # Not specified in this format
                'description': description,
                'required': is_required if (is_required or is_optional) else None,
                'default_value': default,
                'example_value': None
            })

        return params if params else None

    def _parse_arguments_section(self, text: str) -> Optional[List[Dict]]:
        """
        Strategy 3: Parse **Arguments:** section (firecrawl style)
        Format: **Arguments:**\n- `name`: description

        Minimal format with just names and descriptions.
        """
        match = re.search(r'\*\*Arguments:\*\*\s*\n((?:- `[^`]+`:.*\n)+)', text)
        if not match:
            return None

        args_text = match.group(1)
        params = []

        # Parse each argument line
        pattern = r'- `([^`]+)`:\s*(.+)$'
        for match in re.finditer(pattern, args_text, re.MULTILINE):
            name = match.group(1).strip()
            description = match.group(2).strip()

            params.append({
                'name': name,
                'type': None,
                'description': description,
                'required': None,  # Not specified
                'default_value': None,
                'example_value': None
            })

        return params if params else None

    def _parse_json_examples(self, text: str) -> Optional[List[Dict]]:
        """
        Strategy 4: Extract parameters from JSON usage examples
        Format: ```json\n{"name": "tool", "arguments": {...}}

        Infers types from example values.
        """
        # Find JSON code blocks
        pattern = r'```json\s*\n({.*?})\s*\n```'
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match.group(1))
                if 'arguments' in data and isinstance(data['arguments'], dict):
                    params = []
                    for name, value in data['arguments'].items():
                        params.append({
                            'name': name,
                            'type': self._infer_type(value),
                            'description': None,
                            'required': None,  # Cannot determine from example
                            'default_value': None,
                            'example_value': json.dumps(value) if not isinstance(value, str) else value
                        })
                    return params
            except json.JSONDecodeError:
                continue

        return None

    def _infer_type(self, value) -> str:
        """Infer JSON schema type from Python value"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        elif value is None:
            return 'null'
        else:
            return 'string'

    def _normalize_type(self, type_str: str) -> str:
        """Normalize type string to standard JSON schema types"""
        type_lower = type_str.lower().strip()

        # Map common variations to standard types
        type_map = {
            'str': 'string',
            'text': 'string',
            'int': 'integer',
            'num': 'number',
            'float': 'number',
            'double': 'number',
            'bool': 'boolean',
            'arr': 'array',
            'list': 'array',
            'obj': 'object',
            'dict': 'object'
        }

        return type_map.get(type_lower, type_lower)


def test_parameters_parser():
    """Test the parser on sample documentation"""

    parser = ParametersParser()

    print("=" * 80)
    print("TESTING PARAMETERS PARSER")
    print("=" * 80)
    print()

    # Test 1: Playwright style (detailed)
    print("Test 1: Playwright-style (detailed parameters)")
    print("-" * 80)
    playwright_sample = """
- **browser_click**
  - Title: Click
  - Description: Perform click on a web page
  - Parameters:
    - `element` (string): Human-readable element description
    - `ref` (string): Exact target element reference
    - `doubleClick` (boolean, optional): Whether to perform a double click
    - `button` (string, optional): Button to click, defaults to left
  - Read-only: **false**
"""
    params = parser.parse_parameters(playwright_sample)
    print(f"Found {len(params)} parameters:")
    for p in params:
        req = "✓ Required" if p['required'] else "○ Optional"
        print(f"  • {p['name']:20s} ({p['type']:10s}) {req}")
        if p['description']:
            print(f"    └─ {p['description'][:60]}...")
    print()

    # Test 2: Jina style (simple)
    print("Test 2: Jina-style (simple parameters)")
    print("-" * 80)
    jina_sample = """
### jina_reader

Extract and read web page content.

**Parameters:**
- `url` - URL to read (required)
- `page` - Page number for paginated content (default: 1)
- `customTimeout` - Timeout override in seconds (optional)
"""
    params = parser.parse_parameters(jina_sample)
    print(f"Found {len(params)} parameters:")
    for p in params:
        req = "✓ Required" if p['required'] else ("○ Optional" if p['required'] is False else "? Unknown")
        print(f"  • {p['name']:20s} {req}")
        if p['default_value']:
            print(f"    └─ Default: {p['default_value']}")
    print()

    # Test 3: Firecrawl style (JSON examples)
    print("Test 3: Firecrawl-style (JSON examples)")
    print("-" * 80)
    firecrawl_sample = """
### 1. Scrape Tool (`firecrawl_scrape`)

**Usage Example:**

```json
{
  "name": "firecrawl_scrape",
  "arguments": {
    "url": "https://example.com",
    "formats": ["markdown"],
    "onlyMainContent": true,
    "waitFor": 1000,
    "timeout": 30000
  }
}
```
"""
    params = parser.parse_parameters(firecrawl_sample)
    print(f"Found {len(params)} parameters:")
    for p in params:
        print(f"  • {p['name']:20s} ({p['type']:10s}) Example: {p['example_value']}")
    print()

    # Test 4: Arguments style
    print("Test 4: Arguments-style (firecrawl)")
    print("-" * 80)
    arguments_sample = """
**Arguments:**
- `urls`: Array of URLs to extract information from
- `prompt`: Custom prompt for the LLM extraction
- `schema`: JSON schema for structured data extraction
"""
    params = parser.parse_parameters(arguments_sample)
    print(f"Found {len(params)} parameters:")
    for p in params:
        print(f"  • {p['name']:20s}")
        if p['description']:
            print(f"    └─ {p['description']}")
    print()

    print("=" * 80)
    print("TESTS COMPLETED")
    print("=" * 80)


if __name__ == '__main__':
    test_parameters_parser()
