-- Remove workflow_id from conditions and properties.
-- Workflow membership is derived indirectly:
--   conditions → edge_conditions → edges → nodes.workflow_id
--   properties → node_properties  → nodes.workflow_id
ALTER TABLE conditions DROP COLUMN IF EXISTS workflow_id;
ALTER TABLE properties DROP COLUMN IF EXISTS workflow_id;
