-- ============================================================================
-- MCP Hub - SQLite Normalized Schema v1.0
-- ============================================================================
-- Description: Complete normalized schema with 11 tables for MCP servers
-- Adapted from PostgreSQL to SQLite
-- Date: 2025-01-19
-- ============================================================================

-- ============================================================================
-- TABLE 1: servers (Core table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS servers (
  -- Identifiers
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  slug TEXT UNIQUE NOT NULL CHECK (slug GLOB '[a-z0-9-]*'),

  -- Basic information
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  tagline TEXT NOT NULL DEFAULT '',
  short_description TEXT NOT NULL DEFAULT '',
  logo_url TEXT,
  homepage_url TEXT,

  -- Internal metrics
  install_count INTEGER DEFAULT 0,
  favorite_count INTEGER DEFAULT 0,
  tools_count INTEGER DEFAULT 0,

  -- Status
  status TEXT DEFAULT 'approved' CHECK (status IN ('approved', 'pending', 'rejected')),
  verification_status TEXT DEFAULT 'unverified' CHECK (verification_status IN ('verified', 'unverified')),

  -- Creator (denormalized for performance)
  creator_id TEXT,  -- UUID as TEXT
  creator_name TEXT,
  creator_username TEXT NOT NULL,

  -- Timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  published_at DATETIME,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for servers
CREATE INDEX IF NOT EXISTS idx_servers_slug ON servers(slug);
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_creator_username ON servers(creator_username);
CREATE INDEX IF NOT EXISTS idx_servers_updated_at ON servers(updated_at DESC);

-- ============================================================================
-- TABLE 2: markdown_content (Markdown content)
-- ============================================================================

CREATE TABLE IF NOT EXISTS markdown_content (
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  server_id TEXT NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  -- Content type
  content_type TEXT NOT NULL CHECK (content_type IN ('about', 'readme', 'faq', 'tools')),

  -- Markdown content
  content TEXT NOT NULL,
  content_html TEXT, -- Pre-generated HTML version (optional)

  -- Metadata
  word_count INTEGER,
  estimated_reading_time_minutes INTEGER,
  extracted_from TEXT, -- Source URL

  -- Timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- Constraint: one content of each type per server
  UNIQUE(server_id, content_type)
);

-- Indexes for markdown_content
CREATE INDEX IF NOT EXISTS idx_markdown_server_id ON markdown_content(server_id);
CREATE INDEX IF NOT EXISTS idx_markdown_content_type ON markdown_content(content_type);

-- ============================================================================
-- TABLE 3: github_info (GitHub information)
-- ============================================================================

CREATE TABLE IF NOT EXISTS github_info (
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  server_id TEXT UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  -- URLs and identification
  github_url TEXT NOT NULL,
  github_owner TEXT NOT NULL,
  github_repo TEXT NOT NULL,

  -- Metrics
  github_stars INTEGER DEFAULT 0,
  github_forks INTEGER DEFAULT 0,
  github_watchers INTEGER DEFAULT 0,
  github_open_issues INTEGER DEFAULT 0,

  -- Activity
  github_last_commit DATETIME,
  github_created_at DATETIME,

  -- Branches
  default_branch TEXT DEFAULT 'main',

  -- Sync timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for github_info
CREATE INDEX IF NOT EXISTS idx_github_info_server_id ON github_info(server_id);
CREATE INDEX IF NOT EXISTS idx_github_info_stars ON github_info(github_stars DESC);
CREATE INDEX IF NOT EXISTS idx_github_info_owner ON github_info(github_owner);
CREATE INDEX IF NOT EXISTS idx_github_info_last_commit ON github_info(github_last_commit DESC);

-- ============================================================================
-- TABLE 4: npm_info (npm information)
-- ============================================================================

CREATE TABLE IF NOT EXISTS npm_info (
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  server_id TEXT UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  -- Identification
  npm_package TEXT NOT NULL,
  npm_version TEXT NOT NULL,

  -- Metrics
  npm_downloads_weekly INTEGER DEFAULT 0,
  npm_downloads_monthly INTEGER DEFAULT 0,

  -- Metadata
  npm_license TEXT,
  npm_homepage TEXT,
  npm_repository_url TEXT,

  -- Versions
  latest_version TEXT,
  latest_version_published_at DATETIME,

  -- Sync timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for npm_info
CREATE INDEX IF NOT EXISTS idx_npm_info_server_id ON npm_info(server_id);
CREATE INDEX IF NOT EXISTS idx_npm_info_package ON npm_info(npm_package);
CREATE INDEX IF NOT EXISTS idx_npm_info_downloads ON npm_info(npm_downloads_weekly DESC);

-- ============================================================================
-- TABLE 5: mcp_config_npm (NPM configuration)
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcp_config_npm (
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  server_id TEXT UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  -- Installation command
  command TEXT NOT NULL DEFAULT 'npx', -- npx or node
  args TEXT NOT NULL, -- JSON array as TEXT: ["arg1", "arg2"]

  -- Required environment variables
  env_required TEXT DEFAULT '[]', -- JSON array as TEXT

  -- Environment variable descriptions (JSON as TEXT)
  env_descriptions TEXT DEFAULT '{}', -- JSON object as TEXT
  -- Format: { "VAR_NAME": { "label": "...", "description": "...", "type": "secret", "get_url": "...", "example": "..." } }

  -- Metadata
  runtime TEXT DEFAULT 'node',

  -- Timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  CHECK (command IN ('npx', 'node', 'npm'))
);

-- Index for mcp_config_npm
CREATE INDEX IF NOT EXISTS idx_mcp_npm_server_id ON mcp_config_npm(server_id);

-- ============================================================================
-- TABLE 6: mcp_config_docker (Docker configuration)
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcp_config_docker (
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  server_id TEXT UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  -- Docker image
  docker_image TEXT NOT NULL, -- Ex: "postgres:latest"
  docker_tag TEXT DEFAULT 'latest',

  -- Docker command (JSON array as TEXT)
  docker_command TEXT DEFAULT '[]',

  -- Environment variables (JSON array as TEXT)
  env_required TEXT DEFAULT '[]',
  env_descriptions TEXT DEFAULT '{}', -- JSON object as TEXT

  -- Ports (JSON object as TEXT)
  ports TEXT DEFAULT '{}', -- Ex: { "5432": "5432" }

  -- Volumes (JSON object as TEXT)
  volumes TEXT DEFAULT '{}', -- Ex: { "/data": "/var/lib/postgresql/data" }

  -- Network configuration
  network_mode TEXT DEFAULT 'bridge',

  -- Metadata
  runtime TEXT DEFAULT 'docker',

  -- Timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for mcp_config_docker
CREATE INDEX IF NOT EXISTS idx_mcp_docker_server_id ON mcp_config_docker(server_id);

-- ============================================================================
-- TRIGGER: Ensure server has only npm OR docker config (mutually exclusive)
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS enforce_single_mcp_config_npm
BEFORE INSERT ON mcp_config_npm
FOR EACH ROW
WHEN EXISTS (SELECT 1 FROM mcp_config_docker WHERE server_id = NEW.server_id)
BEGIN
  SELECT RAISE(ABORT, 'Server already has docker config. Cannot add npm config.');
END;

CREATE TRIGGER IF NOT EXISTS enforce_single_mcp_config_docker
BEFORE INSERT ON mcp_config_docker
FOR EACH ROW
WHEN EXISTS (SELECT 1 FROM mcp_config_npm WHERE server_id = NEW.server_id)
BEGIN
  SELECT RAISE(ABORT, 'Server already has npm config. Cannot add docker config.');
END;

-- ============================================================================
-- TABLE 7: tools (MCP tools)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tools (
  id TEXT PRIMARY KEY,  -- UUID as TEXT
  server_id TEXT NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  -- Identification
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT NOT NULL,

  -- Input schema (JSON as TEXT)
  input_schema TEXT NOT NULL, -- JSON Schema as TEXT

  -- Examples (optional)
  example_usage TEXT,
  example_response TEXT,

  -- Metadata
  category TEXT,
  is_dangerous INTEGER DEFAULT 0, -- BOOLEAN as INTEGER (0/1)
  requires_auth INTEGER DEFAULT 0, -- BOOLEAN as INTEGER (0/1)

  -- Display order
  display_order INTEGER DEFAULT 0,

  -- Timestamps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(server_id, name)
);

-- Indexes for tools
CREATE INDEX IF NOT EXISTS idx_tools_server_id ON tools(server_id);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name);

-- ============================================================================
-- TABLE 8: categories (Reusable categories)
-- ============================================================================

CREATE TABLE IF NOT EXISTS categories (
  id TEXT PRIMARY KEY,  -- UUID as TEXT

  -- Identification
  slug TEXT UNIQUE NOT NULL CHECK (slug GLOB '[a-z0-9-]*'),
  name TEXT UNIQUE NOT NULL,

  -- Description
  description TEXT,

  -- Visual
  icon TEXT, -- Icon name or URL
  color TEXT DEFAULT '#3B82F6',

  -- Stats
  server_count INTEGER DEFAULT 0,

  -- Display order
  display_order INTEGER DEFAULT 0,

  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 9: server_categories (Many-to-many junction table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS server_categories (
  server_id TEXT NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
  category_id TEXT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,

  display_order INTEGER DEFAULT 0,
  added_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (server_id, category_id)
);

-- Indexes for server_categories
CREATE INDEX IF NOT EXISTS idx_server_categories_server_id ON server_categories(server_id);
CREATE INDEX IF NOT EXISTS idx_server_categories_category_id ON server_categories(category_id);

-- ============================================================================
-- TABLE 10: tags (Reusable tags)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tags (
  id TEXT PRIMARY KEY,  -- UUID as TEXT

  -- Identification
  slug TEXT UNIQUE NOT NULL CHECK (slug GLOB '[a-z0-9-]*'),
  name TEXT UNIQUE NOT NULL,

  -- Description
  description TEXT,

  -- Visual
  color TEXT DEFAULT '#3B82F6',

  -- Stats
  server_count INTEGER DEFAULT 0,

  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 11: server_tags (Many-to-many junction table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS server_tags (
  server_id TEXT NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
  tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

  display_order INTEGER DEFAULT 0,
  added_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (server_id, tag_id)
);

-- Indexes for server_tags
CREATE INDEX IF NOT EXISTS idx_server_tags_server_id ON server_tags(server_id);
CREATE INDEX IF NOT EXISTS idx_server_tags_tag_id ON server_tags(tag_id);

-- ============================================================================
-- TRIGGERS: Auto-update server_count in categories and tags
-- ============================================================================

-- Trigger to update category server_count on INSERT
CREATE TRIGGER IF NOT EXISTS trigger_category_count_insert
AFTER INSERT ON server_categories
FOR EACH ROW
BEGIN
  UPDATE categories SET server_count = server_count + 1 WHERE id = NEW.category_id;
END;

-- Trigger to update category server_count on DELETE
CREATE TRIGGER IF NOT EXISTS trigger_category_count_delete
AFTER DELETE ON server_categories
FOR EACH ROW
BEGIN
  UPDATE categories SET server_count = server_count - 1 WHERE id = OLD.category_id;
END;

-- Trigger to update tag server_count on INSERT
CREATE TRIGGER IF NOT EXISTS trigger_tag_count_insert
AFTER INSERT ON server_tags
FOR EACH ROW
BEGIN
  UPDATE tags SET server_count = server_count + 1 WHERE id = NEW.tag_id;
END;

-- Trigger to update tag server_count on DELETE
CREATE TRIGGER IF NOT EXISTS trigger_tag_count_delete
AFTER DELETE ON server_tags
FOR EACH ROW
BEGIN
  UPDATE tags SET server_count = server_count - 1 WHERE id = OLD.tag_id;
END;

-- Trigger to update tools_count in servers on INSERT
CREATE TRIGGER IF NOT EXISTS trigger_tools_count_insert
AFTER INSERT ON tools
FOR EACH ROW
BEGIN
  UPDATE servers SET tools_count = tools_count + 1 WHERE id = NEW.server_id;
END;

-- Trigger to update tools_count in servers on DELETE
CREATE TRIGGER IF NOT EXISTS trigger_tools_count_delete
AFTER DELETE ON tools
FOR EACH ROW
BEGIN
  UPDATE servers SET tools_count = tools_count - 1 WHERE id = OLD.server_id;
END;

-- ============================================================================
-- VIEWS: Useful views for common queries
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_servers_complete AS
SELECT
  s.*,
  gh.github_url,
  gh.github_owner,
  gh.github_repo,
  gh.github_stars,
  gh.github_last_commit,
  npm.npm_package,
  npm.npm_version,
  npm.npm_downloads_weekly,
  COALESCE(mcn.runtime, mcd.runtime) as runtime,
  COALESCE(mcn.command, mcd.docker_image) as config_command
FROM servers s
LEFT JOIN github_info gh ON gh.server_id = s.id
LEFT JOIN npm_info npm ON npm.server_id = s.id
LEFT JOIN mcp_config_npm mcn ON mcn.server_id = s.id
LEFT JOIN mcp_config_docker mcd ON mcd.server_id = s.id;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

-- Display migration summary
SELECT 'Migration complete! 11 tables created.' as message;
