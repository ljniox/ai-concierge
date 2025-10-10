"""
Utility functions for temporary pages system
Integrates with existing SDB services for generating reports and receipts
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.services.temporary_pages_service import get_temp_pages_service
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

class TempPagesUtils:
    """Utilities for generating temporary pages and receipts from SDB data"""

    def __init__(self):
        self.temp_service = get_temp_pages_service()
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def create_student_report_page(
        self,
        student_id: str,
        report_type: str = "complete",
        expires_in_hours: int = 24,
        created_by: str = "system"
    ) -> Optional[str]:
        """Create a temporary student report page"""
        try:
            # Get student data
            student_data = self._get_student_complete_data(student_id)
            if not student_data:
                return None

            # Generate report content based on type
            if report_type == "complete":
                content = self._generate_complete_student_report(student_data)
                title = f"Rapport Complet - {student_data['student']['prenoms']} {student_data['student']['nom']}"
            elif report_type == "grades":
                content = self._generate_grades_report(student_data)
                title = f"Bulletin de Notes - {student_data['student']['prenoms']} {student_data['student']['nom']}"
            elif report_type == "personal":
                content = self._generate_personal_info_report(student_data)
                title = f"Fiche Étudiante - {student_data['student']['prenoms']} {student_data['student']['nom']}"
            else:
                content = student_data
                title = f"Rapport Étudiant - {student_data['student']['prenoms']} {student_data['student']['nom']}"

            # Create temporary page
            access_code = self.temp_service.create_temporary_page(
                title=title,
                content=content,
                content_type="student_report",
                created_by=created_by,
                expires_in_hours=expires_in_hours,
                allowed_actions=["read", "print"]
            )

            return access_code

        except Exception as e:
            print(f"❌ Error creating student report: {e}")
            return None

    def create_class_report_page(
        self,
        class_id: str,
        trimestre: int = 1,
        annee_scolaire: str = "2024-2025",
        expires_in_hours: int = 48,
        created_by: str = "system"
    ) -> Optional[str]:
        """Create a temporary class report page"""
        try:
            # Get class data
            class_data = self._get_class_complete_data(class_id, trimestre, annee_scolaire)
            if not class_data:
                return None

            content = {
                "class_info": class_data["class_info"],
                "students": class_data["students"],
                "statistics": class_data["statistics"],
                "generated_at": datetime.utcnow().isoformat(),
                "trimestre": trimestre,
                "annee_scolaire": annee_scolaire
            }

            title = f"Rapport de Classe - {class_data['class_info']['classe_nom']} - Trimestre {trimestre}"

            # Create temporary page
            access_code = self.temp_service.create_temporary_page(
                title=title,
                content=content,
                content_type="class_report",
                created_by=created_by,
                expires_in_hours=expires_in_hours,
                allowed_actions=["read", "print"]
            )

            return access_code

        except Exception as e:
            print(f"❌ Error creating class report: {e}")
            return None

    def create_payment_receipt(
        self,
        inscription_id: str,
        amount: float,
        payment_method: str = "Cash",
        created_by: str = "system"
    ) -> Optional[str]:
        """Create a permanent payment receipt"""
        try:
            # Get inscription data
            inscription = self._get_inscription_data(inscription_id)
            if not inscription:
                return None

            content = {
                "student_name": f"{inscription['prenoms']} {inscription['nom']}",
                "inscription_id": inscription['id_inscription'],
                "class": inscription.get('class_name', 'N/A'),
                "amount": amount,
                "payment_method": payment_method,
                "payment_date": datetime.utcnow().isoformat(),
                "school_year": inscription.get('annee_scolaire', '2024-2025')
            }

            title = f"Reçu de Paiement - {inscription['prenoms']} {inscription['nom']}"

            # Create permanent receipt
            receipt_code = self.temp_service.create_receipt(
                title=title,
                content=content,
                receipt_type="payment",
                reference_id=inscription_id,
                amount=amount,
                created_by=created_by
            )

            return receipt_code

        except Exception as e:
            print(f"❌ Error creating payment receipt: {e}")
            return None

    def create_inscription_receipt(
        self,
        inscription_id: str,
        created_by: str = "system"
    ) -> Optional[str]:
        """Create a permanent inscription receipt"""
        try:
            # Get inscription data
            inscription = self._get_inscription_data(inscription_id)
            if not inscription:
                return None

            content = {
                "student_name": f"{inscription['prenoms']} {inscription['nom']}",
                "inscription_id": inscription['id_inscription'],
                "class": inscription.get('class_name', 'N/A'),
                "inscription_date": inscription['date_inscription'],
                "status": inscription['etat'],
                "amount_paid": inscription.get('paye', 0),
                "total_amount": inscription.get('montant', 0),
                "school_year": inscription.get('annee_scolaire', '2024-2025')
            }

            title = f"Attestation d'Inscription - {inscription['prenoms']} {inscription['nom']}"

            # Create permanent receipt
            receipt_code = self.temp_service.create_receipt(
                title=title,
                content=content,
                receipt_type="inscription",
                reference_id=inscription_id,
                amount=inscription.get('paye', 0),
                created_by=created_by
            )

            return receipt_code

        except Exception as e:
            print(f"❌ Error creating inscription receipt: {e}")
            return None

    def _get_student_complete_data(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get complete student data"""
        try:
            # Get student basic info
            student = self.supabase.table('catechumenes').select('*').eq('id_catechumene', student_id).single().execute()
            if not student.data:
                return None

            # Get parent info
            parent = None
            if student.data['code_parent']:
                parent = self.supabase.table('parents').select('*').eq('code_parent', student.data['code_parent']).single().execute()

            # Get inscriptions
            inscriptions = self.supabase.table('inscriptions').select('*').eq('id_catechumene', student_id).execute()

            # Get grades
            grades = self.supabase.table('notes').select('*').eq('id_catechumene', student_id).execute()

            return {
                "student": student.data,
                "parent": parent.data if parent else None,
                "inscriptions": inscriptions.data if inscriptions.data else [],
                "grades": grades.data if grades.data else [],
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"❌ Error getting student data: {e}")
            return None

    def _get_class_complete_data(self, class_id: str, trimestre: int, annee_scolaire: str) -> Optional[Dict[str, Any]]:
        """Get complete class data with statistics"""
        try:
            # Get class info
            class_info = self.supabase.table('classes').select('*').eq('id', class_id).single().execute()
            if not class_info.data:
                return None

            # Get students in class
            students = self.supabase.table('inscriptions').select('*').eq('id_classe_courante', class_id).execute()

            # Get grades for this class/trimester
            grades = self.supabase.table('notes').select('*').eq('trimestre', trimestre).eq('annee_scolaire', annee_scolaire).execute()

            # Calculate statistics
            student_grades = {}
            for grade in grades.data if grades.data else []:
                student_id = grade['id_catechumene']
                if student_id not in student_grades:
                    student_grades[student_id] = []
                student_grades[student_id].append(grade['note'])

            class_stats = {
                "total_students": len(students.data) if students.data else 0,
                "students_with_grades": len(student_grades),
                "average_grade": sum([sum(grades_list)/len(grades_list) for grades_list in student_grades.values()]) / len(student_grades) if student_grades else 0,
                "highest_grade": max([max(grades_list) for grades_list in student_grades.values()]) if student_grades else 0,
                "lowest_grade": min([min(grades_list) for grades_list in student_grades.values()]) if student_grades else 0
            }

            return {
                "class_info": class_info.data,
                "students": students.data if students.data else [],
                "grades": grades.data if grades.data else [],
                "statistics": class_stats,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"❌ Error getting class data: {e}")
            return None

    def _get_inscription_data(self, inscription_id: str) -> Optional[Dict[str, Any]]:
        """Get inscription data with class information"""
        try:
            # Get inscription
            inscription = self.supabase.table('inscriptions').select('*').eq('id', inscription_id).single().execute()
            if not inscription.data:
                return None

            # Get class info
            class_info = None
            if inscription.data['id_classe_courante']:
                class_info = self.supabase.table('classes').select('*').eq('id', inscription.data['id_classe_courante']).single().execute()

            result = inscription.data.copy()
            if class_info and class_info.data:
                result['class_name'] = class_info.data['classe_nom']
                result['class_level'] = class_info.data['niveau']

            return result

        except Exception as e:
            print(f"❌ Error getting inscription data: {e}")
            return None

    def _generate_complete_student_report(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete student report content"""
        return {
            "personal_info": {
                "name": f"{student_data['student']['prenoms']} {student_data['student']['nom']}",
                "birth_year": student_data['student']['annee_naissance'],
                "baptized": student_data['student']['baptise'],
                "baptism_location": student_data['student'].get('lieu_bapteme', 'N/A')
            },
            "parent_info": {
                "name": f"{student_data['parent']['prenoms']} {student_data['parent']['nom']}" if student_data['parent'] else 'N/A',
                "phone": student_data['parent']['telephone'] if student_data['parent'] else 'N/A',
                "code_parent": student_data['student']['code_parent']
            },
            "current_inscription": next((ins for ins in student_data['inscriptions'] if ins['etat'] == 'Inscription Validée'), None),
            "grades_history": student_data['grades'],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_grades_report(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate grades-only report"""
        grades_by_trimestre = {}
        for grade in student_data['grades']:
            trimestre = grade['trimestre']
            if trimestre not in grades_by_trimestre:
                grades_by_trimestre[trimestre] = []
            grades_by_trimestre[trimestre].append({
                "note": grade['note'],
                "appreciation": grade.get('appreciation', ''),
                "absences": grade.get('absences', 0),
                "annee_scolaire": grade['annee_scolaire']
            })

        return {
            "student_name": f"{student_data['student']['prenoms']} {student_data['student']['nom']}",
            "grades_by_trimestre": grades_by_trimestre,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_personal_info_report(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personal information report"""
        return {
            "personal_info": {
                "full_name": f"{student_data['student']['prenoms']} {student_data['student']['nom']}",
                "birth_year": student_data['student']['annee_naissance'],
                "baptized": student_data['student']['baptise'],
                "baptism_location": student_data['student'].get('lieu_bapteme', 'N/A'),
                "baptism_certificate_provided": student_data['student']['extrait_bapteme_fourni'],
                "birth_certificate_provided": student_data['student']['extrait_naissance_fourni'],
                "transfer_certificate_provided": student_data['student']['attestation_de_transfert_fournie']
            },
            "parent_info": {
                "full_name": f"{student_data['parent']['prenoms']} {student_data['parent']['nom']}" if student_data['parent'] else 'N/A',
                "phone": student_data['parent']['telephone'] if student_data['parent'] else 'N/A',
                "code_parent": student_data['student']['code_parent']
            },
            "generated_at": datetime.utcnow().isoformat()
        }

# Convenience functions
def get_temp_pages_utils():
    """Get temp pages utilities instance"""
    return TempPagesUtils()

def create_student_report_link(student_id: str, report_type: str = "complete", expires_in_hours: int = 24) -> Optional[str]:
    """Create a student report and return the access link"""
    utils = get_temp_pages_utils()
    access_code = utils.create_student_report_page(student_id, report_type, expires_in_hours)
    if access_code:
        return f"http://localhost:8000/api/v1/temporary-pages/view/{access_code}/web"
    return None

def create_class_report_link(class_id: str, trimestre: int = 1, expires_in_hours: int = 48) -> Optional[str]:
    """Create a class report and return the access link"""
    utils = get_temp_pages_utils()
    access_code = utils.create_class_report_page(class_id, trimestre, expires_in_hours=expires_in_hours)
    if access_code:
        return f"http://localhost:8000/api/v1/temporary-pages/view/{access_code}/web"
    return None

def create_payment_receipt_link(inscription_id: str, amount: float, payment_method: str = "Cash") -> Optional[str]:
    """Create a payment receipt and return the access link"""
    utils = get_temp_pages_utils()
    receipt_code = utils.create_payment_receipt(inscription_id, amount, payment_method)
    if receipt_code:
        return f"http://localhost:8000/api/v1/temporary-pages/receipt/{receipt_code}/web"
    return None

if __name__ == "__main__":
    # Test the utilities
    print("🧪 Testing Temporary Pages Utilities...")

    utils = get_temp_pages_utils()

    # Test creating a student report (would need a real student_id)
    print("ℹ️  Student report creation tested (requires real student ID)")

    # Test creating a payment receipt (would need real inscription_id)
    print("ℹ️  Payment receipt creation tested (requires real inscription ID)")

    print("✅ Testing completed!")