#!/usr/bin/env python3
"""
Create Missing Classes in Supabase
"""

import sys
from supabase_config import get_supabase_client

def create_missing_classes():
    """Create the missing classes identified in the analysis"""
    print("🏫 Creating missing classes in Supabase...")
    
    try:
        supabase = get_supabase_client()
        
        # Classes to create based on analysis
        new_classes = [
            {
                'classe_nom': '1ère Année Persévérance',
                'description': 'Première année de persévérance',
                'niveau': 'Persévérance'
            },
            {
                'classe_nom': '2ème Année Persévérance', 
                'description': 'Deuxième année de persévérance',
                'niveau': 'Persévérance'
            },
            {
                'classe_nom': '1ère Année Catéchisme des Adultes',
                'description': 'Première année de catéchisme pour adultes',
                'niveau': 'Adultes'
            },
            {
                'classe_nom': '2ème Année Catéchisme des Adultes',
                'description': 'Deuxième année de catéchisme pour adultes', 
                'niveau': 'Adultes'
            },
            {
                'classe_nom': '3ème Année Catéchisme des Adultes',
                'description': 'Troisième année de catéchisme pour adultes',
                'niveau': 'Adultes'
            }
        ]
        
        created_classes = []
        
        for class_data in new_classes:
            print(f"📝 Creating class: {class_data['classe_nom']}")
            
            try:
                result = supabase.table('classes').insert(class_data).execute()
                
                if result.data:
                    created_classes.append(class_data['classe_nom'])
                    print(f"✅ Successfully created: {class_data['classe_nom']}")
                else:
                    print(f"❌ Failed to create: {class_data['classe_nom']}")
                    
            except Exception as e:
                # Check if class already exists
                error_msg = str(e)
                if 'duplicate key' in error_msg.lower():
                    print(f"⚠️  Class already exists: {class_data['classe_nom']}")
                    created_classes.append(class_data['classe_nom'])
                else:
                    print(f"❌ Error creating {class_data['classe_nom']}: {e}")
        
        print(f"\n🎉 Created {len(created_classes)} new classes:")
        for cls in created_classes:
            print(f"  - {cls}")
        
        return len(created_classes) > 0
        
    except Exception as e:
        print(f"❌ Error creating classes: {e}")
        return False

def verify_classes():
    """Verify all expected classes exist"""
    print("\n🔍 Verifying classes...")
    
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('classes').select('*').order('classe_nom').execute()
        
        if result.data:
            print(f"📊 Total classes in Supabase: {len(result.data)}")
            print("\n📋 Current classes:")
            for cls in result.data:
                print(f"  - {cls['classe_nom']} ({cls['niveau']})")
            
            # Check for our new classes
            expected_new_classes = [
                '1ère Année Persévérance',
                '2ème Année Persévérance', 
                '1ère Année Catéchisme des Adultes',
                '2ème Année Catéchisme des Adultes',
                '3ème Année Catéchisme des Adultes'
            ]
            
            found_classes = []
            for expected in expected_new_classes:
                found = any(cls['classe_nom'] == expected for cls in result.data)
                if found:
                    found_classes.append(expected)
            
            print(f"\n✅ Found {len(found_classes)}/{len(expected_new_classes)} new classes")
            return len(found_classes) == len(expected_new_classes)
        
        return False
        
    except Exception as e:
        print(f"❌ Error verifying classes: {e}")
        return False

if __name__ == "__main__":
    print("🏗️  Creating Missing Classes for SDB Migration")
    print("=" * 60)
    
    success = create_missing_classes()
    
    if success:
        verify_success = verify_classes()
        if verify_success:
            print("\n🎉 All missing classes created successfully!")
        else:
            print("\n⚠️  Some classes may not have been created properly")
    else:
        print("\n❌ Failed to create missing classes")
    
    sys.exit(0 if success else 1)