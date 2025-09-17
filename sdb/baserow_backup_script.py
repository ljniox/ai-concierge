#!/usr/bin/env python3
"""
Backup Baserow Tables to CSV
"""

import os
import sys
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_baserow_table(table_id, table_name):
    """Fetch all rows from a Baserow table"""
    try:
        print(f"📤 Fetching {table_name} from Baserow...")
        
        BASEROW_URL = os.getenv("BASEROW_URL")
        BASEROW_AUTH_KEY = os.getenv("BASEROW_AUTH_KEY")
        
        if not BASEROW_URL or not BASEROW_AUTH_KEY:
            print(f"❌ Missing Baserow configuration for {table_name}")
            return None
        
        headers = {
            "Authorization": f"Token {BASEROW_AUTH_KEY}"
        }
        
        all_rows = []
        page = 1
        
        while True:
            url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/?user_field_names=true&page={page}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Error fetching {table_name}: {response.status_code}")
                return None
            
            data = response.json()
            all_rows.extend(data['results'])
            
            if not data['next']:
                break
                
            page += 1
        
        print(f"✅ Fetched {len(all_rows)} rows from {table_name}")
        return all_rows
        
    except Exception as e:
        print(f"❌ Error fetching {table_name}: {e}")
        return None

def save_to_csv(data, filename, table_name):
    """Save data to CSV file"""
    try:
        if not data:
            print(f"⚠️  No data to save for {table_name}")
            return False
        
        print(f"💾 Saving {table_name} to {filename}...")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if data:
                # Get all unique field names from all rows
                fieldnames = set()
                for row in data:
                    fieldnames.update(row.keys())
                fieldnames = sorted(list(fieldnames))
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Handle nested data (like ID_AnneeInscription)
                for row in data:
                    cleaned_row = {}
                    for key, value in row.items():
                        if isinstance(value, list) and len(value) > 0:
                            # Handle select fields
                            if isinstance(value[0], dict) and 'value' in value[0]:
                                cleaned_row[key] = value[0]['value']
                            else:
                                cleaned_row[key] = str(value)
                        elif isinstance(value, list):
                            cleaned_row[key] = ''
                        else:
                            cleaned_row[key] = value
                    writer.writerow(cleaned_row)
        
        print(f"✅ Saved {len(data)} records to {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving {table_name}: {e}")
        return False

def create_baserow_backup():
    """Create backup of Baserow tables"""
    print("💾 Creating backup of Baserow data...")
    print("=" * 50)
    
    # Create backup directory
    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Baserow tables to backup (table_id, table_name)
    tables = [
        (574, "inscriptions"),
        (575, "catechumenes"),
        (577, "classes"),
        (578, "annees_scolaires"),
        (579, "paroisses")
    ]
    
    csv_files = []
    
    for table_id, table_name in tables:
        try:
            # Fetch data from Baserow
            data = fetch_baserow_table(table_id, table_name)
            
            if data:
                # Save to CSV
                filename = f"{backup_dir}/baserow_{table_name}.csv"
                if save_to_csv(data, filename, table_name):
                    csv_files.append(filename)
        except Exception as e:
            print(f"❌ Failed to backup {table_name}: {e}")
            continue
    
    print(f"\n📊 Baserow backup completed!")
    print(f"📁 Tables backed up: {len(csv_files)}")
    
    return csv_files

if __name__ == "__main__":
    csv_files = create_baserow_backup()
    sys.exit(0 if csv_files else 1)