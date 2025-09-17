#!/usr/bin/env python3
"""
Create final readable report with proper class names
"""

import json
from datetime import datetime

def main():
    # Load data
    with open('class_mapping.json', 'r', encoding='utf-8') as f:
        class_mapping = json.load(f)

    with open('final_catechumen_statistics.json', 'r', encoding='utf-8') as f:
        stats = json.load(f)

    # Create readable class mapping
    readable_classes = {
        'fb6d9698-2975-49ea-8a24-697fc8cf1167': 'CI (Initiation Chrétienne)',
        '6eabb6eb-2074-4807-bb6b-36b437bf116d': 'CP (Cours Préparatoire)',
        'dc689b6c-0452-43da-b015-426b47fd9e8b': 'CE1 (Cours Élémentaire 1)',
        'deaacd2d-86f7-400a-afef-dd73314bfb4a': 'CE2 (Cours Élémentaire 2)',
        'd3dd421b-0b7e-49f0-a744-957ca127e878': 'CM1 (Cours Moyen 1)',
        '71f3f025-7489-40c2-aa8d-f679773f39ca': 'CM2 (Cours Moyen 2)',
        '287422de-781f-43d8-a475-79782af496de': '5ème (Cinquième)',
        '87dec81f-8045-4a98-9194-2300fd75c154': '6ème (Sixième)',
        '0e9984d4-d74c-4d8c-8b64-3128c5ca9fbf': 'Classe Non Spécifiée',
        '83d6c36e-fa16-41cd-a413-1736e93c797e': 'Persévérance',
        '51139cf4-48bf-42f9-9569-1cc962c57935': 'Persévérance',
        'b782acc5-cf44-4b64-beef-dc1ad4307421': 'Adultes',
        '853771f9-08aa-42b0-b1e6-8d50b0ad80f3': 'Adultes',
        '1f2003ff-c488-4ff7-a27a-8a0ce10caab4': 'Adultes',
        'Non spécifiée': 'Non spécifiée'
    }

    # Process the report data
    target_years_report = stats.get('target_years_report', {})

    # Create enhanced report with readable names
    enhanced_report = {
        "title": "Statistiques des Catéchumènes par Classe - Période 2023-2025",
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_inscriptions": sum(target_years_report[year]['total_inscriptions'] for year in ['2023-2024', '2024-2025']),
            "period": "2023-2024 et 2024-2025",
            "total_unique_classes": len(readable_classes) - 1  # Exclude 'Non spécifiée'
        },
        "yearly_breakdown": {}
    }

    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report:
            data = target_years_report[year]
            enhanced_report["yearly_breakdown"][year] = {
                "total_inscriptions": data['total_inscriptions'],
                "class_breakdown_readable": {},
                "status_breakdown": data['status_breakdown'],
                "result_breakdown": data['result_breakdown']
            }

            # Convert class IDs to readable names
            for class_id, count in data['class_breakdown'].items():
                readable_name = readable_classes.get(class_id, class_id)
                enhanced_report["yearly_breakdown"][year]["class_breakdown_readable"][readable_name] = count

    # Combined analysis
    combined_classes = {}
    for year in ['2023-2024', '2024-2025']:
        if year in target_years_report:
            for class_id, count in target_years_report[year]['class_breakdown'].items():
                readable_name = readable_classes.get(class_id, class_id)
                combined_classes[readable_name] = combined_classes.get(readable_name, 0) + count

    enhanced_report["combined_analysis"] = {
        "total_inscriptions": enhanced_report["summary"]["total_inscriptions"],
        "class_distribution": combined_classes
    }

    # Key insights
    enhanced_report["insights"] = {
        "most_popular_classes": sorted(combined_classes.items(), key=lambda x: x[1], reverse=True)[:5],
        "growth_analysis": {
            "2023-2024": target_years_report.get('2023-2024', {}).get('total_inscriptions', 0),
            "2024-2025": target_years_report.get('2024-2025', {}).get('total_inscriptions', 0),
            "growth_rate": ((target_years_report.get('2024-2025', {}).get('total_inscriptions', 0) -
                           target_years_report.get('2023-2024', {}).get('total_inscriptions', 0)) /
                          target_years_report.get('2023-2024', {}).get('total_inscriptions', 1) * 100)
        },
        "validation_rate": {
            "2023-2024": target_years_report.get('2023-2024', {}).get('status_breakdown', {}).get('Inscription Validée', 0) /
                          target_years_report.get('2023-2024', {}).get('total_inscriptions', 1) * 100,
            "2024-2025": target_years_report.get('2024-2025', {}).get('status_breakdown', {}).get('Inscription Validée', 0) /
                          target_years_report.get('2024-2025', {}).get('total_inscriptions', 1) * 100
        }
    }

    # Print final readable report
    print("\n" + "="*80)
    print("📊 STATISTIQUES DES CATÉCHUMÈNES PAR CLASSE")
    print("="*80)
    print(f"📅 Période: 2023-2024 et 2024-2025")
    print(f"🕒 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n📈 RÉSUMÉ:")
    print(f"   Total des inscriptions: {enhanced_report['summary']['total_inscriptions']}")
    print(f"   Croissance: {enhanced_report['insights']['growth_analysis']['growth_rate']:+.1f}%")
    print(f"   Taux de validation moyen: {(enhanced_report['insights']['validation_rate']['2023-2024'] + enhanced_report['insights']['validation_rate']['2024-2025'])/2:.1f}%")

    print(f"\n🎓 PAR ANNÉE:")
    for year in ['2023-2024', '2024-2025']:
        if year in enhanced_report['yearly_breakdown']:
            data = enhanced_report['yearly_breakdown'][year]
            print(f"\n   {year}: {data['total_inscriptions']} inscriptions")
            print(f"   Top 5 classes:")
            sorted_classes = sorted(data['class_breakdown_readable'].items(), key=lambda x: x[1], reverse=True)[:5]
            for class_name, count in sorted_classes:
                percentage = (count / data['total_inscriptions']) * 100
                print(f"     • {class_name}: {count} ({percentage:.1f}%)")

    print(f"\n🏆 CLASSES LES PLUS POPULAIRES (combinées):")
    for class_name, count in enhanced_report['insights']['most_popular_classes'][:5]:
        percentage = (count / enhanced_report['combined_analysis']['total_inscriptions']) * 100
        print(f"   • {class_name}: {count} ({percentage:.1f}%)")

    # Save the enhanced report
    with open('enhanced_catechumen_report.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_report, f, indent=2, ensure_ascii=False)

    # Create a markdown version for easy reading
    markdown_content = f"""# Statistiques des Catéchumènes par Classe

**Période d'analyse:** 2023-2024 et 2024-2025
**Date du rapport:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé Général

- **Total des inscriptions:** {enhanced_report['summary']['total_inscriptions']}
- **Croissance annuelle:** {enhanced_report['insights']['growth_analysis']['growth_rate']:+.1f}%
- **Nombre total de classes:** {enhanced_report['summary']['total_unique_classes']}

## Répartition par Année Scolaire

### 2023-2024
- **Total:** {enhanced_report['yearly_breakdown']['2023-2024']['total_inscriptions']} inscriptions
- **Taux de validation:** {enhanced_report['insights']['validation_rate']['2023-2024']:.1f}%

Principales classes:
"""
    for class_name, count in sorted(enhanced_report['yearly_breakdown']['2023-2024']['class_breakdown_readable'].items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / enhanced_report['yearly_breakdown']['2023-2024']['total_inscriptions']) * 100
        markdown_content += f"- {class_name}: {count} ({percentage:.1f}%)\n"

    markdown_content += f"""
### 2024-2025
- **Total:** {enhanced_report['yearly_breakdown']['2024-2025']['total_inscriptions']} inscriptions
- **Taux de validation:** {enhanced_report['insights']['validation_rate']['2024-2025']:.1f}%

Principales classes:
"""
    for class_name, count in sorted(enhanced_report['yearly_breakdown']['2024-2025']['class_breakdown_readable'].items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / enhanced_report['yearly_breakdown']['2024-2025']['total_inscriptions']) * 100
        markdown_content += f"- {class_name}: {count} ({percentage:.1f}%)\n"

    markdown_content += """
## Top 5 des Classes (Combiné)

"""
    for class_name, count in enhanced_report['insights']['most_popular_classes'][:5]:
        percentage = (count / enhanced_report['combined_analysis']['total_inscriptions']) * 100
        markdown_content += f"{count+1}. **{class_name}**: {count} inscriptions ({percentage:.1f}%)\n"

    with open('catechumen_statistics_report.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"\n💾 Fichiers générés:")
    print(f"   • enhanced_catechumen_report.json - Rapport JSON détaillé")
    print(f"   • catechumen_statistics_report.md - Rapport Markdown lisible")

if __name__ == "__main__":
    main()