-- Temporary Pages System Database Schema
-- Database: temp_pages_system.db
-- Version: 1.0.0
-- Purpose: Temporary secure URLs for document collection (FR-041-045)

-- ==================================================
-- TABLE: pages_temporaires
-- ==================================================
CREATE TABLE IF NOT EXISTS pages_temporaires (
    page_id TEXT PRIMARY KEY NOT NULL,
    code_acces TEXT UNIQUE NOT NULL,  -- 8-char alphanumeric (excluding 0, O, 1, I, L)
    url_complete TEXT UNIQUE NOT NULL,  -- Full URL with code
    utilisateur_associe_id TEXT NOT NULL,  -- Parent user_id (cross-db reference to profil_utilisateurs)
    createur_id TEXT NOT NULL,  -- Staff user_id who created the page
    objet TEXT NOT NULL,  -- inscription, documents_complementaires, autre
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,  -- Default: created_at + 7 days (FR-043)
    premiere_utilisation_at TIMESTAMP,  -- First access timestamp
    statut TEXT DEFAULT 'active' NOT NULL,  -- active, utilisee, expiree, revoquee
    documents_collectes TEXT,  -- JSON array of document IDs (cross-db reference to documents)

    -- Constraints
    CHECK (objet IN ('inscription', 'documents_complementaires', 'autre')),
    CHECK (statut IN ('active', 'utilisee', 'expiree', 'revoquee')),
    CHECK (length(code_acces) = 8)
);

-- ==================================================
-- INDEXES
-- ==================================================
CREATE INDEX IF NOT EXISTS idx_pages_code ON pages_temporaires(code_acces);
CREATE INDEX IF NOT EXISTS idx_pages_utilisateur ON pages_temporaires(utilisateur_associe_id);
CREATE INDEX IF NOT EXISTS idx_pages_statut ON pages_temporaires(statut, expires_at);
CREATE INDEX IF NOT EXISTS idx_pages_createur ON pages_temporaires(createur_id);

-- ==================================================
-- VERIFICATION
-- ==================================================
-- SELECT name FROM sqlite_master WHERE type='table' AND name='pages_temporaires';
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_pages%';
