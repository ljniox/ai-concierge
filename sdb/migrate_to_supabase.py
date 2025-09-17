#!/usr/bin/env python3
"""
Migration script from Baserow to Supabase for SDB
"""

import os
import sys
import requests
import json
from datetime import datetime
from supabase import create_client, Client
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
BASEROW_URL = os.getenv("BASEROW_URL")
BASEROW_AUTH_KEY = os.getenv("BASEROW_AUTH_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Baserow table IDs
TABLES = {
    'catechumenes': 575,
    'inscriptions': 574,
    'parents': 572,
    'classes': 661,
    'annees_scolaires': 576
}

# Headers for Baserow API
headers = {
    "Authorization": f"Token {BASEROW_AUTH_KEY}",
    "Content-Type": "application/json"
}

def initialize_supabase():
    """Initialize Supabase client"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully")
        return supabase
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        return None

def get_all_rows(table_id):
    """Get all rows from a Baserow table"""
    all_rows = []
    page = 1
    
    while True:
        url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/?user_field_names=true&page={page}&size=100"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            all_rows.extend(data['results'])
            
            if data.get('next') is None:
                break
                
            page += 1
            print(f"📄 Fetched page {page} ({len(all_rows)} total rows)")
            
        except Exception as e:
            print(f"❌ Error fetching data from table {table_id}: {e}")
            break
    
    print(f"✅ Retrieved {len(all_rows)} rows from table {table_id}")
    return all_rows

def migrate_parents(supabase):
    """Migrate parents data"""
    print("🔄 Migrating parents...")
    
    parents_data = get_all_rows(TABLES['parents'])
    migrated_count = 0
    
    for parent in parents_data:
        try:
            parent_data = {
                'code_parent': parent.get('Code Parent', ''),
                'prenoms': parent.get('Prenoms', ''),
                'nom': parent.get('Nom', ''),
                'telephone': parent.get('Téléphone', ''),
                'telephone2': parent.get('Téléphone 2', ''),
                'email': parent.get('Email', ''),
                'actif': parent.get('Actif', True)
            }
            
            result = supabase.table('parents').upsert(parent_data).execute()
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating parent {parent.get('Prenoms', 'Unknown')}: {e}")
    
    print(f"✅ Parents migration completed: {migrated_count}/{len(parents_data)} records")
    return migrated_count

def migrate_classes(supabase):
    """Migrate classes data"""
    print("🔄 Migrating classes...")
    
    classes_data = get_all_rows(TABLES['classes'])
    migrated_count = 0
    
    for classe in classes_data:
        try:
            # Extract niveau from class name
            classe_name = classe.get('value', '')
            niveau = ''
            
            if 'CP' in classe_name:
                niveau = 'CP'
            elif 'CI' in classe_name:
                niveau = 'CI'
            elif 'CE1' in classe_name:
                niveau = 'CE1'
            elif 'CE2' in classe_name:
                niveau = 'CE2'
            elif 'CM1' in classe_name:
                niveau = 'CM1'
            elif 'CM2' in classe_name:
                niveau = 'CM2'
            elif '5ème' in classe_name:
                niveau = '5ème'
            elif '6ème' in classe_name:
                niveau = '6ème'
            
            class_data = {
                'classe_nom': classe_name,
                'niveau': niveau,
                'description': f'Classe de {classe_name}'
            }
            
            result = supabase.table('classes').upsert(class_data).execute()
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating class {classe.get('value', 'Unknown')}: {e}")
    
    print(f"✅ Classes migration completed: {migrated_count}/{len(classes_data)} records")
    return migrated_count

def migrate_annees_scolaires(supabase):
    """Migrate school years data"""
    print("🔄 Migrating school years...")
    
    annees_data = get_all_rows(TABLES['annees_scolaires'])
    migrated_count = 0
    
    for annee in annees_data:
        try:
            annee_data = {
                'annee_nom': annee.get('value', ''),
                'description': f'Année scolaire {annee.get("value", "")}',
                'active': annee.get('value', '') == '2024-2025'
            }
            
            result = supabase.table('annees_scolaires').upsert(annee_data).execute()
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating school year {annee.get('value', 'Unknown')}: {e}")
    
    print(f"✅ School years migration completed: {migrated_count}/{len(annees_data)} records")
    return migrated_count

def migrate_catechumenes(supabase):
    """Migrate catechumenes data"""
    print("🔄 Migrating catechumenes...")
    
    catechumenes_data = get_all_rows(TABLES['catechumenes'])
    migrated_count = 0
    
    for catechumene in catechumenes_data:
        try:
            catechumene_data = {
                'id_catechumene': catechumene.get('ID Catechumene', ''),
                'prenoms': catechumene.get('Prenoms', ''),
                'nom': catechumene.get('Nom', ''),
                'baptise': catechumene.get('Baptisee', 'non'),
                'extrait_bapteme_fourni': catechumene.get('Extrait De Bapteme Fourni', 'non'),
                'lieu_bapteme': catechumene.get('LieuBapteme', ''),
                'commentaire': catechumene.get('Commentaire', ''),
                'annee_naissance': catechumene.get('Année de naissance', ''),
                'attestation_transfert_fournie': catechumene.get('Attestation De Transfert Fournie', 'non'),
                'operateur': catechumene.get('operateur', ''),
                'code_parent': catechumene.get('Code Parent', ''),
                'extrait_naissance_fourni': catechumene.get('Extrait de Naissance Fourni', 'non')
            }
            
            result = supabase.table('catechumenes').upsert(catechumene_data).execute()
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating catechumene {catechumene.get('Prenoms', 'Unknown')}: {e}")
    
    print(f"✅ Catechumenes migration completed: {migrated_count}/{len(catechumenes_data)} records")
    return migrated_count

def get_class_id_by_name(supabase, classe_name):
    """Get class UUID by name"""
    try:
        result = supabase.table('classes').select('id').eq('classe_nom', classe_name).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]['id']
    except Exception as e:
        print(f"❌ Error getting class ID for {classe_name}: {e}")
    return None

def get_annee_id_by_name(supabase, annee_name):
    """Get school year UUID by name"""
    try:
        result = supabase.table('annees_scolaires').select('id').eq('annee_nom', annee_name).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]['id']
    except Exception as e:
        print(f"❌ Error getting school year ID for {annee_name}: {e}")
    return None

def migrate_inscriptions(supabase):
    """Migrate inscriptions data"""
    print("🔄 Migrating inscriptions...")
    
    inscriptions_data = get_all_rows(TABLES['inscriptions'])
    migrated_count = 0
    
    for inscription in inscriptions_data:
        try:
            # Get foreign key IDs
            id_classe_courante = None
            id_annee_inscription = None
            id_annee_suivante = None
            
            # Get current class ID
            classe_courante = inscription.get('ClasseCourante', '')
            if classe_courante:
                id_classe_courante = get_class_id_by_name(supabase, classe_courante)
            
            # Get school year ID
            annee_inscription = inscription.get('Annee Inscription', '')
            if annee_inscription:
                id_annee_inscription = get_annee_id_by_name(supabase, annee_inscription)
            
            # Get next year class ID
            annee_suivante = inscription.get('Annee Suivante', '')
            if annee_suivante:
                id_annee_suivante = get_class_id_by_name(supabase, annee_suivante)
            
            # Parse date
            date_inscription = None
            date_str = inscription.get('DateInscription', '')
            if date_str:
                try:
                    date_inscription = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            inscription_data = {
                'id_inscription': inscription.get('ID Inscription', ''),
                'id_catechumene': inscription.get('ID Catechumene', ''),
                'prenoms': inscription.get('Prenoms', ''),
                'nom': inscription.get('Nom', ''),
                'annee_precedente': inscription.get('AnneePrecedente', ''),
                'paroisse_annee_precedente': inscription.get('ParoisseAnneePrecedente', ''),
                'id_classe_courante': id_classe_courante,
                'montant': inscription.get('Montant', 0),
                'paye': inscription.get('Paye', 0),
                'date_inscription': date_inscription,
                'commentaire': inscription.get('Commentaire', ''),
                'sms': inscription.get('sms', 'non'),
                'action': inscription.get('action', ''),
                'attestation_de_transfert': inscription.get('AttestationDeTransfert', 'non'),
                'operateur': inscription.get('operateur', ''),
                'id_annee_inscription': id_annee_inscription,
                'resultat_final': inscription.get('Resultat Final', ''),
                'note_finale': inscription.get('Note Finale', 0),
                'moyen_paiement': inscription.get('Moyen Paiement', ''),
                'infos_paiement': inscription.get('Infos Paiement', ''),
                'choix_paiement': inscription.get('Choix Paiement', ''),
                'id_annee_suivante': id_annee_suivante,
                'etat': inscription.get('Etat', 'En attente'),
                'absences': inscription.get('Absennces', 0),
                'livre_remis': inscription.get('Livre Remis', 'non'),
                'groupe': inscription.get('Groupe', '')
            }
            
            result = supabase.table('inscriptions').upsert(inscription_data).execute()
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating inscription {inscription.get('Prenoms', 'Unknown')}: {e}")
    
    print(f"✅ Inscriptions migration completed: {migrated_count}/{len(inscriptions_data)} records")
    return migrated_count

def run_migration():
    """Run the complete migration process"""
    print("🚀 Starting SDB migration to Supabase...")
    
    # Initialize Supabase client
    supabase = initialize_supabase()
    if not supabase:
        return False
    
    # Migration statistics
    stats = {}
    
    # Run migrations in order
    try:
        stats['parents'] = migrate_parents(supabase)
        stats['classes'] = migrate_classes(supabase)
        stats['annees_scolaires'] = migrate_annees_scolaires(supabase)
        stats['catechumenes'] = migrate_catechumenes(supabase)
        stats['inscriptions'] = migrate_inscriptions(supabase)
        
        print("\n🎉 Migration completed successfully!")
        print("\n📊 Migration Statistics:")
        for table, count in stats.items():
            print(f"   {table}: {count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)