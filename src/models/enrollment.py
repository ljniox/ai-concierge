"""
Enrollment Models

Pydantic models for enrollment management system with comprehensive validation.

Features:
- Student enrollment data with OCR integration
- Legacy data migration support
- Fixed enrollment fee (5000 FCFA)
- Status management and transitions

Constitution Principle II: Type safety throughout codebase
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

from .base import DatabaseModel, TimestampMixin, AuditMixin, InscriptionStatut, UserRole


class InscriptionCreate(BaseModel):
    """Request model for creating new enrollment."""

    nom_enfant: str = Field(..., min_length=2, max_length=50, description="Student's last name")
    prenom_enfant: str = Field(..., min_length=2, max_length=50, description="Student's first name(s)")
    date_naissance: date = Field(..., description="Birth date")
    lieu_naissance: str = Field(..., min_length=2, max_length=100, description="Birth place")
    date_bapteme: Optional[date] = Field(None, description="Baptism date (if baptized)")
    paroisse_bapteme: Optional[str] = Field(None, max_length=100, description="Baptism parish")
    nom_pretre_bapteme: Optional[str] = Field(None, max_length=100, description="Baptizing priest name")
    paroisse_origine: Optional[str] = Field(None, max_length=100, description="Origin parish (for transfers)")
    annee_catechisme_precedente: Optional[str] = Field(None, description="Previous catechism year (for transfers)")
    annee_catechetique: str = Field(..., description="Catechism year (e.g., '2025-2026')")
    niveau: Optional[str] = Field(None, description="Catechism level (éveil, CE1, CE2, CM1, CM2, confirmation)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    # Legacy data support
    legacy_code_parent: Optional[str] = Field(None, description="Legacy parent code (migration)")
    legacy_catechumene_id: Optional[str] = Field(None, description="Legacy student ID (migration)")

    # Fixed fee is automatically set to 5000 FCFA
    montant_total: Decimal = Field(default=Decimal('5000.00'), description="Fixed enrollment fee (5000 FCFA)")

    @validator('annee_catechetique')
    def validate_annee_catechetique(cls, v):
        """Validate catechism year format (YYYY-YYYY)."""
        import re
        pattern = r'^(\d{4})-(\d{4})$'
        match = re.match(pattern, v)
        if not match:
            raise ValueError("Invalid catechism year format. Use YYYY-YYYY format (e.g., 2025-2026)")

        start_year = int(match.group(1))
        end_year = int(match.group(2))

        if end_year != start_year + 1:
            raise ValueError("End year must be exactly one year after start year")

        return v

    @validator('niveau')
    def validate_niveau(cls, v):
        """Validate catechism level."""
        if v is not None:
            valid_levels = ['éveil', 'CE1', 'CE2', 'CM1', 'CM2', 'confirmation']
            if v not in valid_levels:
                raise ValueError(f"Invalid catechism level. Valid levels: {', '.join(valid_levels)}")
        return v

    @validator('date_bapteme')
    def validate_date_bapteme(cls, v, values):
        """Baptism date cannot be before birth date."""
        if v and 'date_naissance' in values and v < values['date_naissance']:
            raise ValueError("Baptism date cannot be before birth date")
        return v

    @validator('montant_total')
    def validate_montant_fixe(cls, v):
        """Ensure the fixed enrollment fee is used."""
        if v != Decimal('5000.00'):
            raise ValueError("Enrollment fee is fixed at 5000 FCFA")
        return v


class InscriptionUpdate(BaseModel):
    """Request model for updating enrollment."""
    nom_enfant: Optional[str] = Field(None, min_length=2, max_length=50)
    prenom_enfant: Optional[str] = Field(None, min_length=2, max_length=50)
    date_naissance: Optional[date] = None
    lieu_naissance: Optional[str] = Field(None, min_length=2, max_length=100)
    date_bapteme: Optional[date] = None
    paroisse_bapteme: Optional[str] = Field(None, max_length=100)
    nom_pretre_bapteme: Optional[str] = Field(None, max_length=100)
    paroisse_origine: Optional[str] = Field(None, max_length=100)
    annee_catechisme_precedente: Optional[str] = None
    niveau: Optional[str] = Field(None, description="Catechism level (éveil, CE1, CE2, CM1, CM2, confirmation)")
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('niveau')
    def validate_niveau(cls, v):
        """Validate catechism level."""
        if v is not None:
            valid_levels = ['éveil', 'CE1', 'CE2', 'CM1', 'CM2', 'confirmation']
            if v not in valid_levels:
                raise ValueError(f"Invalid catechism level. Valid levels: {', '.join(valid_levels)}")
        return v


class Inscription(DatabaseModel, AuditMixin):
    """
    Complete enrollment model with all fields.

    Represents new enrollment records with OCR document processing
    and fixed 5000 FCFA enrollment fee.
    """
    id: str = Field(..., description="UUID identifier")
    numero_unique: str = Field(..., description="Human-readable inscription number (e.g., CAT-2025-0001)")
    parent_id: str = Field(..., description="Enrolling parent user ID")
    legacy_code_parent: Optional[str] = Field(None, description="Legacy parent code (migration support)")
    legacy_catechumene_id: Optional[str] = Field(None, description="Legacy student ID (re-enrollment)")
    nom_enfant: str = Field(..., description="Student last name")
    prenom_enfant: str = Field(..., description="Student first name(s)")
    date_naissance: date = Field(..., description="Birth date")
    lieu_naissance: str = Field(..., description="Birth place")
    date_bapteme: Optional[date] = Field(None, description="Baptism date")
    paroisse_bapteme: Optional[str] = Field(None, description="Baptism parish")
    nom_pretre_bapteme: Optional[str] = Field(None, description="Baptizing priest name")
    paroisse_origine: Optional[str] = Field(None, description="Origin parish (for transfers)")
    annee_catechisme_precedente: Optional[str] = Field(None, description="Previous catechism year (for transfers)")
    annee_catechetique: str = Field(..., description="Catechism year (e.g., '2025-2026')")
    niveau: Optional[str] = Field(None, description="Catechism level")
    classe_id: Optional[str] = Field(None, description="Class assignment (when placed)")
    statut: str = Field(..., description="Enrollment status")
    montant_total: Decimal = Field(..., description="Fixed enrollment fee (5000 FCFA)")
    montant_paye: Decimal = Field(..., description="Amount paid so far")
    solde_restant: Optional[Decimal] = Field(None, description="Remaining balance (calculated)")
    validated_by: Optional[str] = Field(None, description="Staff member who validated")
    validated_at: Optional[datetime] = Field(None, description="Validation timestamp")
    notes: Optional[str] = Field(None, description="Additional notes")

    @property
    def full_name(self) -> str:
        """Get student's full name."""
        return f"{self.nom_enfant} {self.prenom_enfant}".strip()

    @property
    def is_paid(self) -> bool:
        """Check if enrollment is fully paid."""
        return self.montant_paye >= self.montant_total

    @property
    def is_active(self) -> bool:
        """Check if enrollment is active."""
        return self.statut == InscriptionStatut.ACTIVE

    @property
    def can_be_modified(self) -> bool:
        """Check if enrollment can be modified."""
        return self.statut in [InscriptionStatut.BROUILLON, InscriptionStatut.EN_ATTENTE_PAIEMENT]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if enrollment can be cancelled."""
        return self.statut != InscriptionStatut.ANNULEE

    @property
    def requires_documents(self) -> List[str]:
        """Get list of required documents based on student data."""
        required = []

        # Birth certificate always required
        required.append("extrait_naissance")

        # Baptism certificate if baptized
        if self.date_bapteme:
            required.append("extrait_bapteme")

        # Transfer attestation if coming from another parish
        if self.paroisse_origine:
            required.append("attestation_transfert")

        return required

    @property
    def missing_documents(self) -> List[str]:
        """Get list of missing required documents."""
        # This would require checking documents table
        # For now, return empty list
        return []

    def transition_to_status(self, new_status: str) -> bool:
        """
        Check if status transition is valid.

        Args:
            new_status: Target status

        Returns:
            bool: True if transition is valid
        """
        valid_transitions = {
            InscriptionStatut.BROUILLON: [
                InscriptionStatut.EN_ATTENTE_PAIEMENT,
                InscriptionStatut.ANNULEE
            ],
            InscriptionStatut.EN_ATTENTE_PAIEMENT: [
                InscriptionStatut.PAIEMENT_PARTIEL,
                InscriptionStatut.ACTIVE,
                InscriptionStatut.ANNULEE
            ],
            InscriptionStatut.PAIEMENT_PARTIEL: [
                InscriptionStatut.ACTIVE,
                InscriptionStatut.ANNULEE
            ],
            InscriptionStatut.ACTIVE: [
                InscriptionStatut.ANNULEE
            ],
            InscriptionStatut.ANNULEE: []  # Terminal state
        }

        return new_status in valid_transitions.get(self.statut, [])


class InscriptionSummary(BaseModel):
    """Summary model for enrollment lists."""
    id: str
    numero_unique: str
    nom_enfant: str
    prenom_enfant: str
    annee_catechetique: str
    niveau: Optional[str]
    statut: str
    montant_total: Decimal
    montant_paye: Decimal
    solde_restant: Decimal
    created_at: datetime
    documents_count: int = 0
    paiements_count: int = 0

    @property
    def payment_progress_percentage(self) -> float:
        """Calculate payment progress as percentage."""
        if self.montant_total == 0:
            return 0
        return min(100, float((self.montant_paye / self.montant_total) * 100))

    @property
    def status_display(self) -> str:
        """Get human-readable status display."""
        status_map = {
            InscriptionStatut.BROUILLON: "Brouillon",
            InscriptionStatut.EN_ATTENTE_PAIEMENT: "En attente de paiement (5000 FCFA)",
            InscriptionStatut.PAIEMENT_PARTIEL: f"Paiement partiel",
            InscriptionStatut.ACTIVE: "Active",
            InscriptionStatut.ANNULEE: "Annulée"
        }
        return status_map.get(self.statut, self.statut)


class InscriptionFilter(BaseModel):
    """Filter parameters for enrollment queries."""
    statut: Optional[str] = None
    annee_catechetique: Optional[str] = None
    niveau: Optional[str] = None
    parent_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    nom_enfant: Optional[str] = None  # Partial name search
    include_legacy: bool = False  # Include legacy inscriptions_16 data

    def build_where_clause(self) -> tuple[str, List]:
        """
        Build SQL WHERE clause from filter parameters.

        Returns:
            tuple: (WHERE clause, parameters list)
        """
        conditions = []
        params = []

        if self.statut:
            conditions.append("statut = ?")
            params.append(self.statut)

        if self.annee_catechetique:
            conditions.append("annee_catechetique = ?")
            params.append(self.annee_catechetique)

        if self.niveau:
            conditions.append("niveau = ?")
            params.append(self.niveau)

        if self.parent_id:
            conditions.append("parent_id = ?")
            params.append(self.parent_id)

        if self.date_from:
            conditions.append("created_at >= ?")
            params.append(self.date_from.isoformat())

        if self.date_to:
            conditions.append("created_at <= ?")
            params.append(self.date_to.isoformat())

        if self.nom_enfant:
            conditions.append("(nom_enfant LIKE ? OR prenom_enfant LIKE ?)")
            search_term = f"%{self.nom_enfant}%"
            params.extend([search_term, search_term])

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        return where_clause, params


# Business logic validation functions
def validate_enrollment_eligibility(parent_id: str, annee_catechetique: str) -> Dict[str, Any]:
    """
    Validate if parent can create new enrollment.

    Args:
        parent_id: Parent user ID
        annee_catechetique: Target catechism year

    Returns:
        Dict: Validation result with details
    """
    # This would check for:
    # 1. Parent account status
    # 2. Existing enrollments for same year
    # 3. Payment compliance
    # 4. Other business rules

    return {
        "eligible": True,
        "restrictions": [],
        "message": "Parent eligible for new enrollment"
    }


def calculate_enrollment_amount() -> Decimal:
    """
    Get the fixed enrollment amount.

    Returns:
        Decimal: Fixed enrollment fee (5000 FCFA)
    """
    return Decimal('5000.00')