SET session_replication_role = replica;

-- Truncate junction tables first
TRUNCATE TABLE mcp_hub.server_tags CASCADE;
TRUNCATE TABLE mcp_hub.server_categories CASCADE;

-- Truncate dependent tables
TRUNCATE TABLE mcp_hub.tools CASCADE;
TRUNCATE TABLE mcp_hub.mcp_config_npm CASCADE;
TRUNCATE TABLE mcp_hub.mcp_config_docker CASCADE;
TRUNCATE TABLE mcp_hub.npm_info CASCADE;
TRUNCATE TABLE mcp_hub.github_info CASCADE;
TRUNCATE TABLE mcp_hub.markdown_content CASCADE;

-- Truncate standalone tables
TRUNCATE TABLE mcp_hub.tags CASCADE;
TRUNCATE TABLE mcp_hub.categories CASCADE;

-- Truncate main table last
TRUNCATE TABLE mcp_hub.servers CASCADE;

SET session_replication_role = DEFAULT;