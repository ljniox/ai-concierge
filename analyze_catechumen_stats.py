#!/usr/bin/env python3
"""
Script to analyze catechumen statistics by class for 2023-2024 and 2024-2025 academic years
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client
from typing import Dict, List, Any

# Load environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def connect_to_supabase() -> Client:
    """Connect to Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not found in environment variables")

    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_academic_year(enrollment_date: str) -> str:
    """Determine academic year from enrollment date"""
    if not enrollment_date:
        return "Unknown"

    try:
        # Parse date (assuming format YYYY-MM-DD or similar)
        if isinstance(enrollment_date, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    date_obj = datetime.strptime(enrollment_date.split('T')[0], '%Y-%m-%d')
                    year = date_obj.year
                    month = date_obj.month

                    # Academic year runs from September to August
                    if month >= 9:
                        return f"{year}-{year + 1}"
                    else:
                        return f"{year - 1}-{year}"
                except ValueError:
                    continue

        return "Unknown"
    except Exception as e:
        print(f"Error parsing date {enrollment_date}: {e}")
        return "Unknown"

def analyze_catechumen_data(supabase: Client) -> Dict[str, Any]:
    """Analyze catechumen data by academic year and class"""

    # First, let's examine the database schema
    print("🔍 Examining database schema...")

    # Get list of tables
    try:
        response = supabase.table('pg_tables').select('*').eq('schemaname', 'public').execute()
        tables = [table['tablename'] for table in response.data]
        print(f"Available tables: {tables}")
    except Exception as e:
        print(f"Error getting tables: {e}")
        # Try direct approach - look for common catechumen table names
        possible_tables = ['catechumenes', 'catechumens', 'students', 'eleves', 'inscriptions']
        tables = possible_tables

    results = {
        "by_academic_year": {},
        "by_class": {},
        "combined_stats": {}
    }

    # Try to find and query catechumen data
    catechumen_table = None
    for table in tables:
        if 'catechumene' in table.lower() or 'student' in table.lower() or 'eleve' in table.lower():
            catechumen_table = table
            break

    if not catechumen_table:
        # If no obvious table found, try common table names
        catechumen_table = 'catechumenes'  # Default based on the schema

    print(f"\n📊 Analyzing table: {catechumen_table}")

    try:
        # Get sample data to understand structure
        sample_response = supabase.table(catechumen_table).select('*').limit(5).execute()

        if sample_response.data:
            print(f"\n📋 Sample data structure:")
            sample_row = sample_response.data[0]
            print(f"Columns: {list(sample_row.keys())}")

            # Get all data
            all_data_response = supabase.table(catechumen_table).select('*').execute()
            catechumens = all_data_response.data

            print(f"\n📈 Total catechumens found: {len(catechumens)}")

            # Analyze by academic year
            for catechumen in catechumens:
                # Determine academic year
                enrollment_date = catechumen.get('date_inscription') or catechumen.get('created_at') or catechumen.get('inscription_date')
                academic_year = get_academic_year(enrollment_date)

                # Get class information
                class_info = catechumen.get('classe') or catechumen.get('niveau') or catechumen.get('class') or 'Unknown'

                if academic_year not in results["by_academic_year"]:
                    results["by_academic_year"][academic_year] = {}

                if class_info not in results["by_academic_year"][academic_year]:
                    results["by_academic_year"][academic_year][class_info] = 0

                results["by_academic_year"][academic_year][class_info] += 1

                # Also collect by class across all years
                if class_info not in results["by_class"]:
                    results["by_class"][class_info] = 0
                results["by_class"][class_info] += 1

            # Focus on the requested years
            target_years = ["2023-2024", "2024-2025"]
            for year in target_years:
                if year in results["by_academic_year"]:
                    results["combined_stats"][year] = {
                        "total": sum(results["by_academic_year"][year].values()),
                        "by_class": results["by_academic_year"][year],
                        "class_count": len(results["by_academic_year"][year])
                    }

        else:
            print(f"❌ No data found in table {catechumen_table}")

    except Exception as e:
        print(f"❌ Error analyzing catechumen data: {e}")
        print("Let's try to query using SQL...")

        # Fallback: Use raw SQL query
        try:
            sql_query = """
            SELECT
                CASE
                    WHEN EXTRACT(MONTH FROM created_at) >= 9 THEN
                        EXTRACT(YEAR FROM created_at) || '-' || (EXTRACT(YEAR FROM created_at) + 1)
                    ELSE
                        (EXTRACT(YEAR FROM created_at) - 1) || '-' || EXTRACT(YEAR FROM created_at)
                END as academic_year,
                classe,
                COUNT(*) as count
            FROM catechumenes
            WHERE created_at IS NOT NULL
            GROUP BY academic_year, classe
            ORDER BY academic_year, classe;
            """

            response = supabase.rpc('exec_sql', {'sql': sql_query}).execute()
            print(f"SQL Query result: {response}")

        except Exception as sql_error:
            print(f"❌ SQL query also failed: {sql_error}")

    return results

def print_statistics(results: Dict[str, Any]):
    """Print the analysis results"""

    print("\n" + "="*80)
    print("📊 CATECHUMEN STATISTICS BY CLASS")
    print("="*80)

    # Print by academic year
    print("\n📅 STATISTICS BY ACADEMIC YEAR:")
    print("-" * 60)

    target_years = ["2023-2024", "2024-2025"]
    for year in target_years:
        if year in results.get("combined_stats", {}):
            stats = results["combined_stats"][year]
            print(f"\n🎓 {year} Academic Year:")
            print(f"   Total Catechumens: {stats['total']}")
            print(f"   Number of Classes: {stats['class_count']}")
            print(f"   Breakdown by Class:")

            for class_name, count in sorted(stats["by_class"].items()):
                percentage = (count / stats['total']) * 100 if stats['total'] > 0 else 0
                print(f"     • {class_name}: {count} ({percentage:.1f}%)")
        else:
            print(f"\n❌ No data found for {year}")

    # Print overall statistics
    print("\n📈 OVERALL STATISTICS:")
    print("-" * 60)

    if results.get("by_class"):
        total_all_years = sum(results["by_class"].values())
        print(f"Total Catechumens (All Years): {total_all_years}")
        print(f"Total Classes: {len(results['by_class'])}")
        print(f"\nClass Distribution (All Years):")

        for class_name, count in sorted(results["by_class"].items()):
            percentage = (count / total_all_years) * 100 if total_all_years > 0 else 0
            print(f"  • {class_name}: {count} ({percentage:.1f}%)")

    # Print detailed breakdown for both years
    print("\n📋 DETAILED BREAKDOWN:")
    print("-" * 60)

    for year in ["2023-2024", "2024-2025"]:
        if year in results.get("by_academic_year", {}):
            print(f"\n{year}:")
            for class_name, count in sorted(results["by_academic_year"][year].items()):
                print(f"  {class_name}: {count}")

def main():
    """Main function"""
    print("🔍 Connecting to Supabase...")

    try:
        supabase = connect_to_supabase()
        print("✅ Connected to Supabase successfully!")

        # Analyze catechumen data
        results = analyze_catechumen_data(supabase)

        # Print statistics
        print_statistics(results)

        # Save results to JSON file
        with open('catechumen_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to catechumen_statistics.json")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())