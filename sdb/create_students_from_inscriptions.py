#!/usr/bin/env python3
"""
Create Missing Student Records from Orphaned Inscriptions
"""

import os
import sys
import requests
import uuid
from supabase_config import get_supabase_client, get_supabase_anon_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def get_orphaned_inscriptions():
    """Get inscriptions that can't be migrated due to missing student records"""
    print("🔍 Finding orphaned inscriptions...")
    
    try:
        # Get migrated inscription IDs and existing student IDs
        supabase_anon = get_supabase_anon_client()
        
        migrated_result = supabase_anon.table('inscriptions').select('id_inscription').execute()
        migrated_ids = {inscr['id_inscription'] for inscr in migrated_result.data}
        
        students_result = supabase_anon.table('catechumenes').select('id_catechumene').execute()
        existing_student_ids = {student['id_catechumene'] for student in students_result.data}
        
        # Fetch all inscriptions from Baserow
        BASEROW_URL = os.getenv("BASEROW_URL")
        BASEROW_AUTH_KEY = os.getenv("BASEROW_AUTH_KEY")
        
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
            all_inscriptions.extend(data['results'])
            
            if not data['next']:
                break
                
            page += 1
        
        # Filter for orphaned inscriptions
        orphaned = []
        for inscr in all_inscriptions:
            student_id = inscr.get('ID Catechumene')
            inscription_id = inscr['ID Inscription']
            
            # Skip if already migrated or student exists
            if inscription_id in migrated_ids:
                continue
            if student_id and student_id in existing_student_ids:
                continue
            
            orphaned.append(inscr)
        
        print(f"📝 Found {len(orphaned)} orphaned inscriptions")
        return orphaned
        
    except Exception as e:
        print(f"❌ Error getting orphaned inscriptions: {e}")
        return []

def create_student_from_inscription(inscription):
    """Create a student record from inscription data"""
    try:
        # Generate new UUID for the student
        new_student_id = str(uuid.uuid4())
        
        # Extract available data from inscription
        prenoms = inscription.get('Prenoms', '').strip()
        nom = inscription.get('Nom', '').strip()
        
        # Handle date of birth extraction (might be in name field)
        date_naissance = None
        telephone = None
        email = None
        adresse = None
        
        # Try to extract birth date from parentheses in name
        import re
        date_pattern = r'\((\d{2}/\d{2}/\d{4})\)'
        date_match = re.search(date_pattern, prenoms)
        if date_match:
            date_naissance = date_match.group(1)
            # Remove date from prenoms
            prenoms = re.sub(date_pattern, '', prenoms).strip()
        
        date_match = re.search(date_pattern, nom)
        if date_match:
            date_naissance = date_match.group(1)
            # Remove date from nom
            nom = re.sub(date_pattern, '', nom).strip()
        
        # Create student data - only use available columns
        student_data = {
            'id_catechumene': new_student_id,
            'prenoms': prenoms,
            'nom': nom,
            'annee_naissance': date_naissance.split('/')[-1] if date_naissance else None,  # Extract year from DD/MM/YYYY
            'baptise': None,
            'extrait_bapteme_fourni': None,
            'attestation_transfert_fournie': None,
            'extrait_naissance_fourni': None,
            'operateur': 'Auto-généré',
            'commentaire': f"Créé automatiquement depuis l'inscription {inscription.get('ID Inscription')} - Date: {date_naissance}"
        }
        
        return student_data
        
    except Exception as e:
        print(f"❌ Error creating student from inscription {inscription.get('ID Inscription')}: {e}")
        return None

def create_missing_students_and_migrate():
    """Create missing student records and migrate their inscriptions"""
    print("🔧 Creating missing student records and migrating inscriptions...")
    
    try:
        # Get orphaned inscriptions
        orphaned_inscriptions = get_orphaned_inscriptions()
        if not orphaned_inscriptions:
            print("✅ No orphaned inscriptions found!")
            return True
        
        supabase = get_supabase_client()
        
        # Get mappings
        classes_result = supabase.table('classes').select('*').execute()
        class_mapping = {c['classe_nom']: c['id'] for c in classes_result.data}
        
        years_result = supabase.table('annees_scolaires').select('*').execute()
        year_mapping = {y['annee_nom']: y['id'] for y in years_result.data}
        
        print(f"📊 Available classes: {len(class_mapping)}")
        print(f"📊 Available years: {len(year_mapping)}")
        
        students_created = 0
        inscriptions_migrated = 0
        errors = 0
        
        print(f"🔄 Processing {len(orphaned_inscriptions)} orphaned inscriptions...")
        
        for i, inscr in enumerate(orphaned_inscriptions):
            try:
                if i % 20 == 0:
                    print(f"📈 Progress: {i}/{len(orphaned_inscriptions)}")
                
                # Skip if no name data
                if not inscr.get('Prenoms') and not inscr.get('Nom'):
                    print(f"⚠️  Skipping {inscr.get('ID Inscription')} - no name data")
                    errors += 1
                    continue
                
                # Create student record
                student_data = create_student_from_inscription(inscr)
                if not student_data:
                    errors += 1
                    continue
                
                # Insert student
                student_result = supabase.table('catechumenes').insert(student_data).execute()
                
                if not student_result.data:
                    print(f"❌ Failed to create student for {inscr.get('ID Inscription')}")
                    errors += 1
                    continue
                
                students_created += 1
                student_id = student_data['id_catechumene']
                
                print(f"✅ Created student: {student_data['prenoms']} {student_data['nom']}")
                
                # Now migrate the inscription
                # Apply class mappings
                class_name = inscr.get('ClasseCourante', '').strip()
                class_mappings = {
                    '2ème Année Confirmation (6e)': '2ème Année Confirmation (5ème)',
                    '3ème Année Confirmation (5e)': '3ème Année Confirmation (6ème)',
                    '8': '3ème Année Confirmation (6ème)'
                }
                
                if class_name in class_mappings:
                    class_name = class_mappings[class_name]
                
                # Get class ID
                class_id = class_mapping.get(class_name) if class_name in class_mapping else None
                
                # Get year ID
                year_id = None
                if inscr.get('ID_AnneeInscription') and inscr['ID_AnneeInscription']:
                    year_name = inscr['ID_AnneeInscription'][0]['value']
                    year_id = year_mapping.get(year_name)
                
                # Clean enum values
                def clean_enum(value, field_type):
                    if not value:
                        return None
                    
                    value = str(value).strip()
                    
                    if field_type == 'etat':
                        if value.lower() in ['inscription validée', 'inscription validee']:
                            return 'Inscription Validée'
                        elif value in ['Inscription Validée', 'En attente', 'Annulée']:
                            return value
                        return 'En attente'
                    
                    elif field_type == 'moyen_paiement':
                        if value.upper() in ['ORANGE MONEY', 'OM']:
                            return 'OM'
                        elif value.lower() in ['au secrétariat', 'cash']:
                            return 'CASH'
                        elif value in ['CASH', 'WAVE', 'OM', 'CB']:
                            return value
                        return None
                    
                    elif field_type == 'yes_no':
                        if value.lower() in ['oui', 'non']:
                            return value.lower()
                        return None
                    
                    elif field_type == 'action':
                        if value.lower() == 'transfert':
                            return 'Transfert à partir d\'une autre paroisse'
                        elif value in ['Nouvelle Inscription', 'Réinscription', 'Transfert à partir d\'une autre paroisse']:
                            return value
                        return None
                    
                    return value
                
                # Prepare inscription data
                inscription_data = {
                    'id_inscription': inscr['ID Inscription'],
                    'id_catechumene': student_id,
                    'prenoms': inscr.get('Prenoms'),
                    'nom': inscr.get('Nom'),
                    'id_classe_courante': class_id,
                    'id_annee_inscription': year_id,
                    'annee_precedente': inscr.get('AnneePrecedente'),
                    'paroisse_annee_precedente': inscr.get('ParoisseAnneePrecedente'),
                    'montant': int(float(inscr.get('Montant', 0))) if inscr.get('Montant') else 0,
                    'paye': int(float(inscr.get('Paye', 0))) if inscr.get('Paye') else 0,
                    'date_inscription': inscr.get('DateInscription'),
                    'commentaire': inscr.get('Commentaire'),
                    'sms': clean_enum(inscr.get('sms'), 'yes_no'),
                    'action': clean_enum(inscr.get('action'), 'action'),
                    'attestation_de_transfert': clean_enum(inscr.get('AttestationDeTransfert'), 'yes_no'),
                    'operateur': inscr.get('operateur'),
                    'resultat_final': inscr.get('Resultat Final'),
                    'note_finale': float(inscr.get('Note Finale', 0)) if inscr.get('Note Finale') else 0,
                    'moyen_paiement': clean_enum(inscr.get('Moyen Paiement'), 'moyen_paiement'),
                    'infos_paiement': inscr.get('Infos Paiement'),
                    'etat': clean_enum(inscr.get('Etat'), 'etat'),
                    'absences': int(inscr.get('Absennces', 0)) if inscr.get('Absennces') and str(inscr.get('Absennces')).isdigit() else 0,
                    'groupe': inscr.get('Groupe'),
                    'livre_remis': clean_enum(inscr.get('Livre Remis'), 'yes_no')
                }
                
                # Insert inscription
                inscription_result = supabase.table('inscriptions').insert(inscription_data).execute()
                
                if inscription_result.data:
                    inscriptions_migrated += 1
                    print(f"✅ Migrated inscription for {student_data['prenoms']} {student_data['nom']}")
                else:
                    print(f"❌ Failed to migrate inscription {inscr.get('ID Inscription')}")
                    errors += 1
                
            except Exception as e:
                errors += 1
                print(f"❌ Error processing {inscr.get('ID Inscription')}: {e}")
                continue
        
        print(f"\n📊 Results:")
        print(f"✅ Students created: {students_created}")
        print(f"✅ Inscriptions migrated: {inscriptions_migrated}")
        print(f"❌ Errors: {errors}")
        
        return students_created > 0
        
    except Exception as e:
        print(f"❌ Error in create_missing_students_and_migrate: {e}")
        return False

def check_final_results():
    """Check final results after creating students and migrating"""
    print("\n🔍 Checking final results...")
    
    try:
        supabase_anon = get_supabase_anon_client()
        
        # Check total inscriptions
        inscriptions_result = supabase_anon.table('inscriptions').select('count', count='exact').limit(1).execute()
        total_inscriptions = inscriptions_result.count
        
        # Check total students
        students_result = supabase_anon.table('catechumenes').select('count', count='exact').limit(1).execute()
        total_students = students_result.count
        
        print(f"📊 Total inscriptions: {total_inscriptions}")
        print(f"📊 Total students: {total_students}")
        print(f"📈 Migration success rate: {(total_inscriptions/800)*100:.1f}% ({total_inscriptions}/800)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking results: {e}")
        return False

if __name__ == "__main__":
    print("👥 Creating Missing Student Records from Orphaned Inscriptions")
    print("=" * 60)
    
    success = create_missing_students_and_migrate()
    
    if success:
        check_success = check_final_results()
        if check_success:
            print("\n🎉 Student creation and migration completed successfully!")
        else:
            print("\n⚠️  Process completed but verification failed")
    else:
        print("\n❌ Failed to create students and migrate inscriptions!")
    
    sys.exit(0 if success else 1)