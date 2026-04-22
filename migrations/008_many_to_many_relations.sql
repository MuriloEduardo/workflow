-- ---------------------------------------------------------------------------
-- Edge ↔ Condition: N:N junction
-- A condition can belong to many edges; an edge can have many conditions.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS edge_conditions (
    edge_id      UUID NOT NULL REFERENCES edges (id) ON DELETE CASCADE,
    condition_id UUID NOT NULL REFERENCES conditions (id) ON DELETE CASCADE,
    PRIMARY KEY (edge_id, condition_id)
);

CREATE INDEX IF NOT EXISTS idx_edge_conditions_edge      ON edge_conditions (edge_id);
CREATE INDEX IF NOT EXISTS idx_edge_conditions_condition ON edge_conditions (condition_id);

-- Migrate existing 1:N data into the junction table.
INSERT INTO edge_conditions (edge_id, condition_id)
SELECT edge_id, id
FROM conditions
WHERE edge_id IS NOT NULL
ON CONFLICT DO NOTHING;

-- Drop the old FK column now that the junction is populated.
ALTER TABLE conditions DROP COLUMN IF EXISTS edge_id;

-- ---------------------------------------------------------------------------
-- Condition ↔ Property: N:N junction
-- A condition can reference many properties; a property can be used in many
-- conditions.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS condition_properties (
    condition_id UUID NOT NULL REFERENCES conditions (id) ON DELETE CASCADE,
    property_id  UUID NOT NULL REFERENCES properties (id) ON DELETE CASCADE,
    PRIMARY KEY (condition_id, property_id)
);

CREATE INDEX IF NOT EXISTS idx_condition_properties_condition ON condition_properties (condition_id);
CREATE INDEX IF NOT EXISTS idx_condition_properties_property  ON condition_properties (property_id);

-- Drop the old text column (replaced by the FK-backed junction).
ALTER TABLE conditions DROP COLUMN IF EXISTS property_name;

-- ---------------------------------------------------------------------------
-- Node ↔ Property: N:N junction
-- A property can be used in many nodes; a node can have many properties.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_properties (
    node_id     UUID NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties (id) ON DELETE CASCADE,
    PRIMARY KEY (node_id, property_id)
);

CREATE INDEX IF NOT EXISTS idx_node_properties_node     ON node_properties (node_id);
CREATE INDEX IF NOT EXISTS idx_node_properties_property ON node_properties (property_id);

-- Drop the old JSONB column (replaced by the FK-backed junction).
ALTER TABLE nodes DROP COLUMN IF EXISTS properties;
