"""
README Parser - Extracts installation config and environment variables
"""
import re
import json
from typing import Dict, List, Optional, Tuple


class ReadmeParser:
    """
    Parses README markdown to extract installation configuration
    """

    def __init__(self, readme_content: str):
        """
        Initialize parser with README content

        Args:
            readme_content: Full README markdown content
        """
        self.content = readme_content
        self.lines = readme_content.split('\n')

    def extract_installation_config(self) -> Optional[Dict]:
        """
        Extract installation command and configuration

        Returns:
            Config dict with command, args, env_vars, or None if not found
        """
        # PHASE 1: Try JSON config blocks first (highest priority)
        json_config = self._extract_json_config_blocks()
        if json_config:
            return json_config

        # PHASE 2: Try git clone + install patterns (before individual commands)
        git_config = self._extract_git_clone_install()
        if git_config:
            return git_config

        # Try Python/pip/uvx configs
        python_config = self._extract_python_config()
        if python_config:
            return python_config

        # Try to extract npm/npx commands
        npm_config = self._extract_npm_config()
        if npm_config:
            return npm_config

        # Try to extract Docker commands
        docker_config = self._extract_docker_config()
        if docker_config:
            return docker_config

        return None

    def _extract_json_config_blocks(self) -> Optional[Dict]:
        """
        PHASE 1: Extract MCP config from JSON code blocks

        Returns:
            npm config dict or None
        """
        code_blocks = self._extract_code_blocks()

        for block in code_blocks:
            # Look for JSON blocks containing mcpServers or claude_desktop_config
            if 'mcpServers' in block or 'claude_desktop_config' in block.lower():
                try:
                    # Try to parse as JSON
                    config = json.loads(block)

                    # Extract mcpServers section
                    mcp_servers = config.get('mcpServers', {})

                    # Get the first server config
                    for server_name, server_config in mcp_servers.items():
                        command = server_config.get('command', 'npx')
                        args = server_config.get('args', [])
                        env = server_config.get('env', {})

                        return {
                            'type': 'npm',
                            'command': command,
                            'args': args,
                            'env_vars': list(env.keys()) if env else []
                        }

                except json.JSONDecodeError:
                    # Try to extract partial JSON
                    continue

        return None

    def _extract_npm_config(self) -> Optional[Dict]:
        """
        Extract npm/npx configuration from README (IMPROVED)

        Returns:
            npm config dict or None
        """
        # Look for code blocks with npx/npm commands
        code_blocks = self._extract_code_blocks()

        for block in code_blocks:
            # Look for npx command (improved pattern)
            npx_match = re.search(r'npx\s+((?:--?[\w-]+\s+)*)([@\w\-\/\.]+)', block)
            if npx_match:
                flags = npx_match.group(1).strip().split() if npx_match.group(1) else []
                package = npx_match.group(2)

                # Build args list
                args = flags if flags else ['-y']
                args.append(package)

                return {
                    'type': 'npm',
                    'command': 'npx',
                    'args': args,
                    'package': package
                }

            # PHASE 1: Improved npm install pattern (with or without -g)
            npm_install_pattern = r'npm\s+install\s+((?:-g\s+)?)([@\w\-\/\.]+)'
            npm_match = re.search(npm_install_pattern, block)
            if npm_match:
                global_flag = npm_match.group(1).strip()
                package = npm_match.group(2)

                args = ['install']
                if global_flag:
                    args.append('-g')
                args.append(package)

                return {
                    'type': 'npm',
                    'command': 'npm',
                    'args': args,
                    'package': package,
                    'runtime': 'node'
                }

        return None

    def _extract_python_config(self) -> Optional[Dict]:
        """
        PHASE 1 & 2: Extract Python/pip/uvx configurations

        Returns:
            python config dict or None
        """
        code_blocks = self._extract_code_blocks()

        for block in code_blocks:
            # PHASE 1: uvx support (Python package runner)
            uvx_pattern = r'uvx\s+((?:--[\w-]+\s+)*)([@\w\-\/\.]+)'
            uvx_match = re.search(uvx_pattern, block)
            if uvx_match:
                flags = uvx_match.group(1).strip()
                package = uvx_match.group(2)

                args = []
                if flags:
                    args.extend(flags.split())
                args.append(package)

                return {
                    'type': 'npm',  # Store as npm type for now (same table)
                    'command': 'uvx',
                    'args': args,
                    'package': package,
                    'runtime': 'python'
                }

            # PHASE 2: pip install pattern
            pip_pattern = r'pip\s+install\s+((?:-e\s+)?)([\w\-\.]+)'
            pip_match = re.search(pip_pattern, block)
            if pip_match:
                editable = pip_match.group(1).strip()
                package = pip_match.group(2)

                args = ['install']
                if editable:
                    args.append('-e')
                args.append(package)

                return {
                    'type': 'npm',  # Store as npm type for now
                    'command': 'pip',
                    'args': args,
                    'package': package,
                    'runtime': 'python'
                }

            # PHASE 2: python -m module execution
            python_m_pattern = r'python\s+-m\s+([\w\.\_]+)'
            python_match = re.search(python_m_pattern, block)
            if python_match:
                module = python_match.group(1)

                return {
                    'type': 'npm',  # Store as npm type for now
                    'command': 'python',
                    'args': ['-m', module],
                    'package': module,
                    'runtime': 'python'
                }

        return None

    def _extract_git_clone_install(self) -> Optional[Dict]:
        """
        PHASE 2: Extract git clone + install patterns

        Returns:
            git-based config dict or None
        """
        # Look for git clone commands
        git_clone_pattern = r'git\s+clone\s+(https?://[^\s]+)'

        matches = re.findall(git_clone_pattern, self.content)
        if matches:
            clone_url = matches[0]

            # Look for install commands after git clone (within next 500 chars)
            idx = self.content.find(clone_url)
            if idx != -1:
                section = self.content[idx:idx+500]

                # Check for npm install
                if 'npm install' in section:
                    return {
                        'type': 'npm',
                        'command': 'git',
                        'args': ['clone', clone_url],
                        'package': clone_url.split('/')[-1].replace('.git', ''),
                        'runtime': 'node',
                        'requires_clone': True
                    }

                # Check for pip install
                if 'pip install' in section:
                    return {
                        'type': 'npm',  # Store as npm type for now
                        'command': 'git',
                        'args': ['clone', clone_url],
                        'package': clone_url.split('/')[-1].replace('.git', ''),
                        'runtime': 'python',
                        'requires_clone': True
                    }

        return None

    def _extract_docker_config(self) -> Optional[Dict]:
        """
        Extract Docker configuration from README

        Returns:
            Docker config dict or None
        """
        code_blocks = self._extract_code_blocks()

        for block in code_blocks:
            # Look for docker run command
            docker_match = re.search(r'docker\s+run\s+(.*?)(\w+/\w+(?::\w+)?)', block, re.DOTALL)
            if docker_match:
                flags = docker_match.group(1).strip()
                image = docker_match.group(2)

                # Parse image and tag
                if ':' in image:
                    image_name, tag = image.split(':', 1)
                else:
                    image_name = image
                    tag = 'latest'

                # Extract ports and volumes from flags
                ports = {}
                volumes = {}

                # Find port mappings: -p 8080:8080
                port_matches = re.findall(r'-p\s+(\d+):(\d+)', flags)
                for host_port, container_port in port_matches:
                    ports[container_port] = host_port

                # Find volume mappings: -v /path:/path
                volume_matches = re.findall(r'-v\s+([\w\/\.-]+):([\w\/\.-]+)', flags)
                for host_path, container_path in volume_matches:
                    volumes[container_path] = host_path

                return {
                    'type': 'docker',
                    'docker_image': image_name,
                    'docker_tag': tag,
                    'ports': ports,
                    'volumes': volumes
                }

        return None

    def extract_environment_variables(self) -> Tuple[List[str], Dict[str, Dict]]:
        """
        Extract required environment variables and their descriptions

        Returns:
            Tuple of (env_required list, env_descriptions dict)
        """
        env_vars = []
        env_descriptions = {}

        # Look for environment variable sections
        env_section = self._find_section(['environment', 'configuration', 'setup', 'env'])

        if not env_section:
            # Look in code blocks for env var patterns
            code_blocks = self._extract_code_blocks()
            for block in code_blocks:
                # Look for export VAR=value or VAR=value patterns
                var_matches = re.findall(r'(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=', block)
                env_vars.extend(var_matches)
        else:
            # Parse environment variable documentation
            lines = env_section.split('\n')

            for i, line in enumerate(lines):
                # Look for variable names (usually in code blocks or bold)
                var_match = re.search(r'`([A-Z_][A-Z0-9_]*)`', line)
                if not var_match:
                    var_match = re.search(r'\*\*([A-Z_][A-Z0-9_]*)\*\*', line)

                if var_match:
                    var_name = var_match.group(1)
                    env_vars.append(var_name)

                    # Try to extract description (rest of the line + next line if bullet point)
                    desc_text = line[var_match.end():].strip(' :-')

                    # If this is a bullet point, get next lines until next bullet
                    if line.strip().startswith(('-', '*', '•')):
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().startswith(('-', '*', '•', '#')):
                            if lines[j].strip():
                                desc_text += ' ' + lines[j].strip()
                            j += 1

                    # Look for "get from" or "obtain from" URLs
                    url_match = re.search(r'(?:get|obtain)\s+(?:from|at)\s+(https?://[^\s\)]+)', desc_text, re.IGNORECASE)
                    get_url = url_match.group(1) if url_match else None

                    # Determine if it's a secret
                    is_secret = any(keyword in var_name.lower() for keyword in ['key', 'token', 'secret', 'password', 'api'])

                    env_descriptions[var_name] = {
                        'label': var_name.replace('_', ' ').title(),
                        'description': desc_text.strip(),
                        'type': 'secret' if is_secret else 'string',
                        'get_url': get_url
                    }

        # Remove duplicates
        env_vars = list(dict.fromkeys(env_vars))

        # Add default descriptions for vars without them
        for var in env_vars:
            if var not in env_descriptions:
                is_secret = any(keyword in var.lower() for keyword in ['key', 'token', 'secret', 'password', 'api'])
                env_descriptions[var] = {
                    'label': var.replace('_', ' ').title(),
                    'description': f'{var.replace("_", " ")} configuration',
                    'type': 'secret' if is_secret else 'string'
                }

        return env_vars, env_descriptions

    def _extract_code_blocks(self) -> List[str]:
        """
        Extract all code blocks from markdown

        Returns:
            List of code block contents
        """
        blocks = []
        in_block = False
        current_block = []

        for line in self.lines:
            if line.strip().startswith('```'):
                if in_block:
                    # End of block
                    blocks.append('\n'.join(current_block))
                    current_block = []
                    in_block = False
                else:
                    # Start of block
                    in_block = True
            elif in_block:
                current_block.append(line)

        return blocks

    def _find_section(self, keywords: List[str]) -> Optional[str]:
        """
        Find a section in the README by keywords

        Args:
            keywords: List of keywords to search for in headers

        Returns:
            Section content or None
        """
        section_start = None

        for i, line in enumerate(self.lines):
            # Check if this is a header line
            if line.startswith('#'):
                header_text = line.lstrip('#').strip().lower()

                # Check if any keyword matches
                if any(keyword in header_text for keyword in keywords):
                    section_start = i + 1
                    break

        if section_start is None:
            return None

        # Extract section until next header of same or higher level
        section_lines = []
        start_level = self.lines[section_start - 1].count('#')

        for i in range(section_start, len(self.lines)):
            line = self.lines[i]

            # Check if this is a header of same or higher level
            if line.startswith('#'):
                current_level = line.count('#')
                if current_level <= start_level:
                    break

            section_lines.append(line)

        return '\n'.join(section_lines)

    def parse_all(self) -> Dict:
        """
        Parse all available information from README

        Returns:
            Dict with all parsed data
        """
        installation_config = self.extract_installation_config()
        env_vars, env_descriptions = self.extract_environment_variables()

        return {
            'installation_config': installation_config,
            'env_required': env_vars,
            'env_descriptions': env_descriptions
        }


# Example usage
if __name__ == '__main__':
    sample_readme = """
# My MCP Server

A sample MCP server.

## Installation

```bash
npx -y @myorg/my-server
```

## Configuration

Set the following environment variables:

- `API_KEY` - Your API key from https://example.com/keys
- `API_SECRET` - Your API secret
- `BASE_URL` - Base URL for the service (default: https://api.example.com)

## Usage

Start the server...
"""

    parser = ReadmeParser(sample_readme)
    result = parser.parse_all()

    print("Installation Config:")
    print(json.dumps(result['installation_config'], indent=2))

    print("\nEnvironment Variables:")
    print(f"Required: {result['env_required']}")
    print(f"\nDescriptions:")
    print(json.dumps(result['env_descriptions'], indent=2))
