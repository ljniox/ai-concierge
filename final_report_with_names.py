#!/usr/bin/env python3
"""
Generate final report with proper class names
"""

import json
from datetime import datetime

def load_class_mapping():
    """Load class mapping from file"""
    try:
        with open('class_mapping.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def load_statistics():
    """Load statistics from file"""
    try:
        with open('final_catechumen_statistics.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def generate_readable_report():
    """Generate human-readable report"""

    class_mapping = load_class_mapping()
    stats = load_statistics()

    if not stats:
        print("❌ No statistics data found")
        return

    year_analysis = stats.get('year_analysis', {})
    target_years_report = stats.get('target_years_report', {})

    print("\n" + "="*80)
    print("📊 RAPPORT FINAL DES STATISTIQUES DES CATÉCHUMÈNES")
    print("="*80)
    print(f"📅 Période d'analyse: 2023-2024 et 2024-2025")
    print(f"🕒 Date du rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Summary
    total_target = sum(target_years_report[year]['total_inscriptions'] for year in ['2023-2024', '2024-2025'])
    print(f"\n📈 RÉSUMÉ GÉNÉRAL:")
    print(f"   Total des inscriptions (2023-2024 + 2024-2025): {total_target}")
    print(f"   Nombre total de classes: {len(set().union(*(data['class_breakdown'].keys() for data in target_years_report.values())))}")

    # Year by year analysis
    print(f"\n🎓 ANALYSE PAR ANNÉE SCOLAIRE:")
    print("-" * 60)

    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report and target_years_report[year]['total_inscriptions'] > 0:
            data = target_years_report[year]
            print(f"\n📊 {year}:")
            print(f"   Total des inscriptions: {data['total_inscriptions']}")

            # Class breakdown with readable names
            if data['class_breakdown']:
                print(f"   Répartition par classe:")
                for class_id, count in sorted(data['class_breakdown'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / data['total_inscriptions']) * 100
                    class_name = class_mapping.get(class_id, class_id)
                    if class_id == 'Non spécifiée':
                        class_name = 'Non spécifiée'
                    print(f"     • {class_name}: {count} ({percentage:.1f}%)")

            # Status breakdown
            if data['status_breakdown']:
                print(f"   Répartition par statut:")
                for status, count in sorted(data['status_breakdown'].items(), key=lambda x: (x[0] or '', x[1]), reverse=True):
                    percentage = (count / data['total_inscriptions']) * 100
                    status_name = status or 'Non spécifié'
                    print(f"     • {status_name}: {count} ({percentage:.1f}%)")

    # Combined analysis for target years
    print(f"\n📊 STATISTIQUES COMBINÉES (2023-2024 + 2024-2025):")
    print("-" * 60)

    combined_classes = {}
    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report:
            for class_id, count in target_years_report[year]['class_breakdown'].items():
                combined_classes[class_id] = combined_classes.get(class_id, 0) + count

    print(f"\n📚 Répartition combinée par classe:")
    for class_id, total_count in sorted(combined_classes.items(), key=lambda x: x[1], reverse=True):
        percentage = (total_count / total_target) * 100
        class_name = class_mapping.get(class_id, class_id)
        if class_id == 'Non spécifiée':
            class_name = 'Non spécifiée'
        print(f"   • {class_name}: {total_count} ({percentage:.1f}%)")

    # Key insights
    print(f"\n🔍 PRINCIPALES OBSERVATIONS:")
    print("-" * 60)

    # Find most popular classes
    most_popular = sorted(combined_classes.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"   Classes les plus populaires:")
    for class_id, count in most_popular:
        if class_id != 'Non spécifiée':
            class_name = class_mapping.get(class_id, class_id)
            percentage = (count / total_target) * 100
            print(f"     • {class_name}: {count} inscriptions ({percentage:.1f}%)")

    # Year-over-year growth
    if '2023-2024' in target_years_report and '2024-2025' in target_years_report:
        year_2023_2024 = target_years_report['2023-2024']['total_inscriptions']
        year_2024_2025 = target_years_report['2024-2025']['total_inscriptions']
        if year_2023_2024 > 0:
            growth_rate = ((year_2024_2025 - year_2023_2024) / year_2023_2024) * 100
            print(f"\n   Croissance d'une année à l'autre:")
            print(f"     • 2023-2024: {year_2023_2024} inscriptions")
            print(f"     • 2024-2025: {year_2024_2025} inscriptions")
            print(f"     • Taux de croissance: {growth_rate:+.1f}%")

    # Success rate (based on results)
    print(f"\n   Taux de réussite (basé sur les résultats finaux):")
    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report and target_years_report[year]['result_breakdown']:
            results = target_years_report[year]['result_breakdown']
            total_results = sum(count for status, count in results.items() if status and count)
            admitted = sum(count for status, count in results.items() if status and 'ADMIS' in status.upper())
            if total_results > 0:
                success_rate = (admitted / total_results) * 100
                print(f"     • {year}: {success_rate:.1f}% de réussite")

    # Save readable report
    readable_report = {
        "title": "Rapport des Statistiques des Catéchumènes",
        "period": "2023-2024 et 2024-2025",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_inscriptions": total_target,
            "years_analyzed": ["2023-2024", "2024-2025"],
            "total_classes": len(combined_classes)
        },
        "yearly_breakdown": target_years_report,
        "combined_analysis": {
            "class_distribution": combined_classes,
            "most_popular_classes": most_popular[:3]
        }
    }

    with open('readable_report.json', 'w', encoding='utf-8') as f:
        json.dump(readable_report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Rapport lisible sauvegardé dans 'readable_report.json'")

def create_presentation_format():
    """Create a presentation-friendly format"""

    stats = load_statistics()
    if not stats:
        return

    target_years_report = stats.get('target_years_report', {})
    class_mapping = load_class_mapping()

    total_target = sum(target_years_report[year]['total_inscriptions'] for year in ['2023-2024', '2024-2025'])

    # Combined class distribution
    combined_classes = {}
    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report:
            for class_id, count in target_years_report[year]['class_breakdown'].items():
                combined_classes[class_id] = combined_classes.get(class_id, 0) + count

    # Create presentation slides
    presentation = {
        "title": "Statistiques des Catéchumènes 2023-2025",
        "slides": [
            {
                "title": "Résumé Global",
                "content": [
                    f"Total des inscriptions: {total_target}",
                    f"Période: 2023-2024 et 2024-2025",
                    f"Nombre de classes: {len([c for c in combined_classes.keys() if c != 'Non spécifiée'])}"
                ]
            },
            {
                "title": "Répartition par Année",
                "content": [
                    f"2023-2024: {target_years_report.get('2023-2024', {}).get('total_inscriptions', 0)} inscriptions",
                    f"2024-2025: {target_years_report.get('2024-2025', {}).get('total_inscriptions', 0)} inscriptions"
                ]
            },
            {
                "title": "Top 5 des Classes",
                "content": []
            }
        ]
    }

    # Add top 5 classes
    top_classes = sorted(combined_classes.items(), key=lambda x: x[1], reverse=True)[:5]
    for class_id, count in top_classes:
        if class_id != 'Non spécifiée':
            class_name = class_mapping.get(class_id, class_id)
            percentage = (count / total_target) * 100
            presentation["slides"][2]["content"].append(f"{class_name}: {count} ({percentage:.0f}%)")

    # Year-by-year breakdown
    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report and target_years_report[year]['total_inscriptions'] > 0:
            year_slide = {
                "title": f"Détail {year}",
                "content": [
                    f"Total: {target_years_report[year]['total_inscriptions']} inscriptions"
                ]
            }

            # Add top classes for this year
            year_classes = target_years_report[year]['class_breakdown']
            top_year_classes = sorted(year_classes.items(), key=lambda x: x[1], reverse=True)[:3]
            for class_id, count in top_year_classes:
                if class_id != 'Non spécifiée':
                    class_name = class_mapping.get(class_id, class_id)
                    percentage = (count / target_years_report[year]['total_inscriptions']) * 100
                    year_slide["content"].append(f"{class_name}: {count} ({percentage:.0f}%)")

            presentation["slides"].append(year_slide)

    with open('presentation_format.json', 'w', encoding='utf-8') as f:
        json.dump(presentation, f, indent=2, ensure_ascii=False)

    print(f"📊 Format présentation sauvegardé dans 'presentation_format.json'")

def main():
    """Main function"""
    try:
        generate_readable_report()
        create_presentation_format()

        print(f"\n✅ Analyse terminée avec succès!")
        print(f"\n📁 Fichiers générés:")
        print(f"   • readable_report.json - Rapport détaillé")
        print(f"   • presentation_format.json - Format pour présentation")
        print(f"   • final_catechumen_statistics.json - Données brutes")
        print(f"   • class_mapping.json - Correspondance des classes")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()