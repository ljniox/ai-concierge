-- Payment System Database Migration
-- Creates tables for mobile money payment processing and validation
-- Gust-IA - Service Diocésain de la Catéchèse

-- Payment records table
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    payment_reference TEXT NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL DEFAULT 5000.00,
    currency TEXT NOT NULL DEFAULT 'XOF',
    status TEXT NOT NULL DEFAULT 'en_attente',
    validation_data TEXT,  -- JSON data from OCR processing
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,

    FOREIGN KEY (enrollment_id) REFERENCES inscriptions(inscription_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES profil_utilisateurs(user_id) ON DELETE CASCADE
);

-- Payment validation workflow table
CREATE TABLE IF NOT EXISTS payment_validations (
    validation_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'en_attente_revision',
    assigned_to TEXT,
    assigned_at DATETIME,
    assigned_by TEXT,
    reviewed_by TEXT,
    reviewed_at DATETIME,
    validation_notes TEXT,
    rejection_reason TEXT,
    receipt_ocr_result TEXT,  -- JSON result from OCR processing
    receipt_processed_at DATETIME,
    escalation_level INTEGER DEFAULT 0,
    escalation_reason TEXT,
    escalated_by TEXT,
    escalated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES profil_utilisateurs(user_id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_by) REFERENCES profil_utilisateurs(user_id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES profil_utilisateurs(user_id) ON DELETE SET NULL,
    FOREIGN KEY (escalated_by) REFERENCES profil_utilisateurs(user_id) ON DELETE SET NULL
);

-- Payment status tracking table
CREATE TABLE IF NOT EXISTS payment_status_tracking (
    tracking_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT,
    notes TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES profil_utilisateurs(user_id) ON DELETE SET NULL
);

-- Payment notifications table
CREATE TABLE IF NOT EXISTS payment_notifications (
    notification_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    payment_id TEXT,
    notification_type TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES profil_utilisateurs(user_id) ON DELETE CASCADE,
    FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_payments_enrollment_id ON payments(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_provider ON payments(provider);
CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(payment_reference);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_payments_expires_at ON payments(expires_at);

CREATE INDEX IF NOT EXISTS idx_payment_validations_payment_id ON payment_validations(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_validations_assigned_to ON payment_validations(assigned_to);
CREATE INDEX IF NOT EXISTS idx_payment_validations_status ON payment_validations(status);
CREATE INDEX IF NOT EXISTS idx_payment_validations_created_at ON payment_validations(created_at);

CREATE INDEX IF NOT EXISTS idx_payment_status_tracking_payment_id ON payment_status_tracking(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_status_tracking_changed_at ON payment_status_tracking(changed_at);
CREATE INDEX IF NOT EXISTS idx_payment_status_tracking_changed_by ON payment_status_tracking(changed_by);

CREATE INDEX IF NOT EXISTS idx_payment_notifications_user_id ON payment_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_notifications_payment_id ON payment_notifications(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_notifications_type ON payment_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_payment_notifications_is_read ON payment_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_payment_notifications_created_at ON payment_notifications(created_at);

-- Create basic inscriptions table if it doesn't exist
CREATE TABLE IF NOT EXISTS inscriptions (
    inscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    nom_enfant TEXT,
    prenom_enfant TEXT,
    classe_inscription TEXT,
    statut_paiement TEXT DEFAULT 'impaye',
    date_paiement DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create basic profil_utilisateurs table if it doesn't exist
CREATE TABLE IF NOT EXISTS profil_utilisateurs (
    user_id TEXT PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    telephone TEXT,
    email TEXT,
    role TEXT DEFAULT 'parent',
    canal_prefere TEXT DEFAULT 'whatsapp',
    identifiant_canal TEXT,
    statut_compte TEXT DEFAULT 'actif',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to automatically update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_payments_timestamp
    AFTER UPDATE ON payments
BEGIN
    UPDATE payments SET updated_at = CURRENT_TIMESTAMP WHERE payment_id = NEW.payment_id;
END;

CREATE TRIGGER IF NOT EXISTS update_payment_validations_timestamp
    AFTER UPDATE ON payment_validations
BEGIN
    UPDATE payment_validations SET updated_at = CURRENT_TIMESTAMP WHERE validation_id = NEW.validation_id;
END;

-- Create system_config table
CREATE TABLE IF NOT EXISTS system_config (
    config_key TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to update system_config timestamp
CREATE TRIGGER IF NOT EXISTS update_system_config_timestamp
    AFTER UPDATE ON system_config
BEGIN
    UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE config_key = NEW.config_key;
END;

-- Insert initial configuration data
INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES
('enrollment_fee', '5000.00', 'Fixed enrollment fee in XOF'),
('payment_timeout_hours', '24', 'Hours before payment expires'),
('ocr_confidence_threshold', '0.75', 'Minimum confidence for payment receipt OCR'),
('treasurer_review_timeout_hours', '48', 'Hours for treasurer to review payments'),
('payment_reminder_intervals', '[6, 24, 48, 72]', 'Hours after payment to send reminders');

-- Create view for payment statistics
CREATE VIEW IF NOT EXISTS payment_stats_view AS
SELECT
    DATE(created_at) as payment_date,
    provider,
    status,
    COUNT(*) as payment_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM payments
GROUP BY DATE(created_at), provider, status
ORDER BY payment_date DESC;

-- Create view for pending validations
CREATE VIEW IF NOT EXISTS pending_validations_view AS
SELECT
    pv.validation_id,
    p.payment_id,
    p.payment_reference,
    p.amount,
    p.provider,
    p.created_at as payment_date,
    pv.assigned_to,
    pv.assigned_at,
    u.nom as treasurer_name,
    u.prenom as treasurer_prenom,
    e.nom_enfant,
    e.prenom_enfant
FROM payment_validations pv
JOIN payments p ON pv.payment_id = p.payment_id
LEFT JOIN profil_utilisateurs u ON pv.assigned_to = u.user_id
LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
WHERE pv.status = 'en_attente_revision'
ORDER BY p.created_at ASC;