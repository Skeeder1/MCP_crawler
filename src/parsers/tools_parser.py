"""
Parser for extracting tools information from MCP server READMEs
"""
import re
from typing import List, Dict, Optional
import json


class ToolsParser:
    """Extract tools from README markdown content"""

    def parse_tools(self, markdown: str) -> List[Dict]:
        """
        Parse tools from README markdown content

        Args:
            markdown: README content as markdown string

        Returns:
            List of tool dictionaries with name, display_name, description
        """
        tools = []

        # Strategy 1: Look for "Available Tools" or "Tools" section
        tools_section = self._extract_tools_section(markdown)
        if tools_section:
            tools.extend(self._parse_tools_from_section(tools_section))

        # Strategy 2: Look for tool listings in code blocks (JSON schemas)
        if not tools:
            tools.extend(self._parse_tools_from_code_blocks(markdown))

        # Strategy 3: Look for function/method names with descriptions
        if not tools:
            tools.extend(self._parse_tools_from_headings(markdown))

        return tools

    def _extract_tools_section(self, markdown: str) -> Optional[str]:
        """Extract the 'Tools' or 'Available Tools' section from markdown"""

        # Pattern to find Tools section (heading + content until next same-level heading)
        # Note: (?=\n##[^#]) ensures we match ## but not ### (prevents premature cutoff)
        patterns = [
            r'##\s*Available\s+Tools\s*\n(.*?)(?=\n##[^#]|\Z)',
            r'##\s*Tools\s*\n(.*?)(?=\n##[^#]|\Z)',
            r'###\s*Available\s+Tools\s*\n(.*?)(?=\n###[^#]|\n##[^#]|\Z)',
            r'###\s*Tools\s*\n(.*?)(?=\n###[^#]|\n##[^#]|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, markdown, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _parse_tools_from_section(self, section: str) -> List[Dict]:
        """Parse tools from a tools section"""
        tools = []

        # Pattern 1: Heading-based (### **tool_name** or ### tool_name)
        # Example: ### **perplexity_search**
        # Note: \n+ allows for multiple blank lines between tools
        heading_pattern = r'###\s*\*\*([a-zA-Z0-9_-]+)\*\*\s*\n(.*?)(?=\n+###\s*\*\*|\Z)'
        matches = re.finditer(heading_pattern, section, re.DOTALL)

        for match in matches:
            name = match.group(1)
            description = match.group(2).strip()
            # Clean description (remove extra newlines, keep first line or paragraph)
            description = self._clean_description(description)

            tools.append({
                'name': name,
                'display_name': self._name_to_display(name),
                'description': description
            })

        # Pattern 2: Numbered heading with backticks (### 1. Tool Name (`tool_name`))
        # Example: ### 1. Scrape Tool (`firecrawl_scrape`)
        if not tools:
            numbered_pattern = r'###\s*\d+\.\s*.*?\(`([a-zA-Z0-9_-]+)`\)\s*\n(.*?)(?=\n+###\s*\d+\.|\Z)'
            matches = re.finditer(numbered_pattern, section, re.DOTALL)

            for match in matches:
                name = match.group(1)
                description = match.group(2).strip()
                description = self._clean_description(description)

                tools.append({
                    'name': name,
                    'display_name': self._name_to_display(name),
                    'description': description
                })

        # Pattern 3: List with backticks (- `tool_name` - description)
        # Example: - `google_search` - Set all the parameters
        # IMPORTANT: Exclude lines under "Parameters:" or "**Parameters:**" sections
        if not tools:
            # First, remove any "Parameters:" sections to avoid false positives
            cleaned_section = self._remove_parameters_sections(section)

            backtick_list_pattern = r'-\s*`([a-zA-Z0-9_-]+)`\s*[-–—]\s*([^\n]+)'
            matches = re.finditer(backtick_list_pattern, cleaned_section)

            for match in matches:
                name = match.group(1)
                description = match.group(2).strip()

                tools.append({
                    'name': name,
                    'display_name': self._name_to_display(name),
                    'description': description
                })

        # Pattern 4: Markdown table (| `tool_name` | description |)
        # Example: |`text_to_audio`|Convert text to audio...|
        if not tools:
            # Look for markdown table rows with backticked tool names
            table_pattern = r'\|\s*`([a-zA-Z0-9_-]+)`\s*\|\s*([^|\n]+)\s*\|'
            matches = re.finditer(table_pattern, section)

            for match in matches:
                name = match.group(1)
                description = match.group(2).strip()

                tools.append({
                    'name': name,
                    'display_name': self._name_to_display(name),
                    'description': description
                })

        # Pattern 5: List-based with bold (- **tool_name**: description)
        # Example: - **search**: Perform a web search
        if not tools:
            list_pattern = r'-\s*\*\*([a-zA-Z0-9_-]+)\*\*:?\s*([^\n]+)'
            matches = re.finditer(list_pattern, section)

            for match in matches:
                name = match.group(1)
                description = match.group(2).strip()

                tools.append({
                    'name': name,
                    'display_name': self._name_to_display(name),
                    'description': description
                })

        # Pattern 6: Simple heading format (### tool_name or ### tool1 / tool2)
        # Example: ### jina_reader or ### jina_search / jina_search_vip
        # This handles plain headings including multi-tool headings
        if not tools:
            # Capture entire heading line (including spaces) up to newline
            simple_heading_pattern = r'###\s+([^\n]+?)\s*\n(.*?)(?=\n###|\n##|\Z)'
            matches = re.finditer(simple_heading_pattern, section, re.DOTALL)

            for match in matches:
                names_str = match.group(1)
                content = match.group(2).strip()

                # Check if multiple tool names separated by /
                if '/' in names_str:
                    # Split by / and process each tool
                    tool_names = [n.strip() for n in names_str.split('/')]
                    for name in tool_names:
                        # Only include if name looks like a tool (snake_case or kebab-case)
                        if '_' in name or '-' in name:
                            description = self._clean_description(content)
                            if description:
                                tools.append({
                                    'name': name,
                                    'display_name': self._name_to_display(name),
                                    'description': description
                                })
                else:
                    # Single tool name
                    name = names_str
                    # Only include if name looks like a tool (snake_case or kebab-case)
                    if '_' in name or '-' in name:
                        description = self._clean_description(content)
                        if description:
                            tools.append({
                                'name': name,
                                'display_name': self._name_to_display(name),
                                'description': description
                            })

        return tools

    def _parse_tools_from_code_blocks(self, markdown: str) -> List[Dict]:
        """Parse tools from JSON schema code blocks"""
        tools = []

        # Find JSON code blocks
        code_block_pattern = r'```(?:json|javascript|typescript)?\n(.*?)```'
        matches = re.finditer(code_block_pattern, markdown, re.DOTALL)

        for match in matches:
            code = match.group(1)
            try:
                # Try to parse as JSON
                data = json.loads(code)

                # Look for tool-like structures
                if isinstance(data, dict):
                    # Check if it's a tools array
                    if 'tools' in data and isinstance(data['tools'], list):
                        for tool in data['tools']:
                            if isinstance(tool, dict) and 'name' in tool:
                                tools.append({
                                    'name': tool.get('name'),
                                    'display_name': tool.get('display_name') or self._name_to_display(tool.get('name')),
                                    'description': tool.get('description', ''),
                                    'input_schema': tool.get('input_schema')
                                })
                    # Check if it's a single tool definition
                    elif 'name' in data:
                        tools.append({
                            'name': data.get('name'),
                            'display_name': data.get('display_name') or self._name_to_display(data.get('name')),
                            'description': data.get('description', ''),
                            'input_schema': data.get('input_schema')
                        })
            except json.JSONDecodeError:
                # Not valid JSON, skip
                continue

        return tools

    def _parse_tools_from_headings(self, markdown: str) -> List[Dict]:
        """Parse tools from heading patterns throughout the document"""
        tools = []

        # Look for patterns like:
        # ### tool_name / tool_name2 (multiple tools on one line)
        # Description text
        pattern_multi = r'###\s+([a-zA-Z0-9_/-]+)\s*\n(.*?)(?=\n###|\n##|\Z)'
        matches = re.finditer(pattern_multi, markdown, re.DOTALL)

        for match in matches:
            names_str = match.group(1)
            content = match.group(2).strip()

            # Check if multiple tool names separated by /
            if '/' in names_str:
                # Split by / and process each tool
                tool_names = [n.strip() for n in names_str.split('/')]
                for name in tool_names:
                    if '_' in name or '-' in name:
                        description = self._clean_description(content)
                        if description:
                            tools.append({
                                'name': name,
                                'display_name': self._name_to_display(name),
                                'description': description
                            })
            else:
                # Single tool name
                name = names_str
                # Only include if name looks like a tool (snake_case or kebab-case)
                if '_' in name or '-' in name:
                    description = self._clean_description(content)
                    if description:
                        tools.append({
                            'name': name,
                            'display_name': self._name_to_display(name),
                            'description': description
                        })

        return tools

    def _remove_parameters_sections(self, text: str) -> str:
        """
        Remove Parameters/Arguments sections from text to avoid extracting
        parameters as tools
        """
        # Pattern 1: Remove "- Parameters:" sections
        text = re.sub(r'- Parameters:\s*\n(?:\s*- `[^`]+`.*\n)+', '', text, flags=re.IGNORECASE)

        # Pattern 2: Remove "**Parameters:**" sections
        text = re.sub(r'\*\*Parameters:\*\*\s*\n(?:- `[^`]+`.*\n)+', '', text, flags=re.IGNORECASE)

        # Pattern 3: Remove "**Arguments:**" sections
        text = re.sub(r'\*\*Arguments:\*\*\s*\n(?:- `[^`]+`:.*\n)+', '', text, flags=re.IGNORECASE)

        return text

    def _clean_description(self, text: str) -> str:
        """Clean and format description text"""
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Code

        # Get first paragraph or first line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Return first non-empty line
            return lines[0]

        return text.strip()

    def _name_to_display(self, name: str) -> str:
        """Convert snake_case or kebab-case name to Display Name"""
        if not name:
            return ""

        # Replace underscores and hyphens with spaces
        display = name.replace('_', ' ').replace('-', ' ')

        # Capitalize each word
        display = ' '.join(word.capitalize() for word in display.split())

        return display


def test_parser():
    """Test the parser with sample markdown"""

    # Sample markdown from Perplexity README
    sample_md = """
# Perplexity API Platform MCP Server

## Available Tools

### **perplexity_search**
Direct web search using the Perplexity Search API. Returns ranked search results with metadata, perfect for finding current information.

### **perplexity_ask**
General-purpose conversational AI with real-time web search using the `sonar-pro` model. Great for quick questions and everyday searches.

### **perplexity_research**
Deep, comprehensive research using the `sonar-deep-research` model. Ideal for thorough analysis and detailed reports.

### **perplexity_reason**
Advanced reasoning and problem-solving using the `sonar-reasoning-pro` model. Perfect for complex analytical tasks.

## Configuration
...
"""

    parser = ToolsParser()

    # Debug: check section extraction
    section = parser._extract_tools_section(sample_md)
    if section:
        print(f"Extracted section ({len(section)} chars):")
        print("=" * 70)
        print(section[:500])
        print("=" * 70)
        print()

        # Debug: check pattern matching
        heading_pattern = r'###\s*\*\*([a-zA-Z0-9_-]+)\*\*\s*\n(.*?)(?=\n+###\s*\*\*|\Z)'
        matches = list(re.finditer(heading_pattern, section, re.DOTALL))
        print(f"Found {len(matches)} pattern matches")
        print()

    tools = parser.parse_tools(sample_md)

    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"\nName: {tool['name']}")
        print(f"Display: {tool['display_name']}")
        print(f"Description: {tool['description']}")


if __name__ == '__main__':
    test_parser()
