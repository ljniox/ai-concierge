#!/usr/bin/env python3
"""
Migrate Inscriptions Data from Baserow to Supabase
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

def migrate_inscriptions():
    """Migrate inscriptions from Baserow to Supabase"""
    print("🔄 Migrating inscriptions data...")
    
    try:
        supabase = get_supabase_client()
        
        # Get class mappings first
        classes_result = supabase.table('classes').select('*').execute()
        class_mapping = {c['classe_nom']: c['id'] for c in classes_result.data}
        
        # Get year mappings
        years_result = supabase.table('annees_scolaires').select('*').execute()
        year_mapping = {y['annee_nom']: y['id'] for y in years_result.data}
        
        print(f"📊 Found {len(class_mapping)} classes and {len(year_mapping)} years")
        
        # Fetch all inscriptions from Baserow
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
                return False
            
            data = response.json()
            all_inscriptions.extend(data['results'])
            
            if not data['next']:
                break
                
            page += 1
        
        print(f"📝 Found {len(all_inscriptions)} inscriptions to migrate")
        
        # Process and insert inscriptions
        migrated_count = 0
        error_count = 0
        
        for inscr in all_inscriptions:
            try:
                # Map class names to IDs
                current_class = None
                if inscr.get('ID_ClasseCourante') and inscr['ID_ClasseCourante']:
                    current_class = class_mapping.get(inscr['ID_ClasseCourante'][0]['value'])
                
                # Map year names to IDs
                year_inscription = None
                if inscr.get('ID_AnneeInscription') and inscr['ID_AnneeInscription']:
                    year_inscription = year_mapping.get(inscr['ID_AnneeInscription'][0]['value'])
                
                # Prepare inscription data
                inscription_data = {
                    'id_inscription': inscr['ID Inscription'],
                    'id_catechumene': inscr['ID Catechumene'],
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
                    'sms': inscr.get('sms'),
                    'action': inscr.get('action'),
                    'attestation_de_transfert': inscr.get('AttestationDeTransfert'),
                    'operateur': inscr.get('operateur'),
                    'resultat_final': inscr.get('Resultat Final'),
                    'note_finale': float(inscr.get('Note Finale', 0)) if inscr.get('Note Finale') else 0,
                    'moyen_paiement': inscr.get('Moyen Paiement'),
                    'infos_paiement': inscr.get('Infos Paiement'),
                    'etat': inscr.get('Etat') or 'Inscription Validée',
                    'absences': int(inscr.get('Absennces', 0)) if inscr.get('Absennces') else 0,
                    'groupe': inscr.get('Groupe'),
                    'livre_remis': inscr.get('Livre Remis')
                }
                
                # Insert into Supabase
                result = supabase.table('inscriptions').insert(inscription_data).execute()
                
                if result.data:
                    migrated_count += 1
                    if migrated_count % 50 == 0:
                        print(f"📈 Migrated {migrated_count} inscriptions...")
                else:
                    error_count += 1
                    print(f"❌ Failed to migrate inscription for {inscr.get('Prenoms')} {inscr.get('Nom')}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error migrating inscription {inscr.get('ID Inscription')}: {e}")
                continue
        
        print(f"✅ Migration completed: {migrated_count} inscriptions migrated, {error_count} errors")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Migrating Inscriptions Data")
    print("=" * 50)
    
    success = migrate_inscriptions()
    
    if success:
        print("\n✅ Inscriptions migration completed!")
    else:
        print("\n❌ Inscriptions migration failed!")
    
    sys.exit(0 if success else 1)