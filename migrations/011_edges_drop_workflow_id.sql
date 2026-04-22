-- Remove workflow_id from edges.
-- Workflow membership is derived indirectly via source_node_id → nodes.workflow_id.
ALTER TABLE edges DROP COLUMN IF EXISTS workflow_id;
