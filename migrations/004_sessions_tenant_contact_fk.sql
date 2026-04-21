-- ---------------------------------------------------------------------------
-- Alter sessions table:
--   1. Rename sender_id → contact_id (will become UUID FK)
--   2. Change tenant_id TEXT → UUID FK tenants
--   3. Add new contact_id UUID FK tenant_contacts
--
-- Strategy: add new UUID columns, drop old TEXT ones.
-- Existing rows (if any) are left with NULLs — acceptable for dev.
-- ---------------------------------------------------------------------------

-- Drop old unique index (references old column names)
DROP INDEX IF EXISTS uix_sessions_active;

-- Add new UUID FK columns
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS tenant_ref  UUID REFERENCES tenants (id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS contact_ref UUID REFERENCES tenant_contacts (id) ON DELETE SET NULL;

-- Drop old text columns
ALTER TABLE sessions
    DROP COLUMN IF EXISTS tenant_id,
    DROP COLUMN IF EXISTS sender_id;

-- Rename new columns to final names
ALTER TABLE sessions RENAME COLUMN tenant_ref  TO tenant_id;
ALTER TABLE sessions RENAME COLUMN contact_ref TO contact_id;

-- Recreate unique index: one active session per tenant+channel+contact
CREATE UNIQUE INDEX IF NOT EXISTS uix_sessions_active
    ON sessions (tenant_id, channel_type, contact_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_sessions_tenant  ON sessions (tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_contact ON sessions (contact_id);
