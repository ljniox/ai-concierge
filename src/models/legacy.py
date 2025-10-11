"""
Legacy Data Models for SDB Catechism Database

Provides read-only Pydantic models for existing database tables:
- catechumenes_2 (509 records): Student information
- parents_2 (341 records): Parent contact information
- inscriptions_16 (819 records): Historical enrollment records
- classes (15 records): Class definitions

These models support data migration and legacy data queries while
maintaining compatibility with the new enrollment system.

Research Decision: research.md#7 - Legacy Data Integration
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import DatabaseModel


class LegacyCatechumene(DatabaseModel):
    """
    Legacy student record from catechumenes_2 table.

    Read-only model for historical student data.
    Used for:
    - Migration to new inscriptions table
    - Legacy data queries
    - Re-enrollment workflows
    """
    model_config = ConfigDict(from_attributes=True)

    # Primary fields from database
    ID_Catechumene: str = Field(description="UUID identifier for student")
    Nom: str = Field(description="Last name")
    Prenoms: str = Field(description="First name(s)")
    Ann_e_de_naissance: Optional[str] = Field(description="Birth year (text format)")
    Code_Parent: Optional[str] = Field(description="Parent identifier (links to parents_2)")
    Baptisee: Optional[str] = Field(description="Baptism status: 'oui'/'non'")
    LieuBapteme: Optional[str] = Field(description="Baptism location")
    Extrait_de_Naissance_Fourni: Optional[str] = Field(description="Birth certificate provided")
    Extrait_De_Bapteme_Fourni: Optional[str] = Field(description="Baptism certificate provided: 'oui'/'non'")
    Attestation_De_Transfert_Fournie: Optional[str] = Field(description="Transfer attestation provided: 'oui'/'non'")
    Extrait_Naissance: Optional[str] = Field(description="Birth certificate file reference")
    Extrait_Bapteme: Optional[str] = Field(description="Baptism certificate file reference")
    Attestation_Transfert: Optional[str] = Field(description="Transfer attestation file reference")
    Commentaire: Optional[str] = Field(description="Comments/notes")
    operateur: Optional[str] = Field(description="Data entry operator")
    id: Optional[str] = Field(description="Sequential ID")

    @property
    def full_name(self) -> str:
        """Get student's full name."""
        return f"{self.Nom} {self.Prenoms}".strip()

    @property
    def is_baptized(self) -> bool:
        """Check if student is baptized."""
        return self.Baptisee and self.Baptisee.lower() == 'oui'

    def to_new_inscription_data(self) -> Dict[str, Any]:
        """
        Convert legacy student data to new enrollment format.

        Returns:
            Dict compatible with InscriptionCreate schema
        """
        return {
            "nom_enfant": self.Nom,
            "prenom_enfant": self.Prenoms,
            "legacy_catechumene_id": self.ID_Catechumene,
            "legacy_code_parent": self.Code_Parent,
            "date_naissance": self.parse_birth_year(),
            "lieu_naissance": "Inconnu",  # Legacy data doesn't include place of birth
            "date_bapteme": None,  # Legacy has year but not specific date
            "paroisse_bapteme": self.LieuBapteme,
            "notes": self.Commentaire
        }

    def parse_birth_year(self) -> Optional[str]:
        """Parse birth year to approximate date."""
        if self.Ann_e_de_naissance:
            try:
                year = int(self.Ann_e_de_naissance)
                return f"{year}-01-01"  # Approximate to January 1st
            except ValueError:
                pass
        return None


class LegacyParent(DatabaseModel):
    """
    Legacy parent record from parents_2 table.

    Read-only model for historical parent data.
    Used for:
    - Migration to new profil_utilisateurs table
    - Authentication via Code_Parent (FR-032)
    - Legacy data queries
    """
    model_config = ConfigDict(from_attributes=True)

    # Primary fields from database
    Code_Parent: str = Field(description="Unique parent code (e.g., '1de90', '57704')")
    Nom: str = Field(description="Last name")
    Prenoms: str = Field(description="First name(s)")
    T_l_phone: Optional[str] = Field(description="Primary phone number")
    T_l_phone_2: Optional[str] = Field(description="Secondary phone number")
    Email: Optional[str] = Field(description="Email address")
    Actif: Optional[str] = Field(description="Active status: 'True'/'False'")
    id: Optional[str] = Field(description="Sequential ID")

    @property
    def full_name(self) -> str:
        """Get parent's full name."""
        return f"{self.Nom} {self.Prenoms}".strip()

    @property
    def is_active(self) -> bool:
        """Check if parent is marked as active."""
        return self.Actif and self.Actif.lower() == 'true'

    @property
    def primary_phone(self) -> Optional[str]:
        """Get primary phone number."""
        if self.T_l_phone:
            return self.T_l_phone
        return self.T_l_phone_2

    def to_new_profile_data(self) -> Dict[str, Any]:
        """
        Convert legacy parent data to new user profile format.

        Returns:
            Dict compatible with ProfileCreate schema
        """
        return {
            "user_id": DatabaseModel.generate_uuid(),
            "nom": self.Nom,
            "prenom": self.Prenoms,
            "role": "parent",
            "telephone": self.primary_phone,
            "email": self.Email,
            "code_parent": self.Code_Parent,  # Will be hashed in the service layer
            "actif": self.is_active
        }


class LegacyInscription(DatabaseModel):
    """
    Legacy enrollment record from inscriptions_16 table.

    Read-only model for historical enrollment data.
    Used for:
    - Data analysis and reporting
    - Payment history tracking
    - Migration validation
    """
    model_config = ConfigDict(from_attributes=True)

    # Primary fields from database
    ID_Inscription: str = Field(description="Unique inscription identifier")
    ID_Catechumene: Optional[str] = Field(description="FK to catechumenes_2")
    Annee_Inscription: Optional[str] = Field(description="Enrollment year")
    ID_AnneeInscription: Optional[str] = Field(description="Reference to annee_inscription")
    ClasseCourante: Optional[str] = Field(description="Current class name")
    ID_ClasseCourante: Optional[str] = Field(description="FK to classes")
    Groupe: Optional[str] = Field(description="Group identifier")
    Paye: Optional[str] = Field(description="Payment status")
    Montant: Optional[str] = Field(description="Amount paid")
    Moyen_Paiement: Optional[str] = Field(description="Payment method")
    Choix_Paiement: Optional[str] = Field(description="Payment choice")
    Infos_Paiement: Optional[str] = Field(description="Payment information")
    Etat: Optional[str] = Field(description="Enrollment state")
    DateInscription: Optional[str] = Field(description="Inscription date")
    Commentaire: Optional[str] = Field(description="Comments")
    ParoisseAnneePrecedente: Optional[str] = Field(description="Previous parish")
    AnneePrecedente: Optional[str] = Field(description="Previous year")
    Annee_Suivante: Optional[str] = Field(description="Next year")
    Livre_Remis: Optional[str] = Field(description="Book delivered status")
    Note_Finale: Optional[str] = Field(description="Final grade")
    Resultat_Final: Optional[str] = Field(description="Final result")
    Absennces: Optional[str] = Field(description="Absences count")
    Mouvements_de_caisse: Optional[str] = Field(description="Cash movements")
    AttestationDeTransfert: Optional[str] = Field(description="Transfer attestation")
    ReconCheck: Optional[str] = Field(description="Reconciliation check")
    ReconOP: Optional[str] = Field(description="Reconciliation operation")
    action: Optional[str] = Field(description="Action performed")
    sms: Optional[str] = Field(description="SMS notifications")
    operateur: Optional[str] = Field(description="Operator")
    Nom: Optional[str] = Field(description="Student name")
    Prenoms: Optional[str] = Field(description="Student first names")
    id: Optional[str] = Field(description="Sequential ID")

    @property
    def full_name(self) -> str:
        """Get student's full name from enrollment record."""
        return f"{self.Nom or ''} {self.Prenoms or ''}".strip()

    @property
    def is_paid(self) -> bool:
        """Check if payment status indicates paid."""
        return self.Paye and self.Paye.lower() in ['paye', 'paiement', 'regle']

    @property
    def payment_amount(self) -> Optional[float]:
        """Parse payment amount to float."""
        if self.Montant:
            try:
                return float(str(self.Montant).replace(',', '.'))
            except ValueError:
                pass
        return None

    def parse_enrollment_date(self) -> Optional[datetime]:
        """Parse enrollment date to datetime."""
        if self.DateInscription:
            try:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(self.DateInscription, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        return None


class LegacyClass(DatabaseModel):
    """
    Legacy class record from classes table.

    Read-only model for class definitions.
    Used for:
    - Class management in enrollment system
    - Student placement
    - Scheduling and organization
    """
    model_config = ConfigDict(from_attributes=True)

    # Primary fields from database
    Nom: str = Field(description="Class name")
    court: Optional[str] = Field(description="Short name")
    Ordre: Optional[str] = Field(description="Display order")
    Actif: Optional[str] = Field(description="Active status")
    Inscriptions___ID_AnneeSuivante: Optional[str] = Field(description="Next year inscription link")
    id: Optional[str] = Field(description="Sequential ID")

    @property
    def is_active(self) -> bool:
        """Check if class is marked as active."""
        return self.Actif and self.Actif.lower() in ['true', '1', 'actif', 'active']

    @property
    def display_order(self) -> int:
        """Get display order as integer."""
        if self.Ordre:
            try:
                return int(self.Ordre)
            except ValueError:
                pass
        return 999  # Put classes without order at the end

    @property
    def short_name(self) -> str:
        """Get short name for display."""
        return self.court or self.Nom


# Legacy Data Service Helpers
class LegacyDataQueries:
    """Predefined queries for accessing legacy data."""

    @staticmethod
    def get_parent_by_code(code_parent: str) -> str:
        """Query to get parent by Code_Parent."""
        return "SELECT * FROM parents_2 WHERE Code_Parent = ? AND Actif = 'True'"

    @staticmethod
    def get_students_by_parent_code(code_parent: str) -> str:
        """Query to get students by parent Code_Parent."""
        return "SELECT * FROM catechumenes_2 WHERE Code_Parent = ? ORDER BY Nom, Prenoms"

    @staticmethod
    def get_legacy_enrollments_by_student(student_id: str) -> str:
        """Query to get historical enrollments for a student."""
        return "SELECT * FROM inscriptions_16 WHERE ID_Catechumene = ? ORDER BY Annee_Inscription DESC"

    @staticmethod
    def get_all_active_classes() -> str:
        """Query to get all active classes."""
        return "SELECT * FROM classes WHERE Actif = 'True' ORDER BY CAST(Ordre AS INTEGER), Nom"

    @staticmethod
    def get_class_by_name(class_name: str) -> str:
        """Query to get class by name."""
        return "SELECT * FROM classes WHERE Nom = ? OR court = ?"

    @staticmethod
    def check_legacy_enrollment_conflict(parent_code: str, annee_catechetique: str) -> str:
        """Query to check if student already enrolled in given year."""
        return """
        SELECT c.* FROM catechumenes_2 c
        JOIN inscriptions_16 i ON c.ID_Catechumene = i.ID_Catechumene
        WHERE c.Code_Parent = ? AND i.Annee_Inscription = ?
        """