-- Migration 001: Create account tables for automatic account creation feature
-- This migration creates all tables for the automatic account creation feature
-- Database: Supabase PostgreSQL
-- Dependencies: None
-- Estimated time: 5 minutes
-- Rollback: Supported (tables will be dropped)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create user_roles table first (no dependencies)
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_system_role BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_name CHECK (name ~ '^[a-z_][a-z0-9_]*$')
);

-- Insert default system roles
INSERT INTO user_roles (name, display_name, description, permissions, is_system_role) VALUES
('parent', 'Parent', 'Parent with access to catechism information', '["view_children", "view_schedule", "send_messages"]', true),
('super_admin', 'Super Administrator', 'Full system administration access', '["*"]', true),
('catechist', 'Catechist', 'Catechism teacher role', '["view_students", "manage_classes", "view_schedule"]', true),
('staff', 'Staff Member', 'General staff access', '["view_basic_info", "send_messages"]', true);

-- Create user_accounts table (depends on no tables)
CREATE TABLE user_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    normalized_phone VARCHAR(20) NOT NULL UNIQUE,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_verified BOOLEAN NOT NULL DEFAULT false,
    parent_database_id VARCHAR(100), -- Reference to catechism database
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- GDPR fields
    consent_given BOOLEAN NOT NULL DEFAULT false,
    consent_level VARCHAR(20) NOT NULL DEFAULT 'minimal',
    data_retention_until TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_via VARCHAR(20) NOT NULL, -- 'whatsapp', 'telegram', 'manual'
    platform_user_id VARCHAR(100), -- Platform-specific user ID
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'suspended', 'deleted')),
    CONSTRAINT valid_consent_level CHECK (consent_level IN ('minimal', 'standard', 'full')),
    CONSTRAINT valid_created_via CHECK (created_via IN ('whatsapp', 'telegram', 'manual'))
);

-- Create indexes for user_accounts
CREATE INDEX idx_user_accounts_phone ON user_accounts(phone_number);
CREATE INDEX idx_user_accounts_normalized_phone ON user_accounts(normalized_phone);
CREATE INDEX idx_user_accounts_status ON user_accounts(status);
CREATE INDEX idx_user_accounts_created_at ON user_accounts(created_at);
CREATE INDEX idx_user_accounts_platform ON user_accounts(created_via, platform_user_id);

-- Create user_sessions table (depends on user_accounts)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_accounts(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    platform VARCHAR(20) NOT NULL,
    platform_user_id VARCHAR(100) NOT NULL,
    session_type VARCHAR(20) NOT NULL DEFAULT 'account_creation',
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Session data
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    conversation_state JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Security
    ip_address INET,
    user_agent TEXT,
    trust_score DECIMAL(3,2) DEFAULT 0.80,

    -- Metadata
    message_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_platform CHECK (platform IN ('whatsapp', 'telegram')),
    CONSTRAINT valid_session_type CHECK (session_type IN ('account_creation', 'general', 'admin')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'expired', 'terminated')),
    CONSTRAINT valid_trust_score CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
    CONSTRAINT valid_expires_at CHECK (expires_at IS NULL OR expires_at > created_at)
);

-- Create indexes for user_sessions
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_platform ON user_sessions(platform, platform_user_id);
CREATE INDEX idx_user_sessions_status ON user_sessions(status);
CREATE INDEX idx_user_sessions_last_activity ON user_sessions(last_activity_at);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Create user_role_assignments table (depends on user_accounts and user_roles)
CREATE TABLE user_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_accounts(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES user_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES user_accounts(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE(user_id, role_id),
    CONSTRAINT valid_assignment CHECK (expires_at IS NULL OR expires_at > assigned_at)
);

-- Create indexes for user_role_assignments
CREATE INDEX idx_user_role_assignments_user_id ON user_role_assignments(user_id);
CREATE INDEX idx_user_role_assignments_role_id ON user_role_assignments(role_id);
CREATE INDEX idx_user_role_assignments_active ON user_role_assignments(is_active, expires_at);

-- Create account_creation_audit table (depends on user_accounts and user_sessions)
CREATE TABLE account_creation_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_accounts(id) ON DELETE SET NULL,
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,

    -- Request details
    phone_number VARCHAR(20) NOT NULL,
    normalized_phone VARCHAR(20) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    platform_user_id VARCHAR(100) NOT NULL,

    -- Processing details
    status VARCHAR(20) NOT NULL,
    result_code VARCHAR(50),
    result_message TEXT,
    processing_time_ms INTEGER,

    -- Data validation
    phone_validation_result JSONB,
    parent_lookup_result JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Security
    ip_address INET,
    user_agent TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_platform CHECK (platform IN ('whatsapp', 'telegram')),
    CONSTRAINT valid_status CHECK (status IN ('initiated', 'phone_validated', 'parent_found', 'account_created', 'failed', 'duplicate')),
    CONSTRAINT valid_processing_time CHECK (processing_time_ms >= 0),
    CONSTRAINT valid_completion CHECK (completed_at IS NULL OR completed_at >= created_at)
);

-- Create indexes for account_creation_audit
CREATE INDEX idx_account_creation_audit_user_id ON account_creation_audit(user_id);
CREATE INDEX idx_account_creation_audit_phone ON account_creation_audit(normalized_phone);
CREATE INDEX idx_account_creation_audit_platform ON account_creation_audit(platform, created_at);
CREATE INDEX idx_account_creation_audit_status ON account_creation_audit(status);
CREATE INDEX idx_account_creation_audit_created_at ON account_creation_audit(created_at);

-- Create webhook_events table (depends on user_accounts and user_sessions)
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_id VARCHAR(255), -- Platform-specific event ID

    -- Request details
    webhook_url TEXT NOT NULL,
    request_method VARCHAR(10) NOT NULL,
    request_headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    request_body_size INTEGER,
    request_body_hash VARCHAR(64), -- SHA-256 hash for integrity

    -- Security (from research: signature verification)
    signature_verified BOOLEAN NOT NULL DEFAULT false,
    signature_details JSONB,
    ip_address INET,

    -- Processing
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    processing_time_ms INTEGER,

    -- Relations
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES user_accounts(id) ON DELETE SET NULL,

    -- Timestamps
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_platform CHECK (platform IN ('whatsapp', 'telegram')),
    CONSTRAINT valid_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'ignored')),
    CONSTRAINT valid_processing_time CHECK (processing_time_ms >= 0)
);

-- Create indexes for webhook_events
CREATE INDEX idx_webhook_events_platform ON webhook_events(platform, received_at);
CREATE INDEX idx_webhook_events_status ON webhook_events(processing_status);
CREATE INDEX idx_webhook_events_signature ON webhook_events(signature_verified, received_at);
CREATE INDEX idx_webhook_events_session_id ON webhook_events(session_id);

-- Create Row Level Security policies
ALTER TABLE user_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_creation_audit ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (will be enhanced during implementation)
CREATE POLICY "Users can view own accounts" ON user_accounts
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own audit records" ON account_creation_audit
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_user_accounts_updated_at
    BEFORE UPDATE ON user_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_roles_updated_at
    BEFORE UPDATE ON user_roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger for account creation
CREATE OR REPLACE FUNCTION log_account_creation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO account_creation_audit (
        user_id,
        phone_number,
        normalized_phone,
        platform,
        platform_user_id,
        status,
        result_code,
        result_message,
        created_at
    ) VALUES (
        NEW.id,
        NEW.phone_number,
        NEW.normalized_phone,
        NEW.created_via,
        NEW.platform_user_id,
        'account_created',
        'SUCCESS',
        'Account created successfully via ' || NEW.created_via,
        NOW()
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for account creation audit
CREATE TRIGGER account_creation_audit_trigger
    AFTER INSERT ON user_accounts
    FOR EACH ROW EXECUTE FUNCTION log_account_creation();

-- Create view for active users with roles
CREATE VIEW active_users_with_roles AS
SELECT
    ua.id,
    ua.phone_number,
    ua.normalized_phone,
    ua.username,
    ua.first_name,
    ua.last_name,
    ua.email,
    ua.status,
    ua.created_via,
    ua.created_at,
    ua.last_login_at,
    COALESCE(
        json_agg(
            json_build_object(
                'id', ur.id,
                'name', ur.name,
                'display_name', ur.display_name,
                'permissions', ur.permissions
            )
        ) FILTER (WHERE ur.id IS NOT NULL),
        '[]'::json
    ) as roles
FROM user_accounts ua
LEFT JOIN user_role_assignments ura ON ua.id = ura.user_id AND ura.is_active = true
LEFT JOIN user_roles ur ON ura.role_id = ur.id AND ur.is_active = true
WHERE ua.status = 'active'
GROUP BY ua.id, ua.phone_number, ua.normalized_phone, ua.username, ua.first_name, ua.last_name, ua.email, ua.status, ua.created_via, ua.created_at, ua.last_login_at;

-- Create view for session statistics
CREATE VIEW session_statistics AS
SELECT
    platform,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
    COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as non_expired_sessions,
    AVG(message_count) as avg_message_count,
    MAX(last_activity_at) as last_activity
FROM user_sessions
GROUP BY platform;

-- Migration completion marker
INSERT INTO user_roles (name, display_name, description, permissions, is_system_role) VALUES
('migration_marker', 'Migration Marker', 'Indicates migration 001 completion', '[]', true)
ON CONFLICT (name) DO NOTHING;

COMMENT ON TABLE user_accounts IS 'Stores user account information for automatic account creation feature';
COMMENT ON TABLE user_roles IS 'Defines system roles that can be assigned to users';
COMMENT ON TABLE user_role_assignments IS 'Links users to roles with assignment metadata';
COMMENT ON TABLE user_sessions IS 'Manages user sessions across different platforms with dual persistence';
COMMENT ON TABLE account_creation_audit IS 'Audit trail for all account creation activities';
COMMENT ON TABLE webhook_events IS 'Log of incoming webhook events for security and debugging';
COMMENT ON VIEW active_users_with_roles IS 'View of active users with their assigned roles';
COMMENT ON VIEW session_statistics IS 'Statistics about user sessions by platform';