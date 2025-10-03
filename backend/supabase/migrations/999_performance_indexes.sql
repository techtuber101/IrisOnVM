-- Performance optimization indexes for faster queries
-- Run this migration to add database indexes that speed up common queries

BEGIN;

-- Index for message fetching (most common query)
-- Covers: thread_id, is_llm_message, created_at ordering
CREATE INDEX IF NOT EXISTS idx_messages_thread_llm_created 
ON messages(thread_id, is_llm_message, created_at ASC)
WHERE is_llm_message = true;

-- Index for agent runs by thread and status
CREATE INDEX IF NOT EXISTS idx_agent_runs_thread_status_started 
ON agent_runs(thread_id, status, started_at DESC);

-- Index for threads by account with created_at for sorting
CREATE INDEX IF NOT EXISTS idx_threads_account_created 
ON threads(account_id, created_at DESC);

-- Index for agent_versions by agent_id and version lookups
CREATE INDEX IF NOT EXISTS idx_agent_versions_agent_id 
ON agent_versions(agent_id, created_at DESC);

-- Index for knowledge_base_items by agent_id (for RPC function)
CREATE INDEX IF NOT EXISTS idx_knowledge_base_items_agent_id 
ON knowledge_base_items(agent_id)
WHERE deleted_at IS NULL;

-- Composite index for projects by account
CREATE INDEX IF NOT EXISTS idx_projects_account_id 
ON projects(account_id, created_at DESC);

COMMIT;

-- Analyze tables to update query planner statistics
ANALYZE messages;
ANALYZE agent_runs;
ANALYZE threads;
ANALYZE projects;
ANALYZE agent_versions;
ANALYZE knowledge_base_items;

