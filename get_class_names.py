#!/usr/bin/env python3<arg_value>
import os
import json
from supabase import create_client

# Set up environment
os.environ['SUPABASE_URL'] = 'https://ixzpejqzxvxpnkbznqnj.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml4enBlanF6eHZ4cG5rYnpucW5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzcwODUyOCwiZXhwIjoyMDczMjg0NTI4fQ.Jki6OqWq0f1Svd2u2m8Zt3xbust-fSlRlSMcWvnsOz4'

def main():
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

    # Get all classes
    classes_response = supabase.table('classes').select('*').execute()
    classes = {c['id']: c for c in classes_response.data}

    print("📚 Available Classes:")
    print("-" * 50)
    for class_id, class_info in classes.items():
        name = class_info.get('nom') or class_info.get('nom_classe') or 'Unnamed'
        niveau = class_info.get('niveau', '')
        print(f"{class_id}: {name} ({niveau})")

    # Save mapping
    class_mapping = {}
    for class_id, class_info in classes.items():
        name = class_info.get('nom') or class_info.get('nom_classe') or f"Class {class_id}"
        niveau = class_info.get('niveau', '')
        class_mapping[class_id] = f"{name} ({niveau})" if niveau else name

    with open('class_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(class_mapping, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Class mapping saved to class_mapping.json")

if __name__ == "__main__":
    main()