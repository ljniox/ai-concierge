#!/usr/bin/env python3
"""
Final comprehensive analysis of catechumen data with proper class joins
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

def analyze_with_class_information():
    """Analyze data with proper class information"""

    supabase = connect_to_supabase()

    print("🎓 Fetching classes information...")
    classes_response = supabase.table('classes').select('*').execute()
    classes = {c['id']: c for c in classes_response.data}
    print(f"📚 Found {len(classes)} classes")

    # Create class lookup
    class_names = {}
    for class_id, class_info in classes.items():
        class_names[class_id] = class_info.get('nom') or class_info.get('nom_classe') or f"Class {class_id}"

    print("📊 Fetching inscriptions with class information...")
    # Try to get inscriptions with joined class information
    try:
        # Using raw SQL to join tables properly
        sql_query = """
        SELECT
            i.*,
            c.nom as classe_nom,
            c.niveau as classe_niveau
        FROM inscriptions i
        LEFT JOIN classes c ON i.id_classe_courante = c.id
        ORDER BY i.date_inscription DESC
        """

        # Since we can't execute raw SQL directly, let's get inscriptions and join manually
        inscriptions_response = supabase.table('inscriptions').select('*').execute()
        inscriptions = inscriptions_response.data

        print(f"📝 Processing {len(inscriptions)} inscriptions...")

        # Enhanced inscriptions with class names
        enhanced_inscriptions = []
        for inscription in inscriptions:
            enhanced = inscription.copy()
            classe_id = inscription.get('id_classe_courante')

            if classe_id and classe_id in class_names:
                enhanced['classe_nom'] = class_names[classe_id]
            else:
                enhanced['classe_nom'] = 'Non spécifiée'

            enhanced_inscriptions.append(enhanced)

        # Analyze by date_inscription instead of created_at
        year_analysis = {}

        for inscription in enhanced_inscriptions:
            # Use date_inscription for academic year
            date_inscription = inscription.get('date_inscription')
            academic_year = get_academic_year_from_date(date_inscription)

            if academic_year:
                if academic_year not in year_analysis:
                    year_analysis[academic_year] = {
                        'total': 0,
                        'by_class': {},
                        'by_status': {},
                        'by_result': {}
                    }

                year_analysis[academic_year]['total'] += 1

                # Class analysis
                classe_nom = inscription.get('classe_nom', 'Non spécifiée')
                year_analysis[academic_year]['by_class'][classe_nom] = year_analysis[academic_year]['by_class'].get(classe_nom, 0) + 1

                # Status analysis
                etat = inscription.get('etat', 'Inconnu')
                year_analysis[academic_year]['by_status'][etat] = year_analysis[academic_year]['by_status'].get(etat, 0) + 1

                # Result analysis
                resultat = inscription.get('resultat_final', 'Inconnu')
                year_analysis[academic_year]['by_result'][resultat] = year_analysis[academic_year]['by_result'].get(resultat, 0) + 1

        return year_analysis, enhanced_inscriptions

    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        return {}, []

def generate_final_report(year_analysis, inscriptions):
    """Generate final report for target years"""

    target_years = ["2023-2024", "2024-2025"]

    print("\n" + "="*80)
    print("📊 RAPPORT FINAL DES STATISTIQUES PAR CLASSE")
    print("="*80)

    # Summary of available years
    all_years = sorted(year_analysis.keys())
    print(f"\n📅 ANNÉES SCOLAIRES DISPONIBLES: {all_years}")

    # Target years analysis
    print(f"\n🎯 ANALYSE DES ANNÉES CIBLES:")
    print("-" * 60)

    report_data = {}

    for year in target_years:
        if year in year_analysis:
            data = year_analysis[year]
            report_data[year] = {
                'total_inscriptions': data['total'],
                'class_breakdown': data['by_class'],
                'status_breakdown': data['by_status'],
                'result_breakdown': data['by_result']
            }

            print(f"\n📊 {year}:")
            print(f"   Total des inscriptions: {data['total']}")

            if data['by_class']:
                print(f"   Répartition par classe:")
                for classe, count in sorted(data['by_class'].items()):
                    percentage = (count / data['total']) * 100 if data['total'] > 0 else 0
                    print(f"     • {classe}: {count} ({percentage:.1f}%)")

            if data['by_status']:
                print(f"   Répartition par statut:")
                for status, count in sorted(data['by_status'].items(), key=lambda x: (x[0] or '', x[1])):
                    percentage = (count / data['total']) * 100 if data['total'] > 0 else 0
                    print(f"     • {status}: {count} ({percentage:.1f}%)")

            if data['by_result']:
                print(f"   Répartition par résultat:")
                for result, count in sorted(data['by_result'].items(), key=lambda x: (x[0] or '', x[1])):
                    percentage = (count / data['total']) * 100 if data['total'] > 0 else 0
                    print(f"     • {result}: {count} ({percentage:.1f}%)")
        else:
            report_data[year] = {
                'total_inscriptions': 0,
                'class_breakdown': {},
                'status_breakdown': {},
                'result_breakdown': {}
            }
            print(f"\n❌ {year}: Aucune donnée trouvée")

    # Overall statistics
    print(f"\n📈 STATISTIQUES GLOBALES:")
    print("-" * 60)

    total_all_years = sum(data['total'] for data in year_analysis.values())
    print(f"Total des inscriptions (toutes années): {total_all_years}")

    # Class distribution across all years
    all_classes = {}
    for year_data in year_analysis.values():
        for classe, count in year_data['by_class'].items():
            all_classes[classe] = all_classes.get(classe, 0) + count

    if all_classes:
        print(f"\n📚 Distribution par classe (toutes années):")
        for classe, count in sorted(all_classes.items(), key=lambda x: (x[0] or '', x[1])):
            percentage = (count / total_all_years) * 100 if total_all_years > 0 else 0
            print(f"   • {classe}: {count} ({percentage:.1f}%)")

    # Target years summary
    target_total = sum(report_data[year]['total_inscriptions'] for year in target_years if year in report_data)
    if target_total > 0:
        print(f"\n🎯 TOTAL POUR LES ANNÉES CIBLES (2023-2024 + 2024-2025): {target_total}")

        target_classes = {}
        for year in target_years:
            if year in report_data:
                for classe, count in report_data[year]['class_breakdown'].items():
                    target_classes[classe] = target_classes.get(classe, 0) + count

        if target_classes:
            print(f"\n📊 Distribution par classe (années cibles):")
            for classe, count in sorted(target_classes.items(), key=lambda x: (x[0] or '', x[1])):
                percentage = (count / target_total) * 100
                print(f"   • {classe}: {count} ({percentage:.1f}%)")

    return report_data

def main():
    """Main function"""
    try:
        print("🔍 Démarrage de l'analyse complète...")
        year_analysis, inscriptions = analyze_with_class_information()
        report_data = generate_final_report(year_analysis, inscriptions)

        # Save comprehensive results
        results = {
            "year_analysis": year_analysis,
            "target_years_report": report_data,
            "total_inscriptions_analyzed": len(inscriptions),
            "analysis_date": datetime.now().isoformat()
        }

        with open('final_catechumen_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Rapport complet sauvegardé dans 'final_catechumen_statistics.json'")

        # Create a clean summary for presentation
        summary = {
            "title": "Statistiques des Catéchumènes par Classe",
            "period": "2023-2024 et 2024-2025",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "findings": {
                "total_target_years": sum(report_data[year]['total_inscriptions'] for year in ["2023-2024", "2024-2025"]),
                "years_with_data": [year for year in ["2023-2024", "2024-2025"] if report_data[year]['total_inscriptions'] > 0],
                "total_classes_found": len(set().union(*(data['class_breakdown'].keys() for data in report_data.values()))),
            },
            "yearly_breakdown": report_data
        }

        with open('presentation_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n📋 Résumé pour présentation sauvegardé dans 'presentation_summary.json'")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()