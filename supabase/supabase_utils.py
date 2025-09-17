"""
Supabase Utilities for SDB Operations
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from supabase_config import get_supabase_client, get_supabase_anon_client
import json

class SDBSupabase:
    """SDB Supabase operations class"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.anon_client = get_supabase_anon_client()
    
    # Student Operations
    def search_student(self, search_term: str) -> List[Dict]:
        """Search for students by name"""
        try:
            result = self.anon_client.rpc('search_students', {'p_search_term': search_term}).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error searching student: {e}")
            return []
    
    def get_student_info(self, id_catechumene: str) -> Optional[Dict]:
        """Get complete student information"""
        try:
            result = self.anon_client.rpc('get_student_info', {'p_id_catechumene': id_catechumene}).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error getting student info: {e}")
            return None
    
    def get_student_grades(self, id_catechumene: str) -> List[Dict]:
        """Get student grades history"""
        try:
            result = self.anon_client.rpc('get_student_grades', {'p_id_catechumene': id_catechumene}).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting student grades: {e}")
            return []
    
    def get_student_inscriptions(self, id_catechumene: str) -> List[Dict]:
        """Get student inscription history"""
        try:
            result = (self.anon_client.table('inscriptions')
                      .select('*')
                      .eq('id_catechumene', id_catechumene)
                      .order('date_inscription', desc=True)
                      .execute())
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting student inscriptions: {e}")
            return []
    
    # Parent Operations
    def get_parent_info(self, code_parent: str) -> Optional[Dict]:
        """Get parent information"""
        try:
            result = (self.anon_client.table('parents')
                      .select('*')
                      .eq('code_parent', code_parent)
                      .single()
                      .execute())
            return result.data if result.data else None
        except Exception as e:
            print(f"❌ Error getting parent info: {e}")
            return None
    
    def search_parent(self, search_term: str) -> List[Dict]:
        """Search for parents"""
        try:
            result = (self.anon_client.table('parents')
                      .select('*')
                      .or_(f"prenom.ilike.%{search_term}%,nom.ilike.%{search_term}%,telephone.ilike.%{search_term}%")
                      .execute())
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error searching parent: {e}")
            return []
    
    # Class Operations
    def get_classes(self) -> List[Dict]:
        """Get all classes"""
        try:
            result = self.anon_client.table('classes').select('*').order('niveau').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting classes: {e}")
            return []
    
    def get_students_by_class(self, classe_id: str, annee_id: str = None) -> List[Dict]:
        """Get students in a specific class"""
        try:
            query = (self.anon_client.table('inscriptions')
                    .select('*, catechumenes(*)')
                    .eq('id_classe_courante', classe_id)
                    .eq('etat', 'Inscription Validée'))
            
            if annee_id:
                query = query.eq('id_annee_inscription', annee_id)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting students by class: {e}")
            return []
    
    # Grade Operations
    def add_grade(self, id_inscription: str, trimestre: int, note: float, 
                  annee_scolaire: str = "2024-2025", appreciation: str = "", 
                  absences: int = 0) -> bool:
        """Add a grade for a student"""
        try:
            # Get student info
            inscription = self.anon_client.table('inscriptions').select('id_catechumene').eq('id', id_inscription).single().execute()
            if not inscription.data:
                return False
            
            grade_data = {
                'id_inscription': id_inscription,
                'id_catechumene': inscription.data['id_catechumene'],
                'trimestre': trimestre,
                'annee_scolaire': annee_scolaire,
                'note': note,
                'appreciation': appreciation,
                'absences': absences
            }
            
            result = self.client.table('notes').insert(grade_data).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Error adding grade: {e}")
            return False
    
    def get_class_grades(self, classe_id: str, trimestre: int, annee_scolaire: str = "2024-2025") -> List[Dict]:
        """Get grades for all students in a class"""
        try:
            result = (self.anon_client.table('notes')
                      .select('*, inscriptions!inner(id_catechumene, prenoms, nom)')
                      .eq('trimestre', trimestre)
                      .eq('annee_scolaire', annee_scolaire)
                      .execute())
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting class grades: {e}")
            return []
    
    # Registration Operations
    def create_inscription(self, inscription_data: Dict) -> Optional[str]:
        """Create a new inscription"""
        try:
            result = self.client.table('inscriptions').insert(inscription_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"❌ Error creating inscription: {e}")
            return None
    
    def update_inscription(self, inscription_id: str, update_data: Dict) -> bool:
        """Update an existing inscription"""
        try:
            result = self.client.table('inscriptions').update(update_data).eq('id', inscription_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Error updating inscription: {e}")
            return False
    
    # Statistics Operations
    def get_class_stats(self, classe_id: str, annee_id: str) -> Dict:
        """Get statistics for a class"""
        try:
            # Get total students
            students_result = (self.anon_client.table('inscriptions')
                            .select('count', count='exact')
                            .eq('id_classe_courante', classe_id)
                            .eq('id_annee_inscription', annee_id)
                            .eq('etat', 'Inscription Validée')
                            .execute())
            
            total_students = students_result.count if hasattr(students_result, 'count') else 0
            
            # Get payment stats
            payments_result = (self.anon_client.table('inscriptions')
                             .select('montant, paye')
                             .eq('id_classe_courante', classe_id)
                             .eq('id_annee_inscription', annee_id)
                             .execute())
            
            total_montant = sum(p['montant'] for p in payments_result.data) if payments_result.data else 0
            total_paye = sum(p['paye'] for p in payments_result.data) if payments_result.data else 0
            
            return {
                'total_students': total_students,
                'total_montant': total_montant,
                'total_paye': total_paye,
                'payment_rate': (total_paye / total_montant * 100) if total_montant > 0 else 0
            }
        except Exception as e:
            print(f"❌ Error getting class stats: {e}")
            return {}
    
    # Utility Operations
    def get_current_year_id(self) -> Optional[str]:
        """Get current school year ID"""
        try:
            result = (self.anon_client.table('annees_scolaires')
                      .select('id')
                      .eq('active', True)
                      .single()
                      .execute())
            return result.data['id'] if result.data else None
        except Exception as e:
            print(f"❌ Error getting current year ID: {e}")
            return None
    
    def export_student_data(self, format_type: str = 'json') -> str:
        """Export all student data"""
        try:
            result = (self.anon_client.table('catechumenes')
                      .select('*, parents(*), inscriptions(*, classes(*))')
                      .execute())
            
            if format_type == 'json':
                return json.dumps(result.data, indent=2, default=str)
            elif format_type == 'csv':
                # Simple CSV export (you might want to use pandas for more complex exports)
                import csv
                import io
                
                if not result.data:
                    return ""
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=result.data[0].keys())
                writer.writeheader()
                writer.writerows(result.data)
                return output.getvalue()
            else:
                return str(result.data)
        except Exception as e:
            print(f"❌ Error exporting student data: {e}")
            return ""

# Convenience functions
def get_sdb_client():
    """Get SDB Supabase client instance"""
    return SDBSupabase()

def quick_student_search(search_term: str):
    """Quick student search"""
    sdb = get_sdb_client()
    students = sdb.search_student(search_term)
    
    if not students:
        print("No students found.")
        return []
    
    print(f"\n📝 Found {len(students)} student(s):")
    for i, student in enumerate(students, 1):
        print(f"{i}. {student['prenoms']} {student['nom']} - {student['current_classe']} ({student['current_annee']})")
        print(f"   Code Parent: {student['code_parent']}")
    
    return students

if __name__ == "__main__":
    # Test the utilities
    print("🧪 Testing SDB Supabase Utilities...")
    
    sdb = get_sdb_client()
    
    # Test search
    test_search = quick_student_search("MANEL")
    
    # Test get student info
    if test_search:
        student_id = test_search[0]['id_catechumene']
        student_info = sdb.get_student_info(student_id)
        if student_info:
            print(f"\n👤 Student Info: {student_info['prenoms']} {student_info['nom']}")
            print(f"   Baptized: {student_info['baptise']}")
            print(f"   Parent: {student_info['parent_prenoms']} {student_info['parent_nom']}")
    
    print("\n✅ Testing completed!")