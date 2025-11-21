-- Migration 003: Add tool_parameters table
-- Description: Store detailed parameter information for each tool
-- Date: 2025-01-20

-- Create tool_parameters table
CREATE TABLE IF NOT EXISTS tool_parameters (
    id TEXT PRIMARY KEY NOT NULL,
    tool_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT,                        -- string, integer, boolean, array, object, number, null
    description TEXT,
    required BOOLEAN NOT NULL DEFAULT 0,  -- 1=required, 0=optional
    default_value TEXT,               -- Stored as JSON string
    example_value TEXT,               -- Stored as JSON string
    display_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE,
    UNIQUE(tool_id, name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tool_params_tool_id ON tool_parameters(tool_id);
CREATE INDEX IF NOT EXISTS idx_tool_params_required ON tool_parameters(required);
CREATE INDEX IF NOT EXISTS idx_tool_params_type ON tool_parameters(type);

-- Add params_count column to tools table
ALTER TABLE tools ADD COLUMN params_count INTEGER DEFAULT 0;

-- Create trigger to auto-update params_count on INSERT
CREATE TRIGGER IF NOT EXISTS trigger_params_count_insert
AFTER INSERT ON tool_parameters
BEGIN
    UPDATE tools
    SET params_count = (
        SELECT COUNT(*) FROM tool_parameters WHERE tool_id = NEW.tool_id
    )
    WHERE id = NEW.tool_id;
END;

-- Create trigger to auto-update params_count on DELETE
CREATE TRIGGER IF NOT EXISTS trigger_params_count_delete
AFTER DELETE ON tool_parameters
BEGIN
    UPDATE tools
    SET params_count = (
        SELECT COUNT(*) FROM tool_parameters WHERE tool_id = OLD.tool_id
    )
    WHERE id = OLD.tool_id;
END;

-- Migration complete
-- Next: Run with: sqlite3 data/mcp_servers.db < migrations/003_add_tool_parameters.sql
