#!/usr/bin/env python3
"""
Extract Non-Migrated Data from Baserow to Text File
"""

import os
import sys
import requests
from supabase_config import get_supabase_client, get_supabase_anon_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
BASEROW_URL = os.getenv("BASEROW_URL")
BASEROW_AUTH_KEY = os.getenv("BASEROW_AUTH_KEY")

def get_all_baserow_inscriptions():
    """Get all inscriptions from Baserow"""
    print("📥 Fetching all inscriptions from Baserow...")
    
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
            return None
        
        data = response.json()
        all_inscriptions.extend(data['results'])
        
        if not data['next']:
            break
            
        page += 1
    
    return all_inscriptions

def get_migrated_inscriptions():
    """Get all migrated inscriptions from Supabase"""
    print("📤 Getting migrated inscriptions from Supabase...")
    
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('inscriptions').select('id_inscription').execute()
        
        if result.data:
            return {inscr['id_inscription'] for inscr in result.data}
        return set()
        
    except Exception as e:
        print(f"❌ Error getting migrated inscriptions: {e}")
        return set()

def get_student_mapping():
    """Get mapping of student IDs to check foreign key constraints"""
    print("👥 Getting student mapping from Supabase...")
    
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('catechumenes').select('id_catechumene').execute()
        
        if result.data:
            return {student['id_catechumene'] for student in result.data}
        return set()
        
    except Exception as e:
        print(f"❌ Error getting student mapping: {e}")
        return set()

def get_class_mapping():
    """Get class mapping from Supabase"""
    print("🏫 Getting class mapping from Supabase...")
    
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('classes').select('id, classe_nom').execute()
        
        if result.data:
            return {c['classe_nom']: c['id'] for c in result.data}
        return {}
        
    except Exception as e:
        print(f"❌ Error getting class mapping: {e}")
        return {}

def get_year_mapping():
    """Get year mapping from Supabase"""
    print("📅 Getting year mapping from Supabase...")
    
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('annees_scolaires').select('id, annee_nom').execute()
        
        if result.data:
            return {y['annee_nom']: y['id'] for y in result.data}
        return {}
        
    except Exception as e:
        print(f"❌ Error getting year mapping: {e}")
        return {}

def analyze_non_migrated(non_migrated, student_mapping, class_mapping, year_mapping):
    """Analyze why records weren't migrated"""
    print("🔍 Analyzing migration issues...")
    
    analysis = {
        'total': len(non_migrated),
        'missing_students': 0,
        'missing_classes': 0,
        'missing_years': 0,
        'invalid_enums': 0,
        'other_issues': 0,
        'details': []
    }
    
    # Valid enum values
    valid_actions = ['Nouvelle Inscription', 'Réinscription', 'Transfert à partir d\'une autre paroisse']
    valid_moyens_paiement = ['CASH', 'WAVE', 'OM', 'CB']
    valid_etats = ['Inscription Validée', 'En attente', 'Annulée']
    valid_yes_no = ['oui', 'non']
    
    for inscr in non_migrated:
        issues = []
        
        # Check foreign key constraints
        if inscr.get('ID Catechumene') not in student_mapping:
            issues.append('Missing student in catechumenes')
            analysis['missing_students'] += 1
        
        # Check class mapping
        if inscr.get('ID_ClasseCourante') and inscr['ID_ClasseCourante']:
            class_name = inscr['ID_ClasseCourante'][0]['value'] if inscr['ID_ClasseCourante'] else None
            if class_name and class_name not in class_mapping:
                issues.append('Missing class in classes')
                analysis['missing_classes'] += 1
        
        # Check year mapping
        if inscr.get('ID_AnneeInscription') and inscr['ID_AnneeInscription']:
            year_name = inscr['ID_AnneeInscription'][0]['value'] if inscr['ID_AnneeInscription'] else None
            if year_name and year_name not in year_mapping:
                issues.append('Missing year in annees_scolaires')
                analysis['missing_years'] += 1
        
        # Check enum values
        action = inscr.get('action')
        if action and action not in valid_actions:
            issues.append(f'Invalid action: {action}')
            analysis['invalid_enums'] += 1
        
        moyen_paiement = inscr.get('Moyen Paiement')
        if moyen_paiement and moyen_paiement not in valid_moyens_paiement:
            issues.append(f'Invalid moyen_paiement: {moyen_paiement}')
            analysis['invalid_enums'] += 1
        
        etat = inscr.get('Etat')
        if etat and etat not in valid_etats:
            issues.append(f'Invalid etat: {etat}')
            analysis['invalid_enums'] += 1
        
        # Check yes/no fields
        yes_no_fields = ['sms', 'AttestationDeTransfert', 'Livre Remis']
        for field in yes_no_fields:
            value = inscr.get(field)
            if value and value not in valid_yes_no and '/' not in str(value):  # Date formats like '16/11' are invalid
                issues.append(f'Invalid {field}: {value}')
                analysis['invalid_enums'] += 1
        
        if not issues:
            issues.append('Unknown issue')
            analysis['other_issues'] += 1
        
        analysis['details'].append({
            'id': inscr['ID Inscription'],
            'name': f"{inscr.get('Prenoms')} {inscr.get('Nom')}",
            'issues': issues
        })
    
    return analysis

def create_report(non_migrated, analysis):
    """Create a comprehensive report"""
    print("📄 Creating report...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# Non-Migrated Inscriptions Report
Generated: {timestamp}

## Summary
- Total Baserow Inscriptions: 802
- Successfully Migrated: 598
- Non-Migrated: {analysis['total']}
- Migration Success Rate: {((802 - analysis['total']) / 802 * 100):.1f}%

## Migration Issues Breakdown
- Missing Students: {analysis['missing_students']}
- Missing Classes: {analysis['missing_classes']}  
- Missing Years: {analysis['missing_years']}
- Invalid Enum Values: {analysis['invalid_enums']}
- Other Issues: {analysis['other_issues']}

## Detailed Non-Migrated Records

"""
    
    for i, detail in enumerate(analysis['details'], 1):
        report += f"""
### {i}. {detail['name']} (ID: {detail['id']})
Issues: {', '.join(detail['issues'])}

"""
    
    report += """
## Recommendations
1. **Missing Students**: Add student records to catechumenes table first
2. **Missing Classes/Years**: Ensure all reference data exists
3. **Invalid Enums**: Clean up data values to match valid enum options
4. **Data Quality**: Implement validation before future migrations

## Data Cleaning Required
The following enum fields need standardization:
- action: Should be one of 'Nouvelle Inscription', 'Réinscription', 'Transfert à partir d\'une autre paroisse'
- moyen_paiement: Should be one of 'CASH', 'WAVE', 'OM', 'CB'
- etat: Should be one of 'Inscription Validée', 'En attente', 'Annulée'
- yes/no fields: Should be 'oui' or 'non'

## Next Steps
1. Clean up the data issues identified above
2. Re-run migration for cleaned records
3. Consider data validation rules in Baserow
"""
    
    return report

def save_raw_data(non_migrated, filename):
    """Save raw non-migrated data"""
    print(f"💾 Saving raw data to {filename}...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Raw Non-Migrated Inscriptions Data\n\n")
        
        for i, inscr in enumerate(non_migrated, 1):
            f.write(f"## Record {i}\n")
            f.write(f"ID: {inscr['ID Inscription']}\n")
            f.write(f"Student: {inscr.get('Prenoms')} {inscr.get('Nom')}\n")
            f.write(f"Student ID: {inscr.get('ID Catechumene')}\n")
            f.write(f"Current Class: {inscr.get('ClasseCourante')}\n")
            f.write(f"Year: {inscr.get('Annee Inscription')}\n")
            f.write(f"Action: {inscr.get('action')}\n")
            f.write(f"Status: {inscr.get('Etat')}\n")
            f.write(f"Payment Method: {inscr.get('Moyen Paiement')}\n")
            f.write(f"Amount: {inscr.get('Montant')}\n")
            f.write(f"Paid: {inscr.get('Paye')}\n")
            f.write(f"SMS: {inscr.get('sms')}\n")
            f.write(f"Transfer Certificate: {inscr.get('AttestationDeTransfert')}\n")
            f.write(f"Absences: {inscr.get('Absennces')}\n")
            f.write(f"Book Given: {inscr.get('Livre Remis')}\n")
            f.write(f"Operator: {inscr.get('operateur')}\n")
            f.write(f"Comments: {inscr.get('Commentaire')}\n")
            f.write(f"Final Result: {inscr.get('Resultat Final')}\n")
            f.write(f"Final Grade: {inscr.get('Note Finale')}\n")
            f.write("-" * 80 + "\n\n")

def main():
    print("🔍 Extracting Non-Migrated Data Report")
    print("=" * 60)
    
    # Get data
    baserow_inscriptions = get_all_baserow_inscriptions()
    if not baserow_inscriptions:
        print("❌ Failed to fetch Baserow data")
        return False
    
    migrated_ids = get_migrated_inscriptions()
    student_mapping = get_student_mapping()
    class_mapping = get_class_mapping()
    year_mapping = get_year_mapping()
    
    # Find non-migrated records
    non_migrated = [inscr for inscr in baserow_inscriptions 
                   if inscr['ID Inscription'] not in migrated_ids]
    
    print(f"📊 Found {len(non_migrated)} non-migrated records")
    
    # Analyze issues
    analysis = analyze_non_migrated(non_migrated, student_mapping, class_mapping, year_mapping)
    
    # Create and save report
    report = create_report(non_migrated, analysis)
    
    with open('non_migrated_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save raw data
    save_raw_data(non_migrated, 'non_migrated_data.txt')
    
    print(f"✅ Report saved to 'non_migrated_report.md'")
    print(f"✅ Raw data saved to 'non_migrated_data.txt'")
    print(f"📈 Migration success rate: {((802 - analysis['total']) / 802 * 100):.1f}%")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)