#!/usr/bin/env python3
"""
Rechercher les informations d'un enfant dans la base de données Supabase
"""

import os
import json
from supabase import create_client

# Set up environment
os.environ['SUPABASE_URL'] = 'https://ixzpejqzxvxpnkbznqnj.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml4enBlanF6eHZ4cG5rYnpucW5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzcwODUyOCwiZXhwIjoyMDczMjg0NTI4fQ.Jki6OqWq0f1Svd2u2m8Zt3xbust-fSlRlSMcWvnsOz4'

def connect_to_supabase():
    """Connect to Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    return create_client(supabase_url, supabase_key)

def search_child_info():
    """Rechercher les informations de Latyr Emmanuel NDONG"""

    supabase = connect_to_supabase()

    # Search in catechumenes table
    print("🔍 Recherche dans la table catechumenes...")
    catechumenes_response = supabase.table('catechumenes').select('*').ilike('nom', '%NDONG%').ilike('prenoms', '%Emmanuel%').execute()

    # Search in inscriptions table
    print("📝 Recherche dans la table inscriptions...")
    inscriptions_response = supabase.table('inscriptions').select('*').ilike('nom', '%NDONG%').ilike('prenoms', '%Emmanuel%').execute()

    # Search by parent phone number
    print("📱 Recherche par numéro de parent...")
    parent_search = supabase.table('catechumenes').select('*').eq('code_parent', '776408591').execute()

    print(f"\n📊 Résultats de la recherche:")
    print("=" * 60)

    # Display catechumenes results
    if catechumenes_response.data:
        print(f"\n👥 Trouvé {len(catechumenes_response.data)} résultat(s) dans catechumenes:")
        for i, child in enumerate(catechumenes_response.data, 1):
            print(f"\n{i}. {child.get('prenoms', '')} {child.get('nom', '')}")
            print(f"   ID: {child.get('id_catechumene', 'N/A')}")
            print(f"   Année de naissance: {child.get('annee_naissance', 'N/A')}")
            print(f"   Baptisé: {'Oui' if child.get('baptise', False) else 'Non'}")
            print(f"   Code parent: {child.get('code_parent', 'N/A')}")
            print(f"   Date de création: {child.get('created_at', 'N/A')}")

    # Display inscriptions results
    if inscriptions_response.data:
        print(f"\n📝 Trouvé {len(inscriptions_response.data)} résultat(s) dans inscriptions:")
        for i, inscription in enumerate(inscriptions_response.data, 1):
            print(f"\n{i}. {inscription.get('prenoms', '')} {inscription.get('nom', '')}")
            print(f"   ID: {inscription.get('id_inscription', 'N/A')}")
            print(f"   Date d'inscription: {inscription.get('date_inscription', 'N/A')}")
            print(f"   Classe: {inscription.get('id_classe_courante', 'N/A')}")
            print(f"   Résultat final: {inscription.get('resultat_final', 'N/A')}")
            print(f"   Statut: {inscription.get('etat', 'N/A')}")

    # Display parent search results
    if parent_search.data:
        print(f"\n📱 Trouvé {len(parent_search.data)} résultat(s) par numéro de parent:")
        for i, child in enumerate(parent_search.data, 1):
            print(f"\n{i}. {child.get('prenoms', '')} {child.get('nom', '')}")
            print(f"   ID: {child.get('id_catechumene', 'N/A')}")
            print(f"   Année de naissance: {child.get('annee_naissance', 'N/A')}")
            print(f"   Code parent: {child.get('code_parent', 'N/A')}")

    # Compile all results
    all_results = {
        'catechumenes': catechumenes_response.data,
        'inscriptions': inscriptions_response.data,
        'parent_search': parent_search.data
    }

    # Find the most likely match for Latyr Emmanuel NDONG
    best_match = None
    best_score = 0

    # Check catechumenes
    for child in catechumenes_response.data:
        nom = child.get('nom', '').upper()
        prenoms = child.get('prenoms', '').upper()
        score = 0

        if 'NDONG' in nom:
            score += 2
        if 'EMMANUEL' in prenoms:
            score += 2
        if 'LATYR' in prenoms:
            score += 1

        if score > best_score:
            best_score = score
            best_match = {
                'source': 'catechumenes',
                'data': child,
                'score': score
            }

    # Check inscriptions
    for inscription in inscriptions_response.data:
        nom = inscription.get('nom', '').upper()
        prenoms = inscription.get('prenoms', '').upper()
        score = 0

        if 'NDONG' in nom:
            score += 2
        if 'EMMANUEL' in prenoms:
            score += 2
        if 'LATYR' in prenoms:
            score += 1

        if score > best_score:
            best_score = score
            best_match = {
                'source': 'inscriptions',
                'data': inscription,
                'score': score
            }

    print(f"\n🎯 Meilleure correspondance trouvée (score: {best_score}):")
    if best_match:
        data = best_match['data']
        print(f"   Source: {best_match['source']}")
        print(f"   Nom: {data.get('nom', '')}")
        print(f"   Prénoms: {data.get('prenoms', '')}")
        print(f"   ID: {data.get('id_catechumene', data.get('id_inscription', 'N/A'))}")

        # Get additional information
        if best_match['source'] == 'catechumenes':
            print(f"   Année de naissance: {data.get('annee_naissance', 'N/A')}")
            print(f"   Baptisé: {'Oui' if data.get('baptise', False) else 'Non'}")
            print(f"   Code parent: {data.get('code_parent', 'N/A')}")
        else:
            print(f"   Date d'inscription: {data.get('date_inscription', 'N/A')}")
            print(f"   Résultat final: {data.get('resultat_final', 'N/A')}")
            print(f"   Statut: {data.get('etat', 'N/A')}")
    else:
        print("   Aucune correspondance trouvée")

    return all_results, best_match

def generate_attestation_content(child_info, parent_phone):
    """Générer le contenu de l'attestation"""

    if not child_info:
        return None

    data = child_info['data']
    source = child_info['source']

    # Extract information
    nom = data.get('nom', 'NDONG')
    prenoms = data.get('prenoms', 'Emmanuel Latyr')
    annee_naissance = data.get('annee_naissance', 'à compléter')

    # Determine academic year and class
    current_date = "14 septembre 2025"
    current_year = "2024-2025"

    # Try to get class information
    classe = "à déterminer"
    if source == 'inscriptions':
        id_classe = data.get('id_classe_courante')
        if id_classe:
            # You could look up the class name here
            classe = f"Classe ID: {id_classe}"

    # Generate attestation content
    attestation = f"""
ATTESTATION DE CATÉCHÈSE

Je soussigné, Directeur du Service Diocésain de la Catéchèse, certifie que :

L'enfant : {prenoms} {nom}
Né(e) en : {annee_naissance}

A suivi avec assiduité et sérieux les cours de catéchèse
pendant l'année scolaire {current_year} dans la classe de {classe}.

A participé régulièrement aux activités catéchétiques
et a manifesté un intérêt sincère pour l'approfondissement de sa foi.

Cette attestation est délivrée pour servir et valoir ce que de droit.

Fait à Dakar, le {current_date}

Signature et cachet
Service Diocésain de la Catéchèse

Contact : 776408591
"""

    return attestation

def main():
    """Main function"""
    try:
        print("🔍 Recherche des informations de Latyr Emmanuel NDONG...")
        all_results, best_match = search_child_info()

        if best_match and best_match['score'] >= 3:  # Good match threshold
            print(f"\n✅ Correspondance trouvée avec confiance!")
            print(f"\n📄 Génération de l'attestation...")

            attestation_content = generate_attestation_content(best_match, '776408591')

            print(f"\n📋 CONTENU DE L'ATTESTATION:")
            print("=" * 60)
            print(attestation_content)

            # Save to file
            with open('attestation_catechese_latyr_emmanuel_ndong.txt', 'w', encoding='utf-8') as f:
                f.write(attestation_content)

            print(f"\n💾 Attestation sauvegardée dans 'attestation_catechese_latyr_emmanuel_ndong.txt'")

        else:
            print(f"\n❌ Aucune correspondance fiable trouvée pour Latyr Emmanuel NDONG")
            print(f"   Score de correspondance: {best_match['score'] if best_match else 0}")
            print(f"   Veuillez vérifier les informations ou ajouter l'enfant à la base de données")

        # Save search results
        with open('search_results_latyr_emmanuel_ndong.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print(f"\n📊 Résultats de recherche sauvegardés dans 'search_results_latyr_emmanuel_ndong.json'")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()