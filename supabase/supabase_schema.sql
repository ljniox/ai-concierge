-- SDB (Service Diocésain de la Catéchèse) - Supabase Schema
-- Migration from Baserow to Supabase

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types for consistent data
CREATE TYPE yes_no_enum AS ENUM ('oui', 'non');
CREATE TYPE action_type AS ENUM ('Nouvelle Inscription', 'Réinscription', 'Transfert à partir d''une autre paroisse');
CREATE TYPE moyen_paiement_type AS ENUM ('CASH', 'WAVE', 'OM', 'CB');
CREATE TYPE etat_inscription AS ENUM ('Inscription Validée', 'En attente', 'Annulée');

-- Function to generate UUID
CREATE OR REPLACE FUNCTION generate_uuid() 
RETURNS UUID AS $$
BEGIN
    RETURN uuid_generate_v4();
END;
$$ LANGUAGE plpgsql;

-- 1. CATECHUMENES table
CREATE TABLE catechumenes (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    id_catechumene TEXT UNIQUE NOT NULL,
    prenoms TEXT NOT NULL,
    nom TEXT NOT NULL,
    baptise yes_no_enum DEFAULT 'non',
    extrait_bapteme_fourni yes_no_enum DEFAULT 'non',
    lieu_bapteme TEXT,
    commentaire TEXT,
    annee_naissance TEXT,
    attestation_transfert_fournie yes_no_enum DEFAULT 'non',
    operateur TEXT,
    code_parent TEXT,
    extrait_naissance_fourni yes_no_enum DEFAULT 'non',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_catechumenes_id ON catechumenes(id_catechumene);
CREATE INDEX idx_catechumenes_nom ON catechumenes(nom);
CREATE INDEX idx_catechumenes_prenoms ON catechumenes(prenoms);
CREATE INDEX idx_catechumenes_code_parent ON catechumenes(code_parent);
CREATE INDEX idx_catechumenes_baptise ON catechumenes(baptise);
CREATE INDEX idx_catechumenes_fulltext ON catechumenes USING gin((nom || ' ' || prenoms) gin_trgm_ops);

-- 2. PARENTS table
CREATE TABLE parents (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    code_parent TEXT UNIQUE NOT NULL,
    prenoms TEXT NOT NULL,
    nom TEXT,
    telephone TEXT UNIQUE NOT NULL,
    telephone2 TEXT,
    email TEXT,
    actif BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_parents_code_parent ON parents(code_parent);
CREATE INDEX idx_parents_telephone ON parents(telephone);
CREATE INDEX idx_parents_actif ON parents(actif);

-- 3. CLASSES table
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    classe_nom TEXT UNIQUE NOT NULL,
    description TEXT,
    niveau TEXT, -- CP, CI, CE1, CE2, CM1, CM2, 5ème, 6ème
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert standard classes
INSERT INTO classes (classe_nom, niveau) VALUES 
('1ère Année Pré-Catéchuménat (CI)', 'CI'),
('2ème Année Pré-Catéchuménat (CP)', 'CP'),
('1ère Année Communion (CE1)', 'CE1'),
('2ème Année Communion (CE2)', 'CE2'),
('3ème Année Communion (CM1)', 'CM1'),
('1ère Année Confirmation (CM2)', 'CM2'),
('2ème Année Confirmation (5ème)', '5ème'),
('3ème Année Confirmation (6ème)', '6ème');

-- 4. ANNEES_SCOLAIRES table
CREATE TABLE annees_scolaires (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    annee_nom TEXT UNIQUE NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert current school years
INSERT INTO annees_scolaires (annee_nom, active) VALUES 
('2024-2025', true),
('2023-2024', false);

-- 5. INSCRIPTIONS table
CREATE TABLE inscriptions (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    id_inscription TEXT UNIQUE NOT NULL,
    id_catechumene TEXT NOT NULL REFERENCES catechumenes(id_catechumene),
    prenoms TEXT NOT NULL,
    nom TEXT NOT NULL,
    annee_precedente TEXT,
    paroisse_annee_precedente TEXT,
    id_classe_courante UUID REFERENCES classes(id),
    montant INTEGER DEFAULT 0,
    paye INTEGER DEFAULT 0,
    date_inscription TIMESTAMP WITH TIME ZONE,
    commentaire TEXT,
    sms yes_no_enum DEFAULT 'non',
    action action_type,
    attestation_de_transfert yes_no_enum DEFAULT 'non',
    operateur TEXT,
    id_annee_inscription UUID REFERENCES annees_scolaires(id),
    resultat_final TEXT,
    note_finale DECIMAL(5,2),
    moyen_paiement moyen_paiement_type,
    infos_paiement TEXT,
    choix_paiement TEXT,
    id_annee_suivante UUID REFERENCES classes(id),
    etat etat_inscription DEFAULT 'En attente',
    absences INTEGER DEFAULT 0,
    livre_remis yes_no_enum DEFAULT 'non',
    groupe TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_inscriptions_id_catechumene ON inscriptions(id_catechumene);
CREATE INDEX idx_inscriptions_nom ON inscriptions(nom);
CREATE INDEX idx_inscriptions_prenoms ON inscriptions(prenoms);
CREATE INDEX idx_inscriptions_annee_inscription ON inscriptions(id_annee_inscription);
CREATE INDEX idx_inscriptions_classe_courante ON inscriptions(id_classe_courante);
CREATE INDEX idx_inscriptions_date_inscription ON inscriptions(date_inscription);
CREATE INDEX idx_inscriptions_fulltext ON inscriptions USING gin((nom || ' ' || prenoms) gin_trgm_ops);

-- 6. NOTES table
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    id_inscription UUID REFERENCES inscriptions(id),
    id_catechumene TEXT REFERENCES catechumenes(id_catechumene),
    trimestre INTEGER NOT NULL CHECK (trimestre >= 1 AND trimestre <= 3),
    annee_scolaire TEXT NOT NULL,
    note DECIMAL(5,2) CHECK (note >= 0 AND note <= 20),
    appreciation TEXT,
    absences INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_notes_id_inscription ON notes(id_inscription);
CREATE INDEX idx_notes_id_catechumene ON notes(id_catechumene);
CREATE INDEX idx_notes_trimestre ON notes(trimestre);
CREATE INDEX idx_notes_annee_scolaire ON notes(annee_scolaire);

-- 7. FILES table (to store file references from Baserow)
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL, -- 'baptism', 'birth_certificate', 'transfer_attestation'
    file_url TEXT,
    catechumene_id TEXT REFERENCES catechumenes(id_catechumene),
    inscription_id UUID REFERENCES inscriptions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_files_catechumene_id ON files(catechumene_id);
CREATE INDEX idx_files_inscription_id ON files(inscription_id);
CREATE INDEX idx_files_type ON files(file_type);

-- 8. TRIGGERS for updated_at timestamps
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp_catechumenes
    BEFORE UPDATE ON catechumenes
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_parents
    BEFORE UPDATE ON parents
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_inscriptions
    BEFORE UPDATE ON inscriptions
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_notes
    BEFORE UPDATE ON notes
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_files
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- 9. ROW LEVEL SECURITY (RLS) Setup
ALTER TABLE catechumenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE parents ENABLE ROW LEVEL SECURITY;
ALTER TABLE inscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (adjust as needed)
CREATE POLICY "Enable read access for all users" ON catechumenes
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON parents
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON inscriptions
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON notes
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON files
    FOR SELECT USING (true);

-- 10. Helper Functions
-- Function to get student's full information
CREATE OR REPLACE FUNCTION get_student_info(p_id_catechumene TEXT)
RETURNS TABLE(
    id_catechumene TEXT,
    prenoms TEXT,
    nom TEXT,
    baptise yes_no_enum,
    lieu_bapteme TEXT,
    annee_naissance TEXT,
    code_parent TEXT,
    parent_prenoms TEXT,
    parent_nom TEXT,
    parent_telephone TEXT,
    current_classe TEXT,
    current_annee TEXT,
    resultat_final TEXT,
    note_finale DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id_catechumene,
        c.prenoms,
        c.nom,
        c.baptise,
        c.lieu_bapteme,
        c.annee_naissance,
        c.code_parent,
        p.prenoms as parent_prenoms,
        p.nom as parent_nom,
        p.telephone as parent_telephone,
        cl.classe_nom as current_classe,
        an.annee_nom as current_annee,
        i.resultat_final,
        i.note_finale
    FROM catechumenes c
    LEFT JOIN parents p ON c.code_parent = p.code_parent
    LEFT JOIN inscriptions i ON c.id_catechumene = i.id_catechumene 
        AND i.etat = 'Inscription Validée'
        AND i.id_annee_inscription = (SELECT id FROM annees_scolaires WHERE active = true LIMIT 1)
    LEFT JOIN classes cl ON i.id_classe_courante = cl.id
    LEFT JOIN annees_scolaires an ON i.id_annee_inscription = an.id
    WHERE c.id_catechumene = p_id_catechumene;
END;
$$ LANGUAGE plpgsql;

-- Function to get student grades history
CREATE OR REPLACE FUNCTION get_student_grades(p_id_catechumene TEXT)
RETURNS TABLE(
    annee_scolaire TEXT,
    trimestre INTEGER,
    note DECIMAL(5,2),
    appreciation TEXT,
    absences INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.annee_scolaire,
        n.trimestre,
        n.note,
        n.appreciation,
        n.absences
    FROM notes n
    WHERE n.id_catechumene = p_id_catechumene
    ORDER BY n.annee_scolaire DESC, n.trimestre;
END;
$$ LANGUAGE plpgsql;

-- Function to search students (full-text search)
CREATE OR REPLACE FUNCTION search_students(p_search_term TEXT)
RETURNS TABLE(
    id_catechumene TEXT,
    prenoms TEXT,
    nom TEXT,
    code_parent TEXT,
    current_classe TEXT,
    current_annee TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id_catechumene,
        c.prenoms,
        c.nom,
        c.code_parent,
        cl.classe_nom as current_classe,
        an.annee_nom as current_annee
    FROM catechumenes c
    LEFT JOIN inscriptions i ON c.id_catechumene = i.id_catechumene 
        AND i.etat = 'Inscription Validée'
        AND i.id_annee_inscription = (SELECT id FROM annees_scolaires WHERE active = true LIMIT 1)
    LEFT JOIN classes cl ON i.id_classe_courante = cl.id
    LEFT JOIN annees_scolaires an ON i.id_annee_inscription = an.id
    WHERE c.nom ILIKE '%' || p_search_term || '%'
       OR c.prenoms ILIKE '%' || p_search_term || '%'
       OR (c.nom || ' ' || c.prenoms) ILIKE '%' || p_search_term || '%'
    ORDER BY c.nom, c.prenoms;
END;
$$ LANGUAGE plpgsql;