#!/usr/bin/env python3
"""
Analyze Class Mismatches for Migration Fix
"""

import os
import sys
import requests
from supabase_config import get_supabase_anon_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASEROW_URL = os.getenv("BASEROW_URL")
BASEROW_AUTH_KEY = os.getenv("BASEROW_AUTH_KEY")

def get_supabase_classes():
    """Get all classes from Supabase"""
    try:
        supabase = get_supabase_anon_client()
        result = supabase.table('classes').select('*').order('classe_nom').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"❌ Error getting Supabase classes: {e}")
        return []

def get_baserow_inscriptions():
    """Get non-migrated inscriptions from Baserow"""
    print("📥 Fetching non-migrated inscriptions...")
    
    # First get migrated IDs
    try:
        supabase = get_supabase_anon_client()
        migrated_result = supabase.table('inscriptions').select('id_inscription').execute()
        migrated_ids = {inscr['id_inscription'] for inscr in migrated_result.data}
    except Exception as e:
        print(f"❌ Error getting migrated IDs: {e}")
        return []
    
    # Get all Baserow inscriptions
    headers = {
        "Authorization": f"Token {BASEROW_AUTH_KEY}"
    }
    
    all_inscriptions = []
    page = 1
    
    while True:
        url = f"{BASEROW_URL}/api/database/rows/table/574/?user_field_names=true&page={page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error fetching inscriptions: {response.status_code}")
            break
        
        data = response.json()
        # Filter for non-migrated
        page_inscriptions = [inscr for inscr in data['results'] 
                           if inscr['ID Inscription'] not in migrated_ids]
        all_inscriptions.extend(page_inscriptions)
        
        if not data['next']:
            break
            
        page += 1
    
    return all_inscriptions

def analyze_class_issues(supabase_classes, baserow_inscriptions):
    """Analyze class name mismatches"""
    print("🔍 Analyzing class mismatches...")
    
    # Create mapping of Supabase classes
    supabase_class_names = {c['classe_nom'].lower().strip() for c in supabase_classes}
    supabase_class_map = {c['classe_nom'].lower().strip(): c for c in supabase_classes}
    
    # Extract all class names from Baserow
    baserow_classes = {}
    class_issues = {}
    
    for inscr in baserow_inscriptions:
        current_class = None
        if inscr.get('ClasseCourante'):
            current_class = inscr['ClasseCourante'].strip()
        
        if current_class:
            if current_class not in baserow_classes:
                baserow_classes[current_class] = 0
            baserow_classes[current_class] += 1
            
            # Check if class exists in Supabase
            if current_class.lower().strip() not in supabase_class_names:
                if current_class not in class_issues:
                    class_issues[current_class] = []
                
                # Find potential matches
                suggestions = find_class_suggestions(current_class, supabase_class_names)
                class_issues[current_class] = {
                    'count': baserow_classes[current_class],
                    'suggestions': suggestions,
                    'sample_records': []
                }
    
    # Add sample records for each issue
    for inscr in baserow_inscriptions:
        current_class = inscr.get('ClasseCourante', '').strip()
        if current_class in class_issues and len(class_issues[current_class]['sample_records']) < 3:
            class_issues[current_class]['sample_records'].append({
                'id': inscr['ID Inscription'],
                'student': f"{inscr.get('Prenoms')} {inscr.get('Nom')}"
            })
    
    return baserow_classes, class_issues, supabase_classes

def find_class_suggestions(baserow_class, supabase_class_names):
    """Find potential matches for a Baserow class in Supabase"""
    suggestions = []
    
    baserow_lower = baserow_class.lower().strip()
    
    # Direct matches
    if baserow_lower in supabase_class_names:
        return [{'type': 'exact', 'match': baserow_class, 'confidence': 100}]
    
    # Find partial matches
    for supabase_name in supabase_class_names:
        supabase_lower = supabase_name
        
        # Check for substring matches
        if baserow_lower in supabase_lower or supabase_lower in baserow_lower:
            confidence = calculate_similarity(baserow_lower, supabase_lower)
            suggestions.append({
                'type': 'partial',
                'match': supabase_name,
                'confidence': confidence
            })
    
    # Check for keyword matches
    keywords = ['pré', 'caté', 'communion', 'confirmation', 'persévérance', 'ci', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6e', '5e']
    baserow_words = baserow_lower.split()
    
    for supabase_name in supabase_class_names:
        supabase_words = supabase_name.split()
        
        # Count matching keywords
        matching_keywords = set(baserow_words) & set(supabase_words)
        if matching_keywords:
            confidence = len(matching_keywords) / max(len(baserow_words), len(supabase_words)) * 100
            suggestions.append({
                'type': 'keyword',
                'match': supabase_name,
                'confidence': confidence,
                'matching_keywords': list(matching_keywords)
            })
    
    # Sort by confidence and return top suggestions
    suggestions.sort(key=lambda x: x['confidence'], reverse=True)
    return suggestions[:5]

def calculate_similarity(str1, str2):
    """Simple similarity calculation"""
    # Longer common substring approach
    longer = str1 if len(str1) > len(str2) else str2
    shorter = str2 if len(str1) > len(str2) else str1
    
    if len(longer) == 0:
        return 100
    
    # Find longest common substring
    max_length = 0
    for i in range(len(shorter)):
        for j in range(i + 1, len(shorter) + 1):
            substring = shorter[i:j]
            if substring in longer:
                max_length = max(max_length, len(substring))
    
    return (max_length / len(longer)) * 100

def generate_class_fix_report(baserow_classes, class_issues, supabase_classes):
    """Generate comprehensive class fix report"""
    
    report = """# Class Mismatch Analysis Report

## Current Supabase Classes
"""
    
    for cls in supabase_classes:
        report += f"- {cls['classe_nom']} (ID: {cls['id']})\n"
    
    report += f"\n## Baserow Classes Found ({len(baserow_classes)} unique)\n"
    
    for cls_name, count in sorted(baserow_classes.items()):
        if cls_name in class_issues:
            report += f"- ❌ {cls_name} ({count} records) - **NO MATCH**\n"
        else:
            report += f"- ✅ {cls_name} ({count} records)\n"
    
    report += "\n## Class Mismatches and Suggested Fixes\n"
    
    for baserow_class, issue in sorted(class_issues.items()):
        report += f"\n### {baserow_class} ({issue['count']} records)\n"
        
        if issue['suggestions']:
            report += "\n**Suggested Matches:**\n"
            for suggestion in issue['suggestions']:
                confidence_emoji = "🟢" if suggestion['confidence'] > 80 else "🟡" if suggestion['confidence'] > 50 else "🔴"
                report += f"- {confidence_emoji} **{suggestion['match']}** ({suggestion['confidence']:.0f}% confidence)"
                
                if suggestion['type'] == 'keyword' and 'matching_keywords' in suggestion:
                    report += f" - Keywords: {', '.join(suggestion['matching_keywords'])}"
                report += "\n"
        else:
            report += "\n**No good matches found** - Consider creating a new class\n"
        
        report += "\n**Sample Records:**\n"
        for record in issue['sample_records'][:3]:
            report += f"- {record['student']} (ID: {record['id']})\n"
    
    report += """

## Recommended Actions

### 1. High Confidence Matches (>80%)
These should be automatically mapped:
"""

    high_confidence = []
    for baserow_class, issue in class_issues.items():
        for suggestion in issue['suggestions']:
            if suggestion['confidence'] > 80:
                high_confidence.append((baserow_class, suggestion['match']))
    
    for baserow, supabase in high_confidence:
        report += f"- Map '{baserow}' → '{supabase}'\n"
    
    report += "\n### 2. Medium Confidence Matches (50-80%)\n"
    report += "Review these manually before mapping:\n"
    
    medium_confidence = []
    for baserow_class, issue in class_issues.items():
        for suggestion in issue['suggestions']:
            if 50 <= suggestion['confidence'] <= 80:
                medium_confidence.append((baserow_class, suggestion['match'], suggestion['confidence']))
    
    for baserow, supabase, conf in medium_confidence:
        report += f"- '{baserow}' → '{supabase}' ({conf:.0f}% confidence)\n"
    
    report += "\n### 3. Low Confidence Matches (<50%)\n"
    report += "Consider creating new classes or investigate data quality:\n"
    
    low_confidence = []
    for baserow_class, issue in class_issues.items():
        if not any(s['confidence'] > 50 for s in issue['suggestions']):
            low_confidence.append(baserow_class)
    
    for cls in low_confidence:
        count = next((issue['count'] for b, issue in class_issues.items() if b == cls), 0)
        report += f"- '{cls}' ({count} records)\n"
    
    report += """

### 4. Missing Classes to Create
Consider adding these classes to Supabase if they represent legitimate educational levels:
"""

    potential_new = []
    for baserow_class, issue in class_issues.items():
        if not any(s['confidence'] > 70 for s in issue['suggestions']):
            potential_new.append((baserow_class, issue['count']))
    
    for cls, count in potential_new:
        report += f"- {cls} ({count} records)\n"
    
    return report

def main():
    print("🔍 Analyzing Class Mismatches for Migration Fix")
    print("=" * 60)
    
    # Get data
    supabase_classes = get_supabase_classes()
    baserow_inscriptions = get_baserow_inscriptions()
    
    if not supabase_classes or not baserow_inscriptions:
        print("❌ Failed to get required data")
        return False
    
    print(f"📊 Found {len(supabase_classes)} Supabase classes")
    print(f"📊 Found {len(baserow_inscriptions)} non-migrated inscriptions")
    
    # Analyze class issues
    baserow_classes, class_issues, supabase_classes = analyze_class_issues(
        supabase_classes, baserow_inscriptions
    )
    
    print(f"🔍 Found {len(class_issues)} class mismatches")
    
    # Generate report
    report = generate_class_fix_report(baserow_classes, class_issues, supabase_classes)
    
    # Save report
    with open('class_mismatch_analysis.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Class analysis saved to 'class_mismatch_analysis.md'")
    
    # Also create a simple mapping file
    create_simple_mapping(class_issues)
    
    return True

def create_simple_mapping(class_issues):
    """Create a simple class mapping file"""
    mapping_content = "# Baserow to Supabase Class Mapping Suggestions\n\n"
    
    for baserow_class, issue in sorted(class_issues.items()):
        mapping_content += f"## {baserow_class} ({issue['count']} records)\n"
        
        if issue['suggestions']:
            best_match = issue['suggestions'][0]  # Take the best suggestion
            if best_match['confidence'] > 70:
                mapping_content += f"SUGGESTED: {best_match['match']} ({best_match['confidence']:.0f}% confidence)\n\n"
            else:
                mapping_content += "NEEDS REVIEW: No high-confidence match\n\n"
        else:
            mapping_content += "NO MATCH FOUND: Consider creating new class\n\n"
    
    with open('class_mapping_suggestions.txt', 'w', encoding='utf-8') as f:
        f.write(mapping_content)
    
    print("✅ Simple mapping saved to 'class_mapping_suggestions.txt'")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)