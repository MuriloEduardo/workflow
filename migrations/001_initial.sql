CREATE TABLE IF NOT EXISTS pending_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_key   TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       TEXT NOT NULL,
    channel_type    TEXT NOT NULL,
    sender_id       TEXT NOT NULL,
    thread_id       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    timeout_seconds INT  NOT NULL DEFAULT 1800,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_sessions_active
    ON sessions (tenant_id, channel_type, sender_id)
    WHERE status = 'active';
