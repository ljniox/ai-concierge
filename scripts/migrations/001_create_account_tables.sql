-- Migration: Create Account Creation System Tables
-- Description: Creates tables for automatic account creation based on phone numbers
-- Version: 001
-- Date: 2025-10-11

-- Enable foreign key support and WAL mode
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Create user_accounts table
CREATE TABLE IF NOT EXISTS user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NULL,  -- Foreign key to existing parent records
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    phone_country_code VARCHAR(5) NOT NULL DEFAULT '+221',
    phone_national_number VARCHAR(15) NOT NULL,
    phone_is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    email VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    account_source VARCHAR(20) NOT NULL DEFAULT 'automatic',  -- 'automatic', 'manual', 'admin'
    created_via VARCHAR(10) NOT NULL,  -- 'telegram', 'whatsapp', 'admin'
    telegram_user_id BIGINT NULL,
    whatsapp_user_id VARCHAR(50) NULL,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    consent_date TIMESTAMP NULL,
    data_retention_days INTEGER NOT NULL DEFAULT 365,
    notes TEXT NULL,

    FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE SET NULL
);

-- Create indexes for user_accounts
CREATE INDEX IF NOT EXISTS idx_user_accounts_phone_number ON user_accounts(phone_number);
CREATE INDEX IF NOT EXISTS idx_user_accounts_parent_id ON user_accounts(parent_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_telegram_user_id ON user_accounts(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_whatsapp_user_id ON user_accounts(whatsapp_user_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_created_at ON user_accounts(created_at);
CREATE INDEX IF NOT EXISTS idx_user_accounts_is_active ON user_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_user_accounts_phone_lookup ON user_accounts(phone_number, is_active);

-- Create user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_display_name VARCHAR(100) NOT NULL,
    role_description TEXT,
    is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user_roles
CREATE INDEX IF NOT EXISTS idx_user_roles_name ON user_roles(role_name);
CREATE INDEX IF NOT EXISTS idx_user_roles_active ON user_roles(is_active);

-- Insert default role data
INSERT OR IGNORE INTO user_roles (role_name, role_display_name, role_description, is_system_role) VALUES
('parent', 'Parent', 'Parent of catechism student with access to parent-specific functions', TRUE),
('super_admin', 'Super Administrateur', 'System administrator with full access to all functions', TRUE),
('catechist', 'Catéchiste', 'Catechism teacher with access to class management', TRUE),
('treasurer', 'Trésorier', 'Treasury staff with access to payment management', TRUE),
('secretary', 'Secrétaire', 'Administrative staff with access to enrollment management', TRUE);

-- Create user_role_assignments table
CREATE TABLE IF NOT EXISTS user_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_by INTEGER NULL,  -- User ID who assigned this role
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,  -- For temporary role assignments
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    assignment_notes TEXT NULL,

    FOREIGN KEY (user_id) REFERENCES user_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES user_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES user_accounts(id) ON DELETE SET NULL,

    UNIQUE(user_id, role_id)  -- Prevent duplicate role assignments
);

-- Create indexes for user_role_assignments
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_user_id ON user_role_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_role_id ON user_role_assignments(role_id);
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_active ON user_role_assignments(is_active);

-- Create account_creation_audit table
CREATE TABLE IF NOT EXISTS account_creation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NULL,  -- NULL if creation failed
    phone_number VARCHAR(20) NOT NULL,
    phone_validation_result VARCHAR(20) NOT NULL,  -- 'valid', 'invalid', 'not_found'
    parent_match_found BOOLEAN NOT NULL,
    parent_id INTEGER NULL,
    creation_status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'skipped'
    creation_source VARCHAR(10) NOT NULL,  -- 'telegram', 'whatsapp'
    webhook_data TEXT NULL,  -- JSON of incoming webhook data
    error_message TEXT NULL,
    processing_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES user_accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE SET NULL
);

-- Create indexes for account_creation_audit
CREATE INDEX IF NOT EXISTS idx_account_creation_audit_phone ON account_creation_audit(phone_number);
CREATE INDEX IF NOT EXISTS idx_account_creation_audit_status ON account_creation_audit(creation_status);
CREATE INDEX IF NOT EXISTS idx_account_creation_audit_created_at ON account_creation_audit(created_at);
CREATE INDEX IF NOT EXISTS idx_account_creation_audit_source ON account_creation_audit(creation_source);
CREATE INDEX IF NOT EXISTS idx_account_creation_audit_user_id ON account_creation_audit(user_id);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(100) NOT NULL UNIQUE,
    platform VARCHAR(10) NOT NULL,  -- 'telegram', 'whatsapp'
    platform_user_id VARCHAR(50) NOT NULL,
    session_data TEXT NULL,  -- JSON of session state
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES user_accounts(id) ON DELETE CASCADE
);

-- Create indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_platform ON user_sessions(platform);
CREATE INDEX IF NOT EXISTS idx_user_sessions_platform_user_id ON user_sessions(platform_user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_lookup ON user_sessions(platform, platform_user_id, is_active);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_user_accounts_timestamp
    BEFORE UPDATE ON user_accounts
    FOR EACH ROW
BEGIN
    UPDATE user_accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_roles_timestamp
    BEFORE UPDATE ON user_roles
    FOR EACH ROW
BEGIN
    UPDATE user_roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_sessions_timestamp
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW
BEGIN
    UPDATE user_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Create view for active users with roles
CREATE VIEW IF NOT EXISTS active_users_with_roles AS
SELECT
    ua.id,
    ua.phone_number,
    ua.full_name,
    ua.username,
    ua.email,
    ua.is_active,
    ua.created_at,
    ua.last_login_at,
    ua.account_source,
    ua.created_via,
    GROUP_CONCAT(ur.role_name) as roles
FROM user_accounts ua
LEFT JOIN user_role_assignments ura ON ua.id = ura.user_id
LEFT JOIN user_roles ur ON ura.role_id = ur.id
WHERE ua.is_active = 1
  AND ura.is_active = 1
  AND ur.is_active = 1
GROUP BY ua.id;

-- Create view for account creation statistics
CREATE VIEW IF NOT EXISTS account_creation_stats AS
SELECT
    DATE(created_at) as creation_date,
    creation_source,
    creation_status,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN creation_status = 'success' THEN 1 END) as successful_creations,
    COUNT(CASE WHEN creation_status = 'failed' THEN 1 END) as failed_creations,
    AVG(processing_time_ms) as avg_processing_time_ms
FROM account_creation_audit
GROUP BY DATE(created_at), creation_source, creation_status
ORDER BY creation_date DESC;

-- Migration completed successfully
-- Tables created: user_accounts, user_roles, user_role_assignments, account_creation_audit, user_sessions
-- Indexes created for optimal performance
-- Default roles inserted
-- Triggers created for timestamp updates
-- Views created for common queries