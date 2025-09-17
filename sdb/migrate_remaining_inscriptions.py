#!/usr/bin/env python3
"""
Migrate Non-Migrated Inscriptions with Class Mappings
"""

import os
import sys
import requests
from supabase_config import get_supabase_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASEROW_URL = os.getenv("BASEROW_URL")
BASEROW_AUTH_KEY = os.getenv("BASEROW_AUTH_KEY")

# Class mappings based on analysis
CLASS_MAPPINGS = {
    '2ème Année Confirmation (6e)': '2ème Année Confirmation (5ème)',
    '3ème Année Confirmation (5e)': '3ème Année Confirmation (6ème)',
    '8': '3ème Année Confirmation (6ème)'
}

# Handle special values for enum fields
def clean_enum_value(value, field_type):
    """Clean enum values to match Supabase constraints"""
    if not value:
        return None
    
    value = str(value).strip()
    
    if field_type == 'yes_no':
        if value.lower() in ['oui', 'non']:
            return value.lower()
        # Handle date strings that got into yes/no fields
        if '/' in value:  # Date format like "16/11"
            return None
        return None
    
    elif field_type == 'action':
        valid_actions = ['Nouvelle Inscription', 'Réinscription', 'Transfert à partir d\'une autre paroisse']
        if value in valid_actions:
            return value
        # Handle abbreviations
        if value.lower() == 'transfert':
            return 'Transfert à partir d\'une autre paroisse'
        return None
    
    elif field_type == 'moyen_paiement':
        valid_moyens = ['CASH', 'WAVE', 'OM', 'CB']
        if value in valid_moyens:
            return value
        # Handle variations
        if value.upper() in ['ORANGE MONEY', 'OM']:
            return 'OM'
        if value.lower() in ['au secrétariat', 'cash']:
            return 'CASH'
        return None
    
    elif field_type == 'etat':
        valid_etats = ['Inscription Validée', 'En attente', 'Annulée']
        if value in valid_etats:
            return value
        # Handle spelling variations
        if value.lower() in ['inscription validée', 'inscription validee']:
            return 'Inscription Validée'
        return None
    
    return value

def migrate_remaining_inscriptions():
    """Migrate remaining inscriptions with class mappings"""
    print("🔄 Migrating remaining inscriptions with class mappings...")
    
    try:
        supabase = get_supabase_client()
        
        # Get current mappings
        classes_result = supabase.table('classes').select('*').execute()
        class_mapping = {c['classe_nom']: c['id'] for c in classes_result.data}
        
        years_result = supabase.table('annees_scolaires').select('*').execute()
        year_mapping = {y['annee_nom']: y['id'] for y in years_result.data}
        
        print(f"📊 Available classes: {len(class_mapping)}")
        print(f"📊 Available years: {len(year_mapping)}")
        
        # Get migrated IDs to avoid duplicates
        migrated_result = supabase.table('inscriptions').select('id_inscription').execute()
        migrated_ids = {inscr['id_inscription'] for inscr in migrated_result.data}
        
        # Fetch non-migrated inscriptions from Baserow
        headers = {
            "Authorization": f"Token {BASEROW_AUTH_KEY}"
        }
        
        all_inscriptions = []
        page = 1
        
        while True:
            url = f"{BASEROW_URL}/api/database/rows/table/574/?user_field_names=true&page={page}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Error fetching inscriptions: {response.status_code}")
                break
            
            data = response.json()
            
            # Filter for non-migrated
            page_inscriptions = [inscr for inscr in data['results'] 
                               if inscr['ID Inscription'] not in migrated_ids]
            all_inscriptions.extend(page_inscriptions)
            
            if not data['next']:
                break
                
            page += 1
        
        print(f"📝 Found {len(all_inscriptions)} non-migrated inscriptions")
        
        # Process and insert inscriptions
        migrated_count = 0
        error_count = 0
        skipped_count = 0
        
        for inscr in all_inscriptions:
            try:
                # Apply class mappings
                current_class_name = inscr.get('ClasseCourante', '').strip()
                if current_class_name in CLASS_MAPPINGS:
                    current_class_name = CLASS_MAPPINGS[current_class_name]
                    print(f"🔄 Mapped class: {inscr.get('ClasseCourante')} → {current_class_name}")
                
                # Map class names to IDs
                current_class = None
                if current_class_name and current_class_name in class_mapping:
                    current_class = class_mapping[current_class_name]
                
                # Map year names to IDs
                year_inscription = None
                if inscr.get('ID_AnneeInscription') and inscr['ID_AnneeInscription']:
                    year_name = inscr['ID_AnneeInscription'][0]['value']
                    if year_name in year_mapping:
                        year_inscription = year_mapping[year_name]
                
                # Check if student exists
                student_id = inscr.get('ID Catechumene')
                if student_id:
                    student_check = supabase.table('catechumenes').select('id').eq('id_catechumene', student_id).execute()
                    if not student_check.data:
                        print(f"⚠️  Skipping - Student not found: {student_id}")
                        skipped_count += 1
                        continue
                
                # Clean enum values
                sms = clean_enum_value(inscr.get('sms'), 'yes_no')
                action = clean_enum_value(inscr.get('action'), 'action')
                attestation_transfert = clean_enum_value(inscr.get('AttestationDeTransfert'), 'yes_no')
                moyen_paiement = clean_enum_value(inscr.get('Moyen Paiement'), 'moyen_paiement')
                etat = clean_enum_value(inscr.get('Etat'), 'etat')
                livre_remis = clean_enum_value(inscr.get('Livre Remis'), 'yes_no')
                
                # Skip if critical fields are missing
                if not etat:
                    etat = 'En attente'  # Default value
                
                # Prepare inscription data
                inscription_data = {
                    'id_inscription': inscr['ID Inscription'],
                    'id_catechumene': student_id,
                    'prenoms': inscr.get('Prenoms'),
                    'nom': inscr.get('Nom'),
                    'id_classe_courante': current_class,
                    'id_annee_inscription': year_inscription,
                    'annee_precedente': inscr.get('AnneePrecedente'),
                    'paroisse_annee_precedente': inscr.get('ParoisseAnneePrecedente'),
                    'montant': int(float(inscr.get('Montant', 0))) if inscr.get('Montant') else 0,
                    'paye': int(float(inscr.get('Paye', 0))) if inscr.get('Paye') else 0,
                    'date_inscription': inscr.get('DateInscription'),
                    'commentaire': inscr.get('Commentaire'),
                    'sms': sms,
                    'action': action,
                    'attestation_de_transfert': attestation_transfert,
                    'operateur': inscr.get('operateur'),
                    'resultat_final': inscr.get('Resultat Final'),
                    'note_finale': float(inscr.get('Note Finale', 0)) if inscr.get('Note Finale') else 0,
                    'moyen_paiement': moyen_paiement,
                    'infos_paiement': inscr.get('Infos Paiement'),
                    'etat': etat,
                    'absences': int(inscr.get('Absennces', 0)) if inscr.get('Absennces') and str(inscr.get('Absennces')).isdigit() else 0,
                    'groupe': inscr.get('Groupe'),
                    'livre_remis': livre_remis
                }
                
                # Insert into Supabase
                result = supabase.table('inscriptions').insert(inscription_data).execute()
                
                if result.data:
                    migrated_count += 1
                    if migrated_count % 10 == 0:
                        print(f"📈 Migrated {migrated_count} additional inscriptions...")
                else:
                    error_count += 1
                    print(f"❌ Failed to migrate inscription for {inscr.get('Prenoms')} {inscr.get('Nom')}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error migrating inscription {inscr.get('ID Inscription')}: {e}")
                continue
        
        print(f"\n📊 Migration Summary:")
        print(f"✅ Successfully migrated: {migrated_count}")
        print(f"⚠️  Skipped (missing students): {skipped_count}")
        print(f"❌ Errors: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

def check_migration_results():
    """Check final migration results"""
    print("\n🔍 Checking final migration results...")
    
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('inscriptions').select('count', count='exact').limit(1).execute()
        
        if result:
            total_migrated = result.count
            print(f"📊 Total inscriptions in Supabase: {total_migrated}")
            
            # Expected was 598 + new migrations
            improvement = total_migrated - 598
            if improvement > 0:
                print(f"🎉 Added {improvement} new inscriptions!")
            elif improvement == 0:
                print("⚠️  No new inscriptions added")
            else:
                print("❌ Something went wrong - count decreased")
            
            return True
    except Exception as e:
        print(f"❌ Error checking results: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Migrating Remaining Inscriptions with Class Mappings")
    print("=" * 60)
    
    success = migrate_remaining_inscriptions()
    
    if success:
        check_success = check_migration_results()
        if check_success:
            print("\n🎉 Additional migration completed!")
        else:
            print("\n⚠️  Migration completed but verification failed")
    else:
        print("\n❌ Additional migration failed!")
    
    sys.exit(0 if success else 1)