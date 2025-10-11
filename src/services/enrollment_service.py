"""
Enrollment Service - Core Business Logic

Manages student enrollments with OCR integration, document validation,
and status management. Fixed fee of 5000 FCFA per enrollment.

Features:
- Enrollment creation and management (5000 FCFA flat fee)
- Document validation workflow
- Legacy parent code integration
- Status transitions and business rules
- Conflict detection and resolution

Constitution Principle: Business logic validation and comprehensive error handling
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal

from ..database.sqlite_manager import get_sqlite_manager
from ..models.enrollment import Inscription, InscriptionCreate, InscriptionUpdate, InscriptionStatut
from ..models.legacy import LegacyParent, LegacyDataQueries
from ..models.base import DatabaseModel
from ..services.audit_service import log_user_action
from ..services.document_storage_service import get_document_storage_service
from ..utils.exceptions import BusinessLogicError, ValidationError, DatabaseError
from ..utils.validators import validate_french_date, validate_name

logger = logging.getLogger(__name__)


class EnrollmentService:
    """
    Core enrollment management service.

    Handles the complete enrollment lifecycle with:
    - Fixed fee calculation (5000 FCFA)
    - Legacy parent code integration
    - Document validation requirements
    - Status management and transitions
    - Business rule enforcement
    """

    def __init__(self):
        self.manager = get_sqlite_manager()
        self.document_storage = get_document_storage_service()
        self.fixed_enrollment_fee = Decimal('5000.00')

    async def create_enrollment(self, enrollment_data: InscriptionCreate, user_id: str) -> Inscription:
        """
        Create a new student enrollment.

        Args:
            enrollment_data: Enrollment creation data
            user_id: Creating user ID (parent)

        Returns:
            Inscription: Created enrollment record

        Business Rules:
        - Fixed fee: 5000 FCFA
        - Check for existing enrollments in same year
        - Validate parent permissions
        - Generate unique inscription number
        """
        try:
            # Validate business rules
            await self._validate_enrollment_eligibility(enrollment_data, user_id)

            # Check for conflicts
            await self._check_enrollment_conflicts(enrollment_data)

            # Generate unique inscription number
            numero_unique = await self._generate_inscription_number(enrollment_data.annee_catechetique)

            # Create enrollment record
            inscription_id = DatabaseModel.generate_uuid()

            enrollment = Inscription(
                id=inscription_id,
                numero_unique=numero_unique,
                parent_id=user_id,
                legacy_code_parent=enrollment_data.legacy_code_parent,
                legacy_catechumene_id=enrollment_data.legacy_catechumene_id,
                nom_enfant=enrollment_data.nom_enfant.strip().upper(),
                prenom_enfant=enrollment_data.prenom_enfant.strip(),
                date_naissance=enrollment_data.date_naissance,
                lieu_naissance=enrollment_data.lieu_naissance.strip(),
                date_bapteme=enrollment_data.date_bapteme,
                paroisse_bapteme=enrollment_data.paroisse_bapteme.strip() if enrollment_data.paroisse_bapteme else None,
                nom_pretre_bapteme=enrollment_data.nom_pretre_bapteme.strip() if enrollment_data.nom_pretre_bapteme else None,
                paroisse_origine=enrollment_data.paroisse_origine.strip() if enrollment_data.paroisse_origine else None,
                annee_catechisme_precedente=enrollment_data.annee_catechisme_precedente,
                annee_catechetique=enrollment_data.annee_catechetique,
                niveau=enrollment_data.niveau,
                statut=InscriptionStatut.BROUILLON,
                montant_total=self.fixed_enrollment_fee,
                montant_paye=Decimal('0.00'),
                notes=enrollment_data.notes.strip() if enrollment_data.notes else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=user_id
            )

            # Save to database
            await self._save_enrollment(inscription)

            # Log creation
            await log_user_action(
                user_id=user_id,
                action_type="create_inscription",
                entity_type="inscription",
                entity_id=inscription_id,
                details={
                    "numero_unique": numero_unique,
                    "nom_enfant": enrollment.nom_enfant,
                    "prenom_enfant": enrollment.prenom_enfant,
                    "annee_catechetique": enrollment.annee_catechetique,
                    "montant_total": float(self.fixed_enrollment_fee),
                    "required_documents": enrollment.requires_documents
                },
                statut_action="succes"
            )

            logger.info(f"Enrollment created: {numero_unique} for {enrollment.full_name}")
            return inscription

        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Enrollment creation failed: {e}")
            raise DatabaseError(f"Failed to create enrollment: {e}")

    async def update_enrollment(self, inscription_id: str, update_data: InscriptionUpdate,
                               user_id: str) -> Inscription:
        """
        Update an existing enrollment.

        Args:
            inscription_id: Enrollment ID
            update_data: Update data
            user_id: Updating user ID

        Returns:
            Inscription: Updated enrollment
        """
        try:
            # Get existing enrollment
            existing = await self.get_enrollment_by_id(inscription_id)

            # Check permissions and business rules
            await self._validate_update_permissions(existing, user_id)

            # Check if enrollment can be modified
            if not existing.can_be_modified:
                raise BusinessLogicError(
                    f"Enrollment {existing.numero_unique} cannot be modified in status: {existing.statut}"
                )

            # Apply updates
            updated_enrollment = await self._apply_enrollment_updates(existing, update_data, user_id)

            # Save updates
            await self._save_enrollment(updated_enrollment)

            # Log update
            await log_user_action(
                user_id=user_id,
                action_type="modify_inscription",
                entity_type="inscription",
                entity_id=inscription_id,
                details={
                    "numero_unique": updated_enrollment.numero_unique,
                    "changes": self._detect_changes(existing, updated_enrollment)
                },
                statut_action="succes"
            )

            logger.info(f"Enrollment updated: {updated_enrollment.numero_unique}")
            return updated_enrollment

        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Enrollment update failed: {e}")
            raise DatabaseError(f"Failed to update enrollment: {e}")

    async def transition_status(self, inscription_id: str, new_status: str, user_id: str,
                                reason: Optional[str] = None) -> Inscription:
        """
        Transition enrollment to new status.

        Args:
            inscription_id: Enrollment ID
            new_status: Target status
            user_id: User making the transition
            reason: Optional reason for transition

        Returns:
            Inscription: Updated enrollment
        """
        try:
            # Get existing enrollment
            existing = await self.get_enrollment_by_id(inscription_id)

            # Validate transition
            if not existing.transition_to_status(new_status):
                raise BusinessLogicError(
                    f"Invalid status transition from {existing.statut} to {new_status}"
                )

            # Apply status-specific business rules
            await self._apply_status_transition_rules(existing, new_status, user_id)

            # Update status
            existing.statut = new_status
            existing.updated_at = datetime.utcnow()

            # Add validation info if applicable
            if new_status == InscriptionStatut.ACTIVE:
                existing.validated_by = user_id
                existing.validated_at = datetime.utcnow()

            # Save changes
            await self._save_enrollment(existing)

            # Log status transition
            await log_user_action(
                user_id=user_id,
                action_type="status_transition",
                entity_type="inscription",
                entity_id=inscription_id,
                details={
                    "numero_unique": existing.numero_unique,
                    "old_status": existing.statut,
                    "new_status": new_status,
                    "reason": reason
                },
                statut_action="succes"
            )

            logger.info(f"Enrollment {existing.numero_unique} status: {existing.statut}")
            return existing

        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Status transition failed: {e}")
            raise DatabaseError(f"Failed to transition status: {e}")

    async def get_enrollment_by_id(self, inscription_id: str) -> Inscription:
        """
        Get enrollment by ID.

        Args:
            inscription_id: Enrollment ID

        Returns:
            Inscription: Enrollment record

        Raises:
            ValidationError: If enrollment not found
        """
        try:
            query = "SELECT * FROM inscriptions WHERE id = ?"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (inscription_id,))
                row = await cursor.fetchone()

            if not row:
                raise ValidationError(f"Enrollment not found: {inscription_id}")

            return Inscription.from_db_row(dict(row))

        except Exception as e:
            logger.error(f"Failed to get enrollment {inscription_id}: {e}")
            raise DatabaseError(f"Failed to retrieve enrollment: {e}")

    async def get_enrollments_by_parent(self, parent_id: str, filters: Optional[Dict] = None) -> List[Inscription]:
        """
        Get enrollments for a specific parent.

        Args:
            parent_id: Parent user ID
            filters: Optional filters

        Returns:
            List[Inscription]: Enrollment records
        """
        try:
            query = "SELECT * FROM inscriptions WHERE parent_id = ?"
            params = [parent_id]

            if filters:
                if 'annee_catechetique' in filters:
                    query += " AND annee_catechetique = ?"
                    params.append(filters['annee_catechetique'])

                if 'statut' in filters:
                    query += " AND statut = ?"
                    params.append(filters['statut'])

            query += " ORDER BY created_at DESC"

            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

            enrollments = []
            for row in rows:
                enrollment = Inscription.from_db_row(dict(row))
                enrollments.append(enrollment)

            return enrollments

        except Exception as e:
            logger.error(f"Failed to get enrollments for parent {parent_id}: {e}")
            raise DatabaseError(f"Failed to retrieve enrollments: {e}")

    async def search_enrollments(self, filters: Dict[str, Any], limit: int = 50,
                                offset: int = 0) -> Tuple[List[Inscription], int]:
        """
        Search enrollments with filters.

        Args:
            filters: Search filters
            limit: Maximum results
            offset: Results offset

        Returns:
            Tuple[List[Inscription], int]: Enrollments and total count
        """
        try:
            # Build WHERE clause
            conditions = []
            params = []

            if 'nom_enfant' in filters:
                conditions.append("(nom_enfant LIKE ? OR prenom_enfant LIKE ?)")
                search_term = f"%{filters['nom_enfant']}%"
                params.extend([search_term, search_term])

            if 'annee_catechetique' in filters:
                conditions.append("annee_catechetique = ?")
                params.append(filters['annee_catechetique'])

            if 'statut' in filters:
                conditions.append("statut = ?")
                params.append(filters['statut'])

            if 'parent_id' in filters:
                conditions.append("parent_id = ?")
                params.append(filters['parent_id'])

            if 'date_from' in filters:
                conditions.append("created_at >= ?")
                params.append(filters['date_from'].isoformat())

            if 'date_to' in filters:
                conditions.append("created_at <= ?")
                params.append(filters['date_to'].isoformat())

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM inscriptions {where_clause}"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(count_query, params)
                total = (await cursor.fetchone())['total']

            # Get paginated results
            query = f"""
            SELECT * FROM inscriptions {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            enrollments = []
            for row in rows:
                enrollment = Inscription.from_db_row(dict(row))
                enrollments.append(enrollment)

            return enrollments, total

        except Exception as e:
            logger.error(f"Enrollment search failed: {e}")
            raise DatabaseError(f"Search failed: {e}")

    async def _validate_enrollment_eligibility(self, enrollment_data: InscriptionCreate, user_id: str):
        """Validate enrollment eligibility and business rules."""
        # Check if user has parent role
        # This would involve checking the user's role in profil_utilisateurs
        # For now, assume user is validated at API level

        # Validate child's age for catechism
        age_years = (date.today() - enrollment_data.date_naissance).days / 365.25
        if age_years < 5 or age_years > 18:
            raise ValidationError(f"Child age ({age_years:.1f} years) outside catechism range (5-18 years)")

        # Validate baptism date if provided
        if enrollment_data.date_bapteme and enrollment_data.date_naissance:
            if enrollment_data.date_bapteme < enrollment_data.date_naissance:
                raise ValidationError("Baptism date cannot be before birth date")

        # Validate transfer requirements
        if enrollment_data.paroisse_origine and not enrollment_data.annee_catechisme_precedente:
            raise ValidationError("Previous catechism year required when coming from another parish")

    async def _check_enrollment_conflicts(self, enrollment_data: InscriptionCreate):
        """Check for existing enrollments that would conflict."""
        try:
            # Check for existing enrollment in same year for same child
            query = """
            SELECT COUNT(*) as count FROM inscriptions
            WHERE nom_enfant = ? AND prenom_enfant = ?
            AND date_naissance = ? AND annee_catechetique = ?
            AND statut != 'annulee'
            """

            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (
                    enrollment_data.nom_enfant.strip().upper(),
                    enrollment_data.prenom_enfant.strip(),
                    enrollment_data.date_naissance.isoformat(),
                    enrollment_data.annee_catechetique
                ))
                result = await cursor.fetchone()

            if result['count'] > 0:
                raise BusinessLogicError(
                    f"Child {enrollment_data.nom_enfant} {enrollment_data.prenom_enfant} "
                    f"already has an active enrollment for {enrollment_data.annee_catechetique}"
                )

            # Check legacy data conflicts if legacy codes provided
            if enrollment_data.legacy_catechumene_id:
                legacy_query = LegacyDataQueries.get_legacy_enrollment_conflict(
                    enrollment_data.legacy_code_parent or "",
                    enrollment_data.annee_catechetique
                )

                cursor = await conn.execute(legacy_query)
                legacy_result = await cursor.fetchone()

                if legacy_result:
                    raise BusinessLogicError(
                        "Legacy enrollment found for same parent and year. Please contact administration."
                    )

        except Exception as e:
            logger.error(f"Conflict check failed: {e}")
            raise

    async def _generate_inscription_number(self, annee_catechetique: str) -> str:
        """Generate unique inscription number for the year."""
        try:
            # Extract year from annee_catechetique (e.g., "2025-2026" -> "2025")
            year = annee_catechetique.split('-')[0]

            # Count existing enrollments for this year
            query = """
            SELECT COUNT(*) as count FROM inscriptions
            WHERE annee_catechetique = ?
            """

            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (annee_catechetique,))
                result = await cursor.fetchone()
                count = result['count'] + 1  # +1 for new enrollment

            # Generate number: CAT-YYYY-XXXX (4-digit zero-padded)
            numero_unique = f"CAT-{year}-{count:04d}"

            # Ensure uniqueness
            while await self._inscription_number_exists(numero_unique):
                count += 1
                numero_unique = f"CAT-{year}-{count:04d}"

            return numero_unique

        except Exception as e:
            logger.error(f"Failed to generate inscription number: {e}")
            raise DatabaseError(f"Failed to generate inscription number: {e}")

    async def _inscription_number_exists(self, numero_unique: str) -> bool:
        """Check if inscription number already exists."""
        try:
            query = "SELECT COUNT(*) as count FROM inscriptions WHERE numero_unique = ?"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (numero_unique,))
                result = await cursor.fetchone()
                return result['count'] > 0

        except Exception as e:
            logger.error(f"Failed to check inscription number: {e}")
            return False

    async def _save_enrollment(self, enrollment: Inscription):
        """Save enrollment to database."""
        try:
            query = """
            INSERT OR REPLACE INTO inscriptions (
                id, numero_unique, parent_id, legacy_code_parent, legacy_catechumene_id,
                nom_enfant, prenom_enfant, date_naissance, lieu_naissance,
                date_bapteme, paroisse_bapteme, nom_pretre_bapteme,
                paroisse_origine, annee_catechisme_precedente, annee_catechetique,
                niveau, classe_id, statut, montant_total, montant_paye,
                validated_by, validated_at, notes, created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            async with self.manager.get_connection('catechese') as conn:
                await conn.execute(query, (
                    enrollment.id,
                    enrollment.numero_unique,
                    enrollment.parent_id,
                    enrollment.legacy_code_parent,
                    enrollment.legacy_catechumene_id,
                    enrollment.nom_enfant,
                    enrollment.prenom_enfant,
                    enrollment.date_naissance.isoformat(),
                    enrollment.lieu_naissance,
                    enrollment.date_bapteme.isoformat() if enrollment.date_bapteme else None,
                    enrollment.paroisse_bapteme,
                    enrollment.nom_pretre_bapteme,
                    enrollment.paroisse_origine,
                    enrollment.annee_catechisme_precedente,
                    enrollment.annee_catechetique,
                    enrollment.niveau,
                    enrollment.classe_id,
                    enrollment.statut,
                    float(enrollment.montant_total),
                    float(enrollment.montant_paye),
                    enrollment.validated_by,
                    enrollment.validated_at.isoformat() if enrollment.validated_at else None,
                    enrollment.notes,
                    enrollment.created_at.isoformat(),
                    enrollment.updated_at.isoformat(),
                    enrollment.created_by
                ))
                await conn.commit()

        except Exception as e:
            logger.error(f"Failed to save enrollment: {e}")
            raise DatabaseError(f"Failed to save enrollment: {e}")

    async def _validate_update_permissions(self, existing: Inscription, user_id: str):
        """Validate user permissions to update enrollment."""
        # Parent can only update their own enrollments
        if existing.parent_id != user_id:
            # Check if user is admin/staff
            # This would involve checking user role in profil_utilisateurs
            # For now, raise error
            raise ValidationError("Permission denied: Cannot update enrollment")

    async def _apply_enrollment_updates(self, existing: Inscription, update_data: InscriptionUpdate,
                                      user_id: str) -> Inscription:
        """Apply updates to enrollment."""
        updated = existing

        # Apply allowed updates
        if update_data.nom_enfant is not None:
            updated.nom_enfant = update_data.nom_enfant.strip().upper()

        if update_data.prenom_enfant is not None:
            updated.prenom_enfant = update_data.prenom_enfant.strip()

        if update_data.date_naissance is not None:
            updated.date_naissance = update_data.date_naissance

        if update_data.lieu_naissance is not None:
            updated.lieu_naissance = update_data.lieu_naissance.strip()

        if update_data.date_bapteme is not None:
            updated.date_bapteme = update_data.date_bapteme

        if update_data.paroisse_bapteme is not None:
            updated.paroisse_bapteme = update_data.paroisse_bapteme.strip()

        if update_data.nom_pretre_bapteme is not None:
            updated.nom_pretre_bapteme = update_data.nom_pretre_bapteme.strip()

        if update_data.paroisse_origine is not None:
            updated.paroisse_origine = update_data.paroisse_origine.strip()

        if update_data.annee_catechisme_precedente is not None:
            updated.annee_catechisme_precedente = update_data.annee_catechisme_precedente

        if update_data.niveau is not None:
            updated.niveau = update_data.niveau

        if update_data.notes is not None:
            updated.notes = update_data.notes.strip() if update_data.notes else None

        updated.updated_at = datetime.utcnow()

        return updated

    async def _apply_status_transition_rules(self, enrollment: Inscription, new_status: str, user_id: str):
        """Apply business rules for status transitions."""
        if new_status == InscriptionStatut.EN_ATTENTE_PAIEMENT:
            # Check if required documents are uploaded
            # This would involve checking documents table
            pass

        elif new_status == InscriptionStatut.ACTIVE:
            # Check if payment is complete
            if not enrollment.is_paid:
                raise BusinessLogicError("Enrollment must be fully paid to activate")

            # Check if all required documents are validated
            # This would involve checking documents table
            pass

    def _detect_changes(self, old: Inscription, new: Inscription) -> Dict[str, Any]:
        """Detect changes between two enrollment versions."""
        changes = {}

        fields_to_compare = [
            'nom_enfant', 'prenom_enfant', 'date_naissance', 'lieu_naissance',
            'date_bapteme', 'paroisse_bapteme', 'nom_pretre_bapteme',
            'paroisse_origine', 'annee_catechisme_precedente', 'niveau',
            'notes', 'statut'
        ]

        for field in fields_to_compare:
            old_value = getattr(old, field, None)
            new_value = getattr(new, field, None)

            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None
                }

        return changes


# Global service instance
_enrollment_service_instance: Optional[EnrollmentService] = None


def get_enrollment_service() -> EnrollmentService:
    """Get global enrollment service instance."""
    global _enrollment_service_instance
    if _enrollment_service_instance is None:
        _enrollment_service_instance = EnrollmentService()
    return _enrollment_service_instance