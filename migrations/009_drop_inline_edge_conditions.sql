-- ---------------------------------------------------------------------------
-- Drop inline condition columns from edges.
-- These were replaced by the edge_conditions N:N junction table (migration 008)
-- and the dedicated conditions table.
-- ---------------------------------------------------------------------------
ALTER TABLE edges
    DROP COLUMN IF EXISTS condition,
    DROP COLUMN IF EXISTS condition_prompt;
