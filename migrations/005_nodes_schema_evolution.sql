-- ---------------------------------------------------------------------------
-- Nodes: drop node_type, add new columns
-- ---------------------------------------------------------------------------

-- Drop the check constraint before dropping the column (Postgres requires this)
ALTER TABLE nodes
    DROP COLUMN IF EXISTS node_type;

ALTER TABLE nodes
    ADD COLUMN IF NOT EXISTS prompt          TEXT,
    ADD COLUMN IF NOT EXISTS response_format JSONB,
    ADD COLUMN IF NOT EXISTS properties      JSONB NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS metadata        JSONB NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS "order"         INT,
    ADD COLUMN IF NOT EXISTS priority        INT  NOT NULL DEFAULT 0;

-- ---------------------------------------------------------------------------
-- Edges: add condition_prompt column
-- ---------------------------------------------------------------------------
ALTER TABLE edges
    ADD COLUMN IF NOT EXISTS condition_prompt TEXT;

-- ---------------------------------------------------------------------------
-- Properties: reusable schema fields for extraction nodes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS properties (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT        NOT NULL,
    type          TEXT        NOT NULL,
    description   TEXT,
    required      BOOLEAN     NOT NULL DEFAULT FALSE,
    default_value JSONB,
    schema        JSONB       NOT NULL DEFAULT '{}',
    metadata      JSONB       NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Conditions: detailed routing logic attached to edges
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conditions (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    edge_id        UUID        NOT NULL REFERENCES edges (id) ON DELETE CASCADE,
    operator       TEXT        NOT NULL,
    property_name  TEXT,
    compare_value  JSONB,
    prompt         TEXT,
    logic_operator TEXT        NOT NULL DEFAULT 'AND'
                               CHECK (logic_operator IN ('AND', 'OR')),
    metadata       JSONB       NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conditions_edge ON conditions (edge_id);
