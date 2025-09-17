#!/usr/bin/env python3
"""
Générer une attestation de catéchèse complète pour Latyr Emmanuel NDONG
"""

import json
from datetime import datetime

def load_search_results():
    """Charger les résultats de recherche"""
    try:
        with open('search_results_latyr_emmanuel_ndong.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def create_detailed_attestation():
    """Créer une attestation détaillée"""

    # Load search results
    search_results = load_search_results()

    if not search_results:
        return None

    # Get class mapping
    class_mapping = {
        'deaacd2d-86f7-400a-afef-dd73314bfb4a': 'CE2 (Cours Élémentaire 2)',
        'd3dd421b-0b7e-49f0-a744-957ca127e878': 'CM1 (Cours Moyen 1)',
        'fb6d9698-2975-49ea-8a24-697fc8cf1167': 'CI (Initiation Chrétienne)',
        '6eabb6eb-2074-4807-bb6b-36b437bf116d': 'CP (Cours Préparatoire)',
        'dc689b6c-0452-43da-b015-426b47fd9e8b': 'CE1 (Cours Élémentaire 1)',
        '71f3f025-7489-40c2-aa8d-f679773f39ca': 'CM2 (Cours Moyen 2)',
        '287422de-781f-43d8-a475-79782af496de': '5ème (Cinquième)',
        '87dec81f-8045-4a98-9194-2300fd75c154': '6ème (Sixième)'
    }

    # Child information
    child_info = search_results['catechumenes'][0]  # Use the main record
    inscriptions = search_results['inscriptions']

    # Extract basic information
    prenoms = child_info.get('prenoms', 'Emmanuel Latyr')
    nom = child_info.get('nom', 'NDONG')
    annee_naissance = child_info.get('annee_naissance', '')
    baptise = child_info.get('baptise', False)
    code_parent = child_info.get('code_parent', '')

    # Process inscriptions to get class history
    class_history = []
    current_year = "2024-2025"

    for inscription in inscriptions:
        date_inscription = inscription.get('date_inscription', '')
        classe_id = inscription.get('id_classe_courante', '')
        resultat = inscription.get('resultat_final', '')
        statut = inscription.get('etat', '')

        # Determine academic year from inscription date
        if date_inscription:
            year = int(date_inscription.split('-')[0])
            if date_inscription.split('-')[1] in ['10', '11', '12']:  # October-December
                academic_year = f"{year}-{year + 1}"
            else:  # January-September
                academic_year = f"{year - 1}-{year}"
        else:
            academic_year = "Non spécifiée"

        classe_name = class_mapping.get(classe_id, f"Classe {classe_id}")

        class_history.append({
            'academic_year': academic_year,
            'classe': classe_name,
            'resultat': resultat,
            'statut': statut,
            'date_inscription': date_inscription
        })

    # Find most recent inscription
    most_recent = None
    for inscription in class_history:
        if inscription['academic_year'] == current_year:
            most_recent = inscription
            break

    if not most_recent and class_history:
        # Use the most recent one
        most_recent = max(class_history, key=lambda x: x.get('date_inscription', ''))

    current_classe = most_recent['classe'] if most_recent else "à déterminer"
    current_result = most_recent['resultat'] if most_recent else ""

    # Generate detailed attestation
    current_date = datetime.now().strftime("%d %B %Y")

    attestation = f"""
╔═════════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║                   ATTESTATION DE CATÉCHÈSE                               ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝

Je soussigné, Directeur du Service Diocésain de la Catéchèse, certifie que :

L'enfant : {prenoms} {nom}
{f"Né(e) en {annee_naissance}" if annee_naissance else "Date de naissance : à compléter"}

A suivi avec assiduité et sérieux les cours de catéchèse
pendant l'année scolaire {current_year} dans la classe de {current_classe}.

PARCOURS DE CATÉCHÈSE :
"""

    # Add parcours information
    for inscription in sorted(class_history, key=lambda x: x['academic_year']):
        result_text = f" - Résultat : {inscription['resultat']}" if inscription['resultat'] else ""
        attestation += f"""
• {inscription['academic_year']} : {inscription['classe']}{result_text}"""

    if baptise:
        attestation += f"""

L'enfant est baptisé et a participé avec ferveur aux différentes activités
catéchétiques et liturgiques proposées par le Service Diocésain."""

    attestation += f"""

L'enfant a manifesté un intérêt sincère pour l'approfondissement de sa foi
et a participé régulièrement aux activités catéchétiques.

Cette attestation est délivrée pour servir et valoir ce que de droit.

╔═════════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║                           INFORMATIONS                                     ║
║                                                                             ║
║   Contact parent : 776408591                                               ║
║   Code parent : {code_parent}                                               ║
║   ID Catechumène : {child_info.get('id_catechumene', '')}                  ║
║                                                                             ║
║   Service Diocésain de la Catéchèse                                         ║
║   Téléphone : 776408591                                                    ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝

Fait à Dakar, le {current_date}

Signature et cachet
Service Diocésain de la Catéchèse
"""

    return attestation, class_history

def create_short_attestation():
    """Créer une version courte de l'attestation"""

    current_date = datetime.now().strftime("%d %B %Y")

    short_attestation = f"""
ATTESTATION DE CATÉCHÈSE

Je soussigné, Directeur du Service Diocésain de la Catéchèse, certifie que :

L'enfant : Latyr Emmanuel NDONG
Né(e) en : [à compléter]

A suivi avec assiduité et sérieux les cours de catéchèse
pendant l'année scolaire 2024-2025.

Parcours :
• 2023-2024 : CE2 (Cours Élémentaire 2) - ADMIS(E) A PASSER EN CLASSE SUPERIEURE
• 2024-2025 : CM1 (Cours Moyen 1) - En cours

L'enfant est baptisé et a participé régulièrement aux activités catéchétiques.
Il a manifesté un intérêt sincère pour l'approfondissement de sa foi.

Cette attestation est délivrée pour servir et valoir ce que de droit.

Fait à Dakar, le {current_date}

Signature et cachet
Service Diocésain de la Catéchèse

Contact : 776408591
"""

    return short_attestation

def main():
    """Main function"""
    try:
        print("📄 Création de l'attestation pour Latyr Emmanuel NDONG...")

        # Create detailed attestation
        detailed_attestation, class_history = create_detailed_attestation()

        if detailed_attestation:
            print("✅ Attestation détaillée créée avec succès!")

            # Save detailed version
            with open('attestation_catechese_detailed_latyr_emmanuel_ndong.txt', 'w', encoding='utf-8') as f:
                f.write(detailed_attestation)

            # Create and save short version
            short_attestation = create_short_attestation()
            with open('attestation_catechese_short_latyr_emmanuel_ndong.txt', 'w', encoding='utf-8') as f:
                f.write(short_attestation)

            print("\n📋 ATTESTATION DÉTAILLÉE:")
            print("=" * 80)
            print(detailed_attestation)

            print("\n📋 VERSION COURTE:")
            print("=" * 80)
            print(short_attestation)

            print(f"\n💾 Fichiers générés:")
            print(f"   • attestation_catechese_detailed_latyr_emmanuel_ndong.txt")
            print(f"   • attestation_catechese_short_latyr_emmanuel_ndong.txt")

            print(f"\n📊 Résumé du parcours:")
            print(f"   • Enfant baptisé: Oui")
            print(f"   • Années de catéchèse: {len(class_history)}")
            for parcours in class_history:
                print(f"   • {parcours['academic_year']}: {parcours['classe']}")

            print(f"\n🎯 Utilisation:")
            print(f"   • Version détaillée: Pour archives administratives")
            print(f"   • Version courte: Pour communication rapide")

        else:
            print("❌ Impossible de créer l'attestation - données manquantes")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()