-- ---------------------------------------------------------------------------
-- Tenants
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    slug        TEXT        NOT NULL UNIQUE,
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'suspended')),
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Tenant Contacts: one contact per channel identity (sender_id + channel_type)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_contacts (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    UUID        NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    channel_type TEXT        NOT NULL,
    sender_id    TEXT        NOT NULL,
    name         TEXT,
    metadata     JSONB       NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (tenant_id, channel_type, sender_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_contacts_tenant ON tenant_contacts (tenant_id);

-- ---------------------------------------------------------------------------
-- Alter executions:
--   - node_id becomes nullable (we may not know the node yet)
--   - add tenant_id and contact_id (nullable, populated when known)
-- ---------------------------------------------------------------------------
ALTER TABLE executions
    ALTER COLUMN node_id DROP NOT NULL;

ALTER TABLE executions
    ADD COLUMN IF NOT EXISTS tenant_id  UUID REFERENCES tenants (id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS contact_id UUID REFERENCES tenant_contacts (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_executions_tenant  ON executions (tenant_id);
CREATE INDEX IF NOT EXISTS idx_executions_contact ON executions (contact_id);
