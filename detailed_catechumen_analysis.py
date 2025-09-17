#!/usr/bin/env python3
"""
Detailed analysis of catechumen data with enrollment information
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
        # Handle different date formats
        if 'T' in date_str:
            date_str = date_str.split('T')[0]

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month

        # Academic year: September 2023 - August 2024 = 2023-2024
        if month >= 9:  # September onwards
            return f"{year}-{year + 1}"
        else:  # January to August
            return f"{year - 1}-{year}"

    except:
        return None

def analyze_catechumens_with_classes():
    """Analyze catechumen data with enrollment/class information"""

    supabase = connect_to_supabase()
    results = {
        "by_academic_year": {},
        "by_class": {},
        "enrollment_stats": {},
        "raw_data_summary": {}
    }

    # Get catechumenes data
    print("📊 Fetching catechumenes data...")
    catechumenes_response = supabase.table('catechumenes').select('*').execute()
    catechumenes = catechumenes_response.data

    print(f"📈 Found {len(catechumenes)} catechumenes")

    # Get inscriptions data if available
    print("📋 Fetching inscriptions data...")
    try:
        inscriptions_response = supabase.table('inscriptions').select('*').execute()
        inscriptions = inscriptions_response.data
        print(f"📋 Found {len(inscriptions)} inscriptions")
    except:
        inscriptions = []
        print("❌ No inscriptions table found")

    # Get classes data if available
    print("🎓 Fetching classes data...")
    try:
        classes_response = supabase.table('classes').select('*').execute()
        classes = classes_response.data
        print(f"🎓 Found {len(classes)} classes")
    except:
        classes = []
        print("❌ No classes table found")

    # Analyze by creation date (as proxy for enrollment)
    print("\n📅 Analyzing by creation date...")
    year_counts = {}
    class_by_year = {}

    for catechumene in catechumenes:
        created_at = catechumene.get('created_at')
        academic_year = get_academic_year_from_date(created_at)

        if academic_year:
            year_counts[academic_year] = year_counts.get(academic_year, 0) + 1

            if academic_year not in class_by_year:
                class_by_year[academic_year] = {}

            # Try to infer class from year of birth
            birth_year = catechumene.get('annee_naissance')
            if birth_year:
                try:
                    birth_year_int = int(birth_year)
                    current_year = 2024
                    age = current_year - birth_year_int

                    # Simple class mapping based on age
                    if age >= 15:
                        class_level = "15+ ans"
                    elif age >= 12:
                        class_level = "12-14 ans"
                    elif age >= 9:
                        class_level = "9-11 ans"
                    elif age >= 6:
                        class_level = "6-8 ans"
                    else:
                        class_level = "< 6 ans"

                    class_by_year[academic_year][class_level] = class_by_year[academic_year].get(class_level, 0) + 1
                except:
                    class_by_year[academic_year]["Âge inconnu"] = class_by_year[academic_year].get("Âge inconnu", 0) + 1
            else:
                class_by_year[academic_year]["Âge inconnu"] = class_by_year[academic_year].get("Âge inconnu", 0) + 1

    # If we have inscriptions data, analyze by inscription date
    if inscriptions:
        print("\n📝 Analyzing inscriptions data...")
        inscription_years = {}

        for inscription in inscriptions:
            created_at = inscription.get('created_at')
            academic_year = get_academic_year_from_date(created_at)

            if academic_year:
                inscription_years[academic_year] = inscription_years.get(academic_year, 0) + 1

        results["enrollment_stats"]["by_inscription_date"] = inscription_years

    # Analyze baptism status
    baptism_stats = {}
    for catechumene in catechumenes:
        baptise = catechumene.get('baptise', False)
        status = "Baptisé" if baptise else "Non baptisé"
        baptism_stats[status] = baptism_stats.get(status, 0) + 1

    # Analyze document provision
    document_stats = {
        "Extrait de naissance fourni": 0,
        "Extrait de baptême fourni": 0,
        "Attestation de transfert fournie": 0
    }

    for catechumene in catechumenes:
        if catechumene.get('extrait_naissance_fourni', False):
            document_stats["Extrait de naissance fourni"] += 1
        if catechumene.get('extrait_bapteme_fourni', False):
            document_stats["Extrait de baptême fourni"] += 1
        if catechumene.get('attestation_transfert_fournie', False):
            document_stats["Attestation de transfert fournie"] += 1

    # Compile results
    results["by_academic_year"] = year_counts
    results["by_class"] = class_by_year
    results["baptism_stats"] = baptism_stats
    results["document_stats"] = document_stats
    results["raw_data_summary"] = {
        "total_catechumenes": len(catechumenes),
        "total_inscriptions": len(inscriptions),
        "total_classes": len(classes),
        "years_found": list(year_counts.keys())
    }

    return results

def print_detailed_results(results):
    """Print detailed analysis results"""

    print("\n" + "="*80)
    print("📊 ANALYSE DÉTAILLÉE DES CATÉCHUMÈNES")
    print("="*80)

    # Summary
    summary = results["raw_data_summary"]
    print(f"\n📈 RÉSUMÉ GÉNÉRAL:")
    print(f"   Total Catéchumènes: {summary['total_catechumenes']}")
    print(f"   Total Inscriptions: {summary['total_inscriptions']}")
    print(f"   Années scolaires trouvées: {summary['years_found']}")

    # By academic year
    print(f"\n📅 STATISTIQUES PAR ANNÉE SCOLAIRE:")
    print("-" * 60)

    target_years = ["2023-2024", "2024-2025"]
    for year in target_years:
        if year in results["by_academic_year"]:
            count = results["by_academic_year"][year]
            print(f"\n🎓 {year}: {count} catéchumènes")

            # Show class breakdown for this year
            if year in results["by_class"]:
                class_breakdown = results["by_class"][year]
                print(f"   Répartition par classe d'âge:")
                for class_name, class_count in sorted(class_breakdown.items()):
                    percentage = (class_count / count) * 100 if count > 0 else 0
                    print(f"     • {class_name}: {class_count} ({percentage:.1f}%)")
        else:
            print(f"\n❌ Aucune donnée trouvée pour {year}")

    # Baptism statistics
    print(f"\n💧 STATISTIQUES DE BAPTÊME:")
    print("-" * 40)
    for status, count in results["baptism_stats"].items():
        total = sum(results["baptism_stats"].values())
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"   {status}: {count} ({percentage:.1f}%)")

    # Document statistics
    print(f"\n📄 STATISTIQUES DES DOCUMENTS:")
    print("-" * 40)
    for doc_type, count in results["document_stats"].items():
        percentage = (count / summary['total_catechumenes']) * 100
        print(f"   {doc_type}: {count} ({percentage:.1f}%)")

    # Enrollment statistics (if available)
    if results.get("enrollment_stats"):
        print(f"\n📝 STATISTIQUES D'INSCRIPTION:")
        print("-" * 40)
        for year, count in results["enrollment_stats"]["by_inscription_date"].items():
            print(f"   {year}: {count} inscriptions")

    # All years overview
    print(f"\n📊 VUE D'ENSEMBLE PAR ANNÉE:")
    print("-" * 40)
    for year in sorted(results["by_academic_year"].keys()):
        count = results["by_academic_year"][year]
        print(f"   {year}: {count} catéchumènes")

def main():
    """Main function"""
    try:
        results = analyze_catechumens_with_classes()
        print_detailed_results(results)

        # Save results
        with open('detailed_catechumen_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Résultats détaillés sauvegardés dans 'detailed_catechumen_statistics.json'")

        # Generate report for 2023-2024 and 2024-2025
        target_years = ["2023-2024", "2024-2025"]
        report = {}

        for year in target_years:
            report[year] = {
                "total_catechumenes": results["by_academic_year"].get(year, 0),
                "class_breakdown": results["by_class"].get(year, {}),
                "percentage_of_total": 0
            }

        # Calculate percentages
        total_all_years = sum(results["by_academic_year"].values())
        for year in report:
            if total_all_years > 0:
                report[year]["percentage_of_total"] = (report[year]["total_catechumenes"] / total_all_years) * 100

        with open('target_years_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📋 Rapport pour les années cibles sauvegardé dans 'target_years_report.json'")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()