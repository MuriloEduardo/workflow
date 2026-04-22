-- ---------------------------------------------------------------------------
-- Workflows: a named workflow definition belonging to a tenant.
-- A tenant can have many workflows; a workflow belongs to exactly one tenant.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workflows (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID        NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    name        TEXT        NOT NULL,
    description TEXT,
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'archived')),
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workflows_tenant ON workflows (tenant_id);

-- ---------------------------------------------------------------------------
-- Add workflow_id to nodes, edges, properties and conditions.
-- Nullable so existing rows are preserved; scoped resources should be set.
-- ---------------------------------------------------------------------------
ALTER TABLE nodes
    ADD COLUMN IF NOT EXISTS workflow_id UUID REFERENCES workflows (id) ON DELETE SET NULL;

ALTER TABLE edges
    ADD COLUMN IF NOT EXISTS workflow_id UUID REFERENCES workflows (id) ON DELETE SET NULL;

ALTER TABLE properties
    ADD COLUMN IF NOT EXISTS workflow_id UUID REFERENCES workflows (id) ON DELETE SET NULL;

ALTER TABLE conditions
    ADD COLUMN IF NOT EXISTS workflow_id UUID REFERENCES workflows (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_nodes_workflow       ON nodes       (workflow_id);
CREATE INDEX IF NOT EXISTS idx_edges_workflow       ON edges       (workflow_id);
CREATE INDEX IF NOT EXISTS idx_properties_workflow  ON properties  (workflow_id);
CREATE INDEX IF NOT EXISTS idx_conditions_workflow  ON conditions  (workflow_id);
