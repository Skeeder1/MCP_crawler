-- ============================================================================
-- Migration 004: Add mcp_so_server_urls table
-- Purpose: Staging table for 2-phase extraction from mcp.so
-- Created: 2025-01-20
-- ============================================================================

-- ============================================================================
-- TABLE: mcp_so_server_urls
-- Description: Stores URLs collected from mcp.so pagination
-- Phase 1: Populate with URLs from mcp.so/servers?page=N
-- Phase 2: Extract GitHub links for each URL
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcp_so_server_urls (
  -- Primary identifier
  id TEXT PRIMARY KEY,

  -- URL information
  mcp_so_url TEXT UNIQUE NOT NULL,  -- Full URL: https://mcp.so/server/{name}/{owner}

  -- Metadata extracted from URL
  server_name TEXT NOT NULL,        -- Extracted from URL path
  owner_name TEXT,                  -- Extracted from URL path
  slug TEXT NOT NULL,               -- Generated slug (slugify(server_name))

  -- Phase 2 status tracking
  phase2_status TEXT DEFAULT 'pending' CHECK (phase2_status IN ('pending', 'processing', 'completed', 'failed')),
  phase2_attempts INTEGER DEFAULT 0,
  phase2_last_attempt DATETIME,
  phase2_error TEXT,

  -- GitHub information (populated in Phase 2)
  github_url TEXT,
  github_owner TEXT,
  github_repo TEXT,

  -- Collection metadata
  page_number INTEGER,              -- Page number where URL was found
  priority INTEGER DEFAULT 0,       -- Processing priority (higher = first)

  -- Timestamps
  discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- Constraints
  CHECK (phase2_attempts >= 0),
  CHECK (priority >= 0)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for finding pending URLs to process
CREATE INDEX IF NOT EXISTS idx_mcp_so_urls_status
  ON mcp_so_server_urls(phase2_status);

-- Index for priority processing
CREATE INDEX IF NOT EXISTS idx_mcp_so_urls_priority
  ON mcp_so_server_urls(priority DESC, discovered_at ASC);

-- Index for duplicate checking by slug
CREATE INDEX IF NOT EXISTS idx_mcp_so_urls_slug
  ON mcp_so_server_urls(slug);

-- Index for grouping by page number
CREATE INDEX IF NOT EXISTS idx_mcp_so_urls_page
  ON mcp_so_server_urls(page_number);

-- Index for finding URLs with GitHub info
CREATE INDEX IF NOT EXISTS idx_mcp_so_urls_github
  ON mcp_so_server_urls(github_url)
  WHERE github_url IS NOT NULL;

-- Index for failed URLs
CREATE INDEX IF NOT EXISTS idx_mcp_so_urls_failed
  ON mcp_so_server_urls(phase2_status, phase2_attempts)
  WHERE phase2_status = 'failed';

-- ============================================================================
-- TRIGGER: Update updated_at timestamp
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS trigger_mcp_so_urls_updated_at
AFTER UPDATE ON mcp_so_server_urls
FOR EACH ROW
BEGIN
  UPDATE mcp_so_server_urls
  SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

-- ============================================================================
-- END OF MIGRATION 004
-- ============================================================================
