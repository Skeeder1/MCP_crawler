
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: servers (Core table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS servers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug TEXT UNIQUE NOT NULL CHECK (slug ~ '^[a-z0-9-]+$'),

  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  tagline TEXT NOT NULL DEFAULT '',
  short_description TEXT NOT NULL DEFAULT '',
  logo_url TEXT,
  homepage_url TEXT,

  install_count INTEGER DEFAULT 0,
  favorite_count INTEGER DEFAULT 0,
  tools_count INTEGER DEFAULT 0,

  status TEXT DEFAULT 'approved' CHECK (status IN ('approved', 'pending', 'rejected')),
  verification_status TEXT DEFAULT 'unverified' CHECK (verification_status IN ('verified', 'unverified')),

  creator_id UUID,
  creator_name TEXT,
  creator_username TEXT NOT NULL,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  published_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_servers_slug ON servers(slug);
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_creator_username ON servers(creator_username);
CREATE INDEX IF NOT EXISTS idx_servers_updated_at ON servers(updated_at DESC);

-- ============================================================================
-- TABLE 2: markdown_content
-- ============================================================================

CREATE TABLE IF NOT EXISTS markdown_content (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  content_type TEXT NOT NULL CHECK (content_type IN ('about', 'readme', 'faq', 'tools')),
  content TEXT NOT NULL,
  content_html TEXT,

  word_count INTEGER,
  estimated_reading_time_minutes INTEGER,
  extracted_from TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(server_id, content_type)
);

CREATE INDEX IF NOT EXISTS idx_markdown_server_id ON markdown_content(server_id);
CREATE INDEX IF NOT EXISTS idx_markdown_content_type ON markdown_content(content_type);

-- ============================================================================
-- TABLE 3: github_info
-- ============================================================================

CREATE TABLE IF NOT EXISTS github_info (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  server_id UUID UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  github_url TEXT NOT NULL,
  github_owner TEXT NOT NULL,
  github_repo TEXT NOT NULL,

  github_stars INTEGER DEFAULT 0,
  github_forks INTEGER DEFAULT 0,
  github_watchers INTEGER DEFAULT 0,
  github_open_issues INTEGER DEFAULT 0,

  github_last_commit TIMESTAMPTZ,
  github_created_at TIMESTAMPTZ,

  default_branch TEXT DEFAULT 'main',

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_synced_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_github_info_server_id ON github_info(server_id);
CREATE INDEX IF NOT EXISTS idx_github_info_stars ON github_info(github_stars DESC);
CREATE INDEX IF NOT EXISTS idx_github_info_owner ON github_info(github_owner);

-- ============================================================================
-- TABLE 4: npm_info
-- ============================================================================

CREATE TABLE IF NOT EXISTS npm_info (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  server_id UUID UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  npm_package TEXT NOT NULL,
  npm_version TEXT NOT NULL,

  npm_downloads_weekly INTEGER DEFAULT 0,
  npm_downloads_monthly INTEGER DEFAULT 0,

  npm_license TEXT,
  npm_homepage TEXT,
  npm_repository_url TEXT,

  latest_version TEXT,
  latest_version_published_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_synced_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_npm_info_server_id ON npm_info(server_id);
CREATE INDEX IF NOT EXISTS idx_npm_info_package ON npm_info(npm_package);
CREATE INDEX IF NOT EXISTS idx_npm_info_downloads ON npm_info(npm_downloads_weekly DESC);

-- ============================================================================
-- TABLE 5: mcp_config_npm
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcp_config_npm (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  server_id UUID UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  command TEXT NOT NULL DEFAULT 'npx',
  args TEXT[] NOT NULL,

  env_required TEXT[] DEFAULT '{}',
  env_descriptions JSONB DEFAULT '{}',

  runtime TEXT DEFAULT 'node',

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT mcp_npm_command_check CHECK (command IN ('npx', 'node', 'npm'))
);

CREATE INDEX IF NOT EXISTS idx_mcp_npm_server_id ON mcp_config_npm(server_id);

-- ============================================================================
-- TABLE 6: mcp_config_docker
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcp_config_docker (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  server_id UUID UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  docker_image TEXT NOT NULL,
  docker_tag TEXT DEFAULT 'latest',
  docker_command TEXT[] DEFAULT '{}',

  env_required TEXT[] DEFAULT '{}',
  env_descriptions JSONB DEFAULT '{}',

  ports JSONB DEFAULT '{}',
  volumes JSONB DEFAULT '{}',

  network_mode TEXT DEFAULT 'bridge',
  runtime TEXT DEFAULT 'docker',

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcp_docker_server_id ON mcp_config_docker(server_id);

-- ============================================================================
-- TABLE 7: tools
-- ============================================================================

CREATE TABLE IF NOT EXISTS tools (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT NOT NULL,

  input_schema JSONB NOT NULL,

  example_usage TEXT,
  example_response TEXT,

  category TEXT,
  is_dangerous BOOLEAN DEFAULT FALSE,
  requires_auth BOOLEAN DEFAULT FALSE,

  display_order INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(server_id, name)
);

CREATE INDEX IF NOT EXISTS idx_tools_server_id ON tools(server_id);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name);

-- ============================================================================
-- TABLE 8: categories
-- ============================================================================

CREATE TABLE IF NOT EXISTS categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  slug TEXT UNIQUE NOT NULL CHECK (slug ~ '^[a-z0-9-]+$'),
  name TEXT UNIQUE NOT NULL,

  description TEXT,

  icon TEXT,
  color TEXT DEFAULT '#3B82F6',

  server_count INTEGER DEFAULT 0,
  display_order INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TABLE 9: server_categories
-- ============================================================================

CREATE TABLE IF NOT EXISTS server_categories (
  server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
  category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,

  display_order INTEGER DEFAULT 0,
  added_at TIMESTAMPTZ DEFAULT NOW(),

  PRIMARY KEY (server_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_server_categories_server_id ON server_categories(server_id);
CREATE INDEX IF NOT EXISTS idx_server_categories_category_id ON server_categories(category_id);

-- ============================================================================
-- TABLE 10: tags
-- ============================================================================

CREATE TABLE IF NOT EXISTS tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  slug TEXT UNIQUE NOT NULL CHECK (slug ~ '^[a-z0-9-]+$'),
  name TEXT UNIQUE NOT NULL,

  description TEXT,
  color TEXT DEFAULT '#3B82F6',

  server_count INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TABLE 11: server_tags
-- ============================================================================

CREATE TABLE IF NOT EXISTS server_tags (
  server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

  display_order INTEGER DEFAULT 0,
  added_at TIMESTAMPTZ DEFAULT NOW(),

  PRIMARY KEY (server_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_server_tags_server_id ON server_tags(server_id);
CREATE INDEX IF NOT EXISTS idx_server_tags_tag_id ON server_tags(tag_id);

-- ============================================================================
-- Enable Row Level Security (RLS)
-- ============================================================================

ALTER TABLE servers ENABLE ROW LEVEL SECURITY;
ALTER TABLE markdown_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE npm_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_config_npm ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_config_docker ENABLE ROW LEVEL SECURITY;
ALTER TABLE tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE server_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE server_tags ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies (Allow read for all, write for service role)
-- ============================================================================

-- Servers: Allow read for all
CREATE POLICY "Allow read access to servers" ON servers FOR SELECT USING (true);
CREATE POLICY "Allow service role to manage servers" ON servers FOR ALL USING (auth.role() = 'service_role');

-- Apply same pattern to all tables
CREATE POLICY "Allow read access to markdown_content" ON markdown_content FOR SELECT USING (true);
CREATE POLICY "Allow read access to github_info" ON github_info FOR SELECT USING (true);
CREATE POLICY "Allow read access to npm_info" ON npm_info FOR SELECT USING (true);
CREATE POLICY "Allow read access to mcp_config_npm" ON mcp_config_npm FOR SELECT USING (true);
CREATE POLICY "Allow read access to mcp_config_docker" ON mcp_config_docker FOR SELECT USING (true);
CREATE POLICY "Allow read access to tools" ON tools FOR SELECT USING (true);
CREATE POLICY "Allow read access to categories" ON categories FOR SELECT USING (true);
CREATE POLICY "Allow read access to server_categories" ON server_categories FOR SELECT USING (true);
CREATE POLICY "Allow read access to tags" ON tags FOR SELECT USING (true);
CREATE POLICY "Allow read access to server_tags" ON server_tags FOR SELECT USING (true);
