-- Migration 004: Enhanced GitHub Info Table
-- Description: Replace simple github_info with comprehensive GitHub data
-- Date: 2025-01-20
-- SQLite adaptation of PostgreSQL schema

-- Step 1: Backup existing data
CREATE TEMPORARY TABLE github_info_backup AS
SELECT server_id, github_url, github_owner, github_repo, default_branch
FROM github_info;

-- Step 2: Drop old table and recreate with new schema
DROP TABLE IF EXISTS github_info;

-- Step 3: Create enhanced github_info table
CREATE TABLE github_info (
    id TEXT PRIMARY KEY NOT NULL,
    server_id TEXT UNIQUE NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

    -- URLs
    github_url TEXT NOT NULL,
    github_owner TEXT NOT NULL,
    github_repo TEXT NOT NULL,
    github_full_name TEXT NOT NULL,

    -- Main metrics ⭐
    github_stars INTEGER DEFAULT 0,
    github_forks INTEGER DEFAULT 0,
    github_watchers INTEGER DEFAULT 0,
    github_open_issues INTEGER DEFAULT 0,

    -- Activity
    github_last_commit DATETIME,
    github_created_at DATETIME,
    github_updated_at DATETIME,
    commit_frequency INTEGER, -- commits/30 days

    -- Project info
    github_description TEXT,
    primary_language TEXT, -- "TypeScript", "Python"
    languages TEXT, -- JSON: {"TypeScript": 89456, "JavaScript": 12345}
    github_topics TEXT, -- JSON array: ["mcp", "railway", "deployment"]

    -- License
    license TEXT, -- "mit", "apache-2.0"
    license_name TEXT, -- "MIT License"

    -- Status
    is_archived BOOLEAN DEFAULT 0,
    is_fork BOOLEAN DEFAULT 0,
    is_disabled BOOLEAN DEFAULT 0,
    default_branch TEXT DEFAULT 'main',

    -- Release
    latest_github_version TEXT,
    latest_release_date DATETIME,
    release_notes TEXT,
    is_prerelease BOOLEAN DEFAULT 0,

    -- Community
    contributors_count INTEGER DEFAULT 0,
    top_contributors TEXT, -- JSON: [{"login": "user1", "contributions": 145}]

    -- Project quality
    github_health_score INTEGER CHECK (github_health_score >= 0 AND github_health_score <= 100),
    has_readme BOOLEAN DEFAULT 1,
    has_license BOOLEAN DEFAULT 0,
    has_contributing BOOLEAN DEFAULT 0,
    has_code_of_conduct BOOLEAN DEFAULT 0,

    -- Trending (trending detection)
    stars_last_week INTEGER DEFAULT 0,
    stars_last_month INTEGER DEFAULT 0,

    -- README
    readme_size INTEGER, -- Size in bytes

    -- Sync
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Step 4: Restore basic data from backup
INSERT INTO github_info (id, server_id, github_url, github_owner, github_repo, github_full_name, default_branch)
SELECT
    lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6))),
    server_id,
    github_url,
    github_owner,
    github_repo,
    github_owner || '/' || github_repo,
    COALESCE(default_branch, 'main')
FROM github_info_backup;

-- Step 5: Drop temporary table
DROP TABLE github_info_backup;

-- Step 6: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_github_info_server_id ON github_info(server_id);
CREATE INDEX IF NOT EXISTS idx_github_info_stars ON github_info(github_stars DESC);
CREATE INDEX IF NOT EXISTS idx_github_info_owner ON github_info(github_owner);
CREATE INDEX IF NOT EXISTS idx_github_info_repo ON github_info(github_repo);
CREATE INDEX IF NOT EXISTS idx_github_info_full_name ON github_info(github_full_name);
CREATE INDEX IF NOT EXISTS idx_github_info_last_commit ON github_info(github_last_commit DESC);
CREATE INDEX IF NOT EXISTS idx_github_info_language ON github_info(primary_language);
CREATE INDEX IF NOT EXISTS idx_github_info_health ON github_info(github_health_score DESC);
CREATE INDEX IF NOT EXISTS idx_github_info_trending ON github_info(stars_last_week DESC);
CREATE INDEX IF NOT EXISTS idx_github_info_created_at ON github_info(github_created_at);
CREATE INDEX IF NOT EXISTS idx_github_info_is_archived ON github_info(is_archived);

-- Migration complete
-- Next: Run with: sqlite3 data/mcp_servers.db < migrations/004_enhanced_github_info.sql
