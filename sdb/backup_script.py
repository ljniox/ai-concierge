#!/usr/bin/env python3
"""
Backup Supabase Tables to CSV and Create ZIP Archive
"""

import os
import sys
import csv
import zipfile
from datetime import datetime
from supabase_config import get_supabase_anon_client

def export_table_to_csv(supabase, table_name, filename):
    """Export a table to CSV file"""
    try:
        print(f"📤 Exporting {table_name}...")
        
        # Get all data from the table
        result = supabase.table(table_name).select('*').execute()
        
        if not result.data:
            print(f"⚠️  No data found in {table_name}")
            return False
        
        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if result.data:
                # Get column names from first row
                fieldnames = result.data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(result.data)
        
        print(f"✅ Exported {len(result.data)} records from {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting {table_name}: {e}")
        return False

def create_backup():
    """Create backup of all tables"""
    print("💾 Creating backup of Supabase data...")
    print("=" * 50)
    
    try:
        supabase = get_supabase_anon_client()
        
        # Create backup directory
        backup_dir = "backup"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Tables to backup
        tables = [
            'inscriptions',
            'catechumenes', 
            'classes',
            'annees_scolaires',
            'paroisses'
        ]
        
        csv_files = []
        
        # Export each table
        for table in tables:
            filename = f"{backup_dir}/{table}.csv"
            if export_table_to_csv(supabase, table, filename):
                csv_files.append(filename)
        
        # Create ZIP archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"supabase_backup_{timestamp}.zip"
        
        print(f"\n📦 Creating ZIP archive: {zip_filename}")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for csv_file in csv_files:
                zipf.write(csv_file, os.path.basename(csv_file))
        
        print(f"✅ Backup completed successfully!")
        print(f"📁 ZIP file: {zip_filename}")
        print(f"📊 Tables backed up: {len(csv_files)}")
        
        # Show file sizes
        zip_size = os.path.getsize(zip_filename)
        print(f"💾 Archive size: {zip_size:,} bytes ({zip_size/1024/1024:.1f} MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

if __name__ == "__main__":
    success = create_backup()
    sys.exit(0 if success else 1)