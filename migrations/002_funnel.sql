-- ---------------------------------------------------------------------------
-- Nodes: steps of a funnel/workflow definition
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nodes (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    description TEXT,
    node_type   TEXT        NOT NULL DEFAULT 'step'
                            CHECK (node_type IN ('start', 'step', 'condition', 'end')),
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive')),
    config      JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Edges: directed transitions between nodes (source → target)
--
-- Cardinality:
--   node  1 ── N  edge  (as source_node_id)
--   node  1 ── N  edge  (as target_node_id)
--   edge  N ── 1  node  (source_node_id)
--   edge  N ── 1  node  (target_node_id)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS edges (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID        NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    target_node_id UUID        NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    label          TEXT,
    condition      JSONB,
    priority       INT         NOT NULL DEFAULT 0,
    metadata       JSONB       NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_node_id);

-- ---------------------------------------------------------------------------
-- Executions: cognition call results produced during a node activation
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS executions (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id       UUID        NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    request_id    TEXT        NOT NULL,
    session_id    TEXT,
    status        TEXT        NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending', 'completed', 'failed')),

    -- Cognition I/O
    prompt        TEXT,
    response      TEXT,
    model         TEXT,

    -- Observability
    input_tokens  INT,
    output_tokens INT,
    total_tokens  INT,
    latency_ms    INT,

    error         TEXT,
    metadata      JSONB       NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_executions_node       ON executions (node_id);
CREATE INDEX IF NOT EXISTS idx_executions_request    ON executions (request_id);
CREATE INDEX IF NOT EXISTS idx_executions_session    ON executions (session_id);
