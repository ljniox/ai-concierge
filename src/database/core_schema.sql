-- Core System Database Schema
-- Database: core_system.db
-- Version: 1.0.0
-- Purpose: System configuration and application registry (FR-033-040)

-- ==================================================
-- TABLE: applications
-- ==================================================
CREATE TABLE IF NOT EXISTS applications (
    app_id TEXT PRIMARY KEY NOT NULL,
    app_name TEXT UNIQUE NOT NULL,  -- Application name: catechese_app, temp_pages_system, etc.
    db_filename TEXT UNIQUE NOT NULL,  -- Database filename
    db_path TEXT UNIQUE NOT NULL,  -- Full path to database file
    version_schema TEXT NOT NULL,  -- Semantic versioning: "1.0.0"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    derniere_migration_at TIMESTAMP,  -- Last schema migration timestamp
    taille_bytes INTEGER,  -- Database file size (updated daily)
    derniere_sauvegarde_at TIMESTAMP,  -- Last backup timestamp (FR-038)
    statut TEXT DEFAULT 'active' NOT NULL,  -- active, maintenance, archived
    config TEXT,  -- JSON: application-specific configuration

    -- Constraints
    CHECK (statut IN ('active', 'maintenance', 'archived'))
);

-- ==================================================
-- INDEXES
-- ==================================================
CREATE INDEX IF NOT EXISTS idx_applications_name ON applications(app_name);
CREATE INDEX IF NOT EXISTS idx_applications_statut ON applications(statut);

-- ==================================================
-- INITIAL DATA
-- ==================================================
-- Insert initial application entries
INSERT OR IGNORE INTO applications (app_id, app_name, db_filename, db_path, version_schema, statut, config)
VALUES
    (
        'cat-001',
        'catechese_app',
        'sdb_cate.sqlite',
        '/home/ubuntu/ai-concierge/sdb_cate.sqlite',
        '1.0.0',
        'active',
        '{"description": "Core catechism data with enrollment management", "legacy_tables": true, "enrollment_system": true}'
    ),
    (
        'tmp-001',
        'temp_pages_system',
        'temp_pages_system.db',
        './data/temp_pages_system.db',
        '1.0.0',
        'active',
        '{"description": "Temporary secure pages for document collection", "expiration_days": 7}'
    ),
    (
        'core-001',
        'core_system',
        'core_system.db',
        './data/core_system.db',
        '1.0.0',
        'active',
        '{"description": "System configuration and application metadata"}'
    );

-- ==================================================
-- VERIFICATION
-- ==================================================
-- SELECT * FROM applications;
-- SELECT name FROM sqlite_master WHERE type='table' AND name='applications';
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_applications%';
