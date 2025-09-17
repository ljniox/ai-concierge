#!/usr/bin/env python3
"""
Examine inscriptions data to find class information for target years
"""

import os
import json
from datetime import datetime
from supabase import create_client
from typing import Dict, List, Any

# Set up environment
os.environ['SUPABASE_URL'] = 'https://ixzpejqzxvxpnkbznqnj.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml4enBlanF6eHZ4cG5rYnpucW5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzcwODUyOCwiZXhwIjoyMDczMjg0NTI4fQ.Jki6OqWq0f1Svd2u2m8Zt3xbust-fSlRlSMcWvnsOz4'

def connect_to_supabase():
    """Connect to Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    return create_client(supabase_url, supabase_key)

def get_academic_year_from_date(date_str):
    """Extract academic year from date string"""
    if not date_str:
        return None

    try:
        if 'T' in date_str:
            date_str = date_str.split('T')[0]

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month

        if month >= 9:
            return f"{year}-{year + 1}"
        else:
            return f"{year - 1}-{year}"

    except:
        return None

def analyze_inscriptions_in_detail():
    """Detailed analysis of inscriptions data"""

    supabase = connect_to_supabase()

    print("📋 Examining inscriptions data structure...")
    inscriptions_response = supabase.table('inscriptions').select('*').limit(5).execute()

    if inscriptions_response.data:
        print("Sample inscription structure:")
        sample = inscriptions_response.data[0]
        for key, value in sample.items():
            print(f"  {key}: {value}")

    print(f"\n📊 Analyzing all {len(inscriptions_response.data)} inscriptions...")

    # Get all inscriptions
    all_inscriptions = supabase.table('inscriptions').select('*').execute().data

    print("\n📅 Analyzing by creation date...")
    year_analysis = {}

    for inscription in all_inscriptions:
        created_at = inscription.get('created_at')
        academic_year = get_academic_year_from_date(created_at)

        if academic_year:
            if academic_year not in year_analysis:
                year_analysis[academic_year] = {
                    'total': 0,
                    'by_class': {},
                    'by_status': {}
                }

            year_analysis[academic_year]['total'] += 1

            # Analyze by class if available
            classe = inscription.get('classe') or inscription.get('niveau') or inscription.get('class')
            if classe:
                year_analysis[academic_year]['by_class'][classe] = year_analysis[academic_year]['by_class'].get(classe, 0) + 1

            # Analyze by status if available
            status = inscription.get('statut') or inscription.get('status') or 'Inconnu'
            year_analysis[academic_year]['by_status'][status] = year_analysis[academic_year]['by_status'].get(status, 0) + 1

    # Look for date-related fields
    print("\n🔍 Looking for date-related fields in inscriptions...")
    sample_inscription = all_inscriptions[0] if all_inscriptions else {}
    date_fields = [key for key in sample_inscription.keys() if 'date' in key.lower() or 'annee' in key.lower() or 'year' in key.lower()]
    print(f"Date fields found: {date_fields}")

    # If we have annee_scolaire field, use that directly
    if 'annee_scolaire' in sample_inscription:
        print("\n📚 Using annee_scolaire field directly...")
        year_analysis_direct = {}

        for inscription in all_inscriptions:
            annee_scolaire = inscription.get('annee_scolaire')
            if annee_scolaire:
                if annee_scolaire not in year_analysis_direct:
                    year_analysis_direct[annee_scolaire] = {
                        'total': 0,
                        'by_class': {},
                        'by_status': {}
                    }

                year_analysis_direct[annee_scolaire]['total'] += 1

                classe = inscription.get('classe') or inscription.get('niveau')
                if classe:
                    year_analysis_direct[annee_scolaire]['by_class'][classe] = year_analysis_direct[annee_scolaire]['by_class'].get(classe, 0) + 1

        year_analysis = year_analysis_direct

    return year_analysis

def print_inscription_analysis(year_analysis):
    """Print detailed inscription analysis"""

    print("\n" + "="*80)
    print("📊 ANALYSE DÉTAILLÉE DES INSCRIPTIONS PAR ANNÉE SCOLAIRE")
    print("="*80)

    target_years = ["2023-2024", "2024-2025"]

    print(f"\n📈 ANNÉES SCOLAIRES TROUVÉES: {sorted(year_analysis.keys())}")

    for year in sorted(year_analysis.keys()):
        data = year_analysis[year]
        print(f"\n🎓 ANNÉE SCOLAIRE {year}:")
        print(f"   Total des inscriptions: {data['total']}")

        if year in target_years:
            print(f"   ⭐ ANNÉE CIBLE ⭐")

        # Class breakdown
        if data['by_class']:
            print(f"   Répartition par classe:")
            for classe, count in sorted(data['by_class'].items()):
                percentage = (count / data['total']) * 100 if data['total'] > 0 else 0
                print(f"     • {classe}: {count} ({percentage:.1f}%)")
        else:
            print(f"   Aucune information de classe disponible")

        # Status breakdown
        if data['by_status']:
            print(f"   Répartition par statut:")
            for status, count in sorted(data['by_status'].items()):
                percentage = (count / data['total']) * 100 if data['total'] > 0 else 0
                print(f"     • {status}: {count} ({percentage:.1f}%)")

    # Summary for target years
    print(f"\n📋 RÉSUMÉ POUR LES ANNÉES CIBLES:")
    print("-" * 60)

    total_target = 0
    for year in target_years:
        if year in year_analysis:
            count = year_analysis[year]['total']
            total_target += count
            print(f"   {year}: {count} inscriptions")
        else:
            print(f"   {year}: 0 inscriptions")

    if total_target > 0:
        print(f"\n   Total pour les années cibles: {total_target} inscriptions")

        # Calculate class distribution for target years
        print(f"\n📊 DISTRIBUTION PAR CLASSE (ANNÉES CIBLES):")
        class_totals = {}

        for year in target_years:
            if year in year_analysis:
                for classe, count in year_analysis[year]['by_class'].items():
                    class_totals[classe] = class_totals.get(classe, 0) + count

        for classe, count in sorted(class_totals.items()):
            percentage = (count / total_target) * 100
            print(f"   • {classe}: {count} ({percentage:.1f}%)")

def main():
    """Main function"""
    try:
        year_analysis = analyze_inscriptions_in_detail()
        print_inscription_analysis(year_analysis)

        # Save results
        with open('inscriptions_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(year_analysis, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Analyse des inscriptions sauvegardée dans 'inscriptions_analysis.json'")

        # Create summary for target years
        target_years = ["2023-2024", "2024-2025"]
        summary = {}

        for year in target_years:
            if year in year_analysis:
                summary[year] = {
                    "total_inscriptions": year_analysis[year]['total'],
                    "class_breakdown": year_analysis[year]['by_class'],
                    "status_breakdown": year_analysis[year]['by_status']
                }
            else:
                summary[year] = {
                    "total_inscriptions": 0,
                    "class_breakdown": {},
                    "status_breakdown": {}
                }

        with open('target_years_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n📋 Résumé des années cibles sauvegardé dans 'target_years_summary.json'")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()