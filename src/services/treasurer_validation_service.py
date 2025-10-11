"""
Treasurer Validation Workflow Service

Handles treasurer validation workflow for payment receipts.
Provides interface for treasurers to review, validate, or reject payments.

Features:
- Payment review queue management
- Receipt verification tools
- Validation/rejection workflow
- Multi-level approval system
- Audit trail and notifications

Constitution Principle: Manual treasurer validation for payment confirmation
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

from ..database.sqlite_manager import get_sqlite_manager
from ..services.mobile_money_service import get_mobile_money_service, PaymentStatus
from ..services.payment_ocr_service import get_payment_ocr_service
from ..services.audit_service import log_user_action
from ..services.messaging_service import get_messaging_service
from ..utils.exceptions import ValidationError, PaymentError

logger = logging.getLogger(__name__)

class ValidationAction(Enum):
    """Treasurer validation actions."""
    APPROVE = "approuver"
    REJECT = "rejeter"
    REQUEST_INFO = "demander_info"
    ESCALATE = "escalader"

class ValidationStatus(Enum):
    """Validation status enumeration."""
    PENDING_REVIEW = "en_attente_revision"
    UNDER_REVIEW = "en_revision"
    APPROVED = "approuve"
    REJECTED = "rejete"
    NEEDS_INFO = "informations_requises"
    ESCALATED = "escalade"

class TreasurerValidationService:
    """Service for treasurer validation workflow."""

    def __init__(self):
        self.mobile_money_service = get_mobile_money_service()
        self.payment_ocr_service = get_payment_ocr_service()
        self.messaging_service = get_messaging_service()
        self.review_timeout_hours = int(os.getenv('TREASURER_REVIEW_TIMEOUT_HOURS', '48'))

    async def get_validation_queue(
        self,
        treasurer_id: str,
        status: Optional[ValidationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get treasurer validation queue.

        Args:
            treasurer_id: Treasurer user ID
            status: Filter by validation status
            limit: Maximum number of items
            offset: Offset for pagination

        Returns:
            Dict: Validation queue data
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Build query with optional status filter
                where_clause = "WHERE pv.status = ?"
                params = [status.value] if status else []

                query = f"""
                SELECT
                    p.*,
                    pv.validation_id,
                    pv.status as validation_status,
                    pv.assigned_to,
                    pv.assigned_at,
                    pv.reviewed_by,
                    pv.reviewed_at,
                    pv.validation_notes,
                    pv.rejection_reason,
                    pv.escalation_level,
                    e.nom_enfant,
                    e.prenom_enfant,
                    u.nom as payer_name,
                    u.prenom as payer_prenom,
                    u.telephone as payer_phone
                FROM payments p
                JOIN payment_validations pv ON p.payment_id = pv.payment_id
                LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
                LEFT JOIN profil_utilisateurs u ON p.user_id = u.user_id
                {where_clause if params else ''}
                ORDER BY p.created_at ASC
                LIMIT ? OFFSET ?
                """

                params.extend([limit, offset])
                cursor = await conn.execute(query, params)
                payments = await cursor.fetchall()

                # Get total count
                count_query = f"""
                SELECT COUNT(*) as total
                FROM payments p
                JOIN payment_validations pv ON p.payment_id = pv.payment_id
                {where_clause if params[:-2] else ''}
                """
                count_params = params[:-2]  # Remove limit and offset
                count_cursor = await conn.execute(count_query, count_params)
                total_count = (await count_cursor.fetchone())['total']

                return {
                    'payments': [dict(payment) for payment in payments],
                    'total_count': total_count,
                    'page': offset // limit + 1,
                    'per_page': limit,
                    'has_more': offset + len(payments) < total_count
                }

        except Exception as e:
            logger.error(f"Failed to get validation queue: {e}")
            return {
                'payments': [],
                'total_count': 0,
                'page': 1,
                'per_page': limit,
                'has_more': False,
                'error': str(e)
            }

    async def assign_payment_to_treasurer(
        self,
        payment_id: str,
        treasurer_id: str,
        assigned_by: str
    ) -> bool:
        """
        Assign a payment to a treasurer for review.

        Args:
            payment_id: Payment ID
            treasurer_id: Treasurer user ID
            assigned_by: User ID making the assignment

        Returns:
            bool: True if assigned successfully
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Check if payment exists and needs validation
                cursor = await conn.execute(
                    "SELECT * FROM payments WHERE payment_id = ? AND status = ?",
                    (payment_id, PaymentStatus.PENDING.value)
                )
                payment = await cursor.fetchone()

                if not payment:
                    logger.warning(f"Payment {payment_id} not found or not pending")
                    return False

                # Create or update validation record
                validation_id = str(uuid.uuid4())

                await conn.execute(
                    """
                    INSERT OR REPLACE INTO payment_validations
                    (validation_id, payment_id, status, assigned_to, assigned_at, assigned_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        validation_id,
                        payment_id,
                        ValidationStatus.PENDING_REVIEW.value,
                        treasurer_id,
                        datetime.utcnow(),
                        assigned_by,
                        datetime.utcnow()
                    )
                )
                await conn.commit()

                # Log assignment
                await log_user_action(
                    user_id=assigned_by,
                    action_type="assign_payment_validation",
                    entity_type="payment_validation",
                    entity_id=validation_id,
                    details={
                        "payment_id": payment_id,
                        "assigned_to": treasurer_id
                    },
                    statut_action="succes"
                )

                # Notify treasurer
                await self._notify_treasurer_assignment(treasurer_id, payment_id)

                logger.info(f"Payment {payment_id} assigned to treasurer {treasurer_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to assign payment to treasurer: {e}")
            return False

    async def validate_payment(
        self,
        validation_id: str,
        treasurer_id: str,
        action: ValidationAction,
        notes: Optional[str] = None,
        receipt_ocr_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process treasurer validation action.

        Args:
            validation_id: Validation record ID
            treasurer_id: Treasurer user ID
            action: Validation action
            notes: Validation notes
            receipt_ocr_result: OCR processing result (if available)

        Returns:
            Dict: Validation result
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get validation record
                cursor = await conn.execute(
                    """
                    SELECT pv.*, p.*
                    FROM payment_validations pv
                    JOIN payments p ON pv.payment_id = p.payment_id
                    WHERE pv.validation_id = ? AND pv.assigned_to = ?
                    """,
                    (validation_id, treasurer_id)
                )
                validation = await cursor.fetchone()

                if not validation:
                    raise ValidationError("Validation record not found or not assigned to this treasurer")

                # Update validation record
                validation_updates = {
                    'status': self._map_action_to_status(action),
                    'reviewed_by': treasurer_id,
                    'reviewed_at': datetime.utcnow(),
                    'validation_notes': notes
                }

                if action == ValidationAction.REJECT:
                    validation_updates['rejection_reason'] = notes
                elif action == ValidationAction.ESCALATE:
                    validation_updates['escalation_level'] = (validation['escalation_level'] or 0) + 1

                # Build update query
                set_clause = ', '.join([f"{k} = ?" for k in validation_updates.keys()])
                values = list(validation_updates.values()) + [validation_id]

                await conn.execute(
                    f"UPDATE payment_validations SET {set_clause} WHERE validation_id = ?",
                    values
                )

                # Update payment status based on action
                new_payment_status = self._map_action_to_payment_status(action)
                await conn.execute(
                    "UPDATE payments SET status = ?, updated_at = ? WHERE payment_id = ?",
                    (new_payment_status.value, datetime.utcnow(), validation['payment_id'])
                )

                await conn.commit()

                # Log validation action
                await log_user_action(
                    user_id=treasurer_id,
                    action_type=f"payment_validation_{action.value}",
                    entity_type="payment_validation",
                    entity_id=validation_id,
                    details={
                        "payment_id": validation['payment_id'],
                        "action": action.value,
                        "notes": notes,
                        "receipt_ocr_confidence": receipt_ocr_result.get('overall_confidence') if receipt_ocr_result else None
                    },
                    statut_action="succes"
                )

                # Send notifications
                await self._send_validation_notifications(
                    validation['payment_id'],
                    action,
                    notes,
                    treasurer_id
                )

                result = {
                    'success': True,
                    'validation_id': validation_id,
                    'payment_id': validation['payment_id'],
                    'action': action.value,
                    'new_status': new_payment_status.value,
                    'processed_at': datetime.utcnow().isoformat()
                }

                logger.info(f"Payment validation processed: {validation_id} - {action.value}")
                return result

        except Exception as e:
            logger.error(f"Failed to validate payment: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_id': validation_id
            }

    async def process_receipt_with_ocr(
        self,
        validation_id: str,
        treasurer_id: str,
        receipt_image_path: str
    ) -> Dict[str, Any]:
        """
        Process payment receipt with OCR for validation.

        Args:
            validation_id: Validation record ID
            treasurer_id: Treasurer user ID
            receipt_image_path: Path to receipt image

        Returns:
            Dict: OCR processing result
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get payment details
                cursor = await conn.execute(
                    """
                    SELECT pv.*, p.*
                    FROM payment_validations pv
                    JOIN payments p ON pv.payment_id = p.payment_id
                    WHERE pv.validation_id = ? AND pv.assigned_to = ?
                    """,
                    (validation_id, treasurer_id)
                )
                validation = await cursor.fetchone()

                if not validation:
                    raise ValidationError("Validation record not found")

                # Process receipt with OCR
                ocr_result = await self.payment_ocr_service.process_payment_receipt(
                    receipt_image_path,
                    expected_amount=validation['amount'],
                    expected_provider=validation['provider']
                )

                # Store OCR result
                await conn.execute(
                    """
                    UPDATE payment_validations
                    SET receipt_ocr_result = ?, receipt_processed_at = ?
                    WHERE validation_id = ?
                    """,
                    (json.dumps(ocr_result), datetime.utcnow(), validation_id)
                )
                await conn.commit()

                # Log OCR processing
                await log_user_action(
                    user_id=treasurer_id,
                    action_type="process_receipt_ocr",
                    entity_type="payment_validation",
                    entity_id=validation_id,
                    details={
                        "payment_id": validation['payment_id'],
                        "ocr_confidence": ocr_result.get('overall_confidence'),
                        "extracted_reference": ocr_result.get('payment_info', {}).get('payment_reference'),
                        "validation_success": ocr_result.get('validation', {}).get('is_valid', False)
                    },
                    statut_action="succes"
                )

                logger.info(f"Receipt OCR processed for validation {validation_id}")
                return {
                    'success': True,
                    'validation_id': validation_id,
                    'ocr_result': ocr_result,
                    'processed_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to process receipt with OCR: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_id': validation_id
            }

    async def get_validation_details(self, validation_id: str, treasurer_id: str) -> Dict[str, Any]:
        """
        Get detailed validation information.

        Args:
            validation_id: Validation record ID
            treasurer_id: Treasurer user ID

        Returns:
            Dict: Validation details
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT
                        pv.*,
                        p.*,
                        e.nom_enfant,
                        e.prenom_enfant,
                        e.classe_inscription,
                        u.nom as payer_name,
                        u.prenom as payer_prenom,
                        u.telephone as payer_phone,
                        t.nom as treasurer_name,
                        t.prenom as treasurer_prenom
                    FROM payment_validations pv
                    JOIN payments p ON pv.payment_id = p.payment_id
                    LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
                    LEFT JOIN profil_utilisateurs u ON p.user_id = u.user_id
                    LEFT JOIN profil_utilisateurs t ON pv.assigned_to = t.user_id
                    WHERE pv.validation_id = ? AND pv.assigned_to = ?
                    """,
                    (validation_id, treasurer_id)
                )
                validation = await cursor.fetchone()

                if not validation:
                    return {'error': 'Validation record not found'}

                # Parse OCR result if exists
                ocr_result = None
                if validation['receipt_ocr_result']:
                    try:
                        ocr_result = json.loads(validation['receipt_ocr_result'])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid OCR result JSON for validation {validation_id}")

                return {
                    'validation': dict(validation),
                    'ocr_result': ocr_result,
                    'provider_info': self.mobile_money_service.get_provider_info(validation['provider'])
                }

        except Exception as e:
            logger.error(f"Failed to get validation details: {e}")
            return {'error': str(e)}

    async def escalate_payment(
        self,
        validation_id: str,
        treasurer_id: str,
        escalation_reason: str,
        escalate_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Escalate payment to higher authority.

        Args:
            validation_id: Validation record ID
            treasurer_id: Current treasurer user ID
            escalation_reason: Reason for escalation
            escalate_to: Target user ID (optional)

        Returns:
            Dict: Escalation result
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Update validation record
                await conn.execute(
                    """
                    UPDATE payment_validations
                    SET status = ?, escalation_level = escalation_level + 1,
                        escalation_reason = ?, escalated_by = ?, escalated_at = ?
                    WHERE validation_id = ?
                    """,
                    (
                        ValidationStatus.ESCALATED.value,
                        escalation_reason,
                        treasurer_id,
                        datetime.utcnow(),
                        validation_id
                    )
                )

                # If escalate_to specified, assign to that user
                if escalate_to:
                    await conn.execute(
                        """
                        UPDATE payment_validations
                        SET assigned_to = ?, assigned_at = ?
                        WHERE validation_id = ?
                        """,
                        (escalate_to, datetime.utcnow(), validation_id)
                    )

                await conn.commit()

                # Log escalation
                await log_user_action(
                    user_id=treasurer_id,
                    action_type="escalate_payment_validation",
                    entity_type="payment_validation",
                    entity_id=validation_id,
                    details={
                        "escalation_reason": escalation_reason,
                        "escalated_to": escalate_to
                    },
                    statut_action="succes"
                )

                # Notify escalation target
                if escalate_to:
                    await self._notify_treasurer_assignment(escalate_to, validation_id)

                logger.info(f"Payment validation escalated: {validation_id}")
                return {
                    'success': True,
                    'validation_id': validation_id,
                    'escalated_to': escalate_to,
                    'escalation_reason': escalation_reason
                }

        except Exception as e:
            logger.error(f"Failed to escalate payment: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_id': validation_id
            }

    async def get_validation_statistics(self, treasurer_id: str) -> Dict[str, Any]:
        """
        Get validation statistics for a treasurer.

        Args:
            treasurer_id: Treasurer user ID

        Returns:
            Dict: Validation statistics
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get validation counts by status
                cursor = await conn.execute(
                    """
                    SELECT pv.status, COUNT(*) as count
                    FROM payment_validations pv
                    WHERE pv.assigned_to = ?
                    GROUP BY pv.status
                    """,
                    (treasurer_id,)
                )
                status_counts = await cursor.fetchall()

                # Get daily validation stats for last 30 days
                cursor = await conn.execute(
                    """
                    SELECT DATE(pv.reviewed_at) as date,
                           COUNT(*) as total,
                           SUM(CASE WHEN pv.status = 'approuve' THEN 1 ELSE 0 END) as approved,
                           SUM(CASE WHEN pv.status = 'rejete' THEN 1 ELSE 0 END) as rejected
                    FROM payment_validations pv
                    WHERE pv.assigned_to = ?
                      AND pv.reviewed_at >= date('now', '-30 days')
                    GROUP BY DATE(pv.reviewed_at)
                    ORDER BY date DESC
                    """,
                    (treasurer_id,)
                )
                daily_stats = await cursor.fetchall()

                # Get average processing time
                cursor = await conn.execute(
                    """
                    SELECT AVG(
                        CASE
                            WHEN pv.assigned_at IS NOT NULL AND pv.reviewed_at IS NOT NULL
                            THEN (julianday(pv.reviewed_at) - julianday(pv.assigned_at)) * 24 * 60
                            ELSE NULL
                        END
                    ) as avg_processing_minutes
                    FROM payment_validations pv
                    WHERE pv.assigned_to = ? AND pv.reviewed_at IS NOT NULL
                    """,
                    (treasurer_id,)
                )
                avg_processing = await cursor.fetchone()

                return {
                    'by_status': [dict(row) for row in status_counts],
                    'daily_stats': [dict(row) for row in daily_stats],
                    'avg_processing_minutes': float(avg_processing['avg_processing_minutes'] or 0),
                    'total_validations': sum(row['count'] for row in status_counts)
                }

        except Exception as e:
            logger.error(f"Failed to get validation statistics: {e}")
            return {}

    def _map_action_to_status(self, action: ValidationAction) -> str:
        """Map validation action to status."""
        mapping = {
            ValidationAction.APPROVE: ValidationStatus.APPROVED.value,
            ValidationAction.REJECT: ValidationStatus.REJECTED.value,
            ValidationAction.REQUEST_INFO: ValidationStatus.NEEDS_INFO.value,
            ValidationAction.ESCALATE: ValidationStatus.ESCALATED.value
        }
        return mapping.get(action, ValidationStatus.PENDING_REVIEW.value)

    def _map_action_to_payment_status(self, action: ValidationAction) -> PaymentStatus:
        """Map validation action to payment status."""
        mapping = {
            ValidationAction.APPROVE: PaymentStatus.VALIDATED,
            ValidationAction.REJECT: PaymentStatus.REJECTED,
            ValidationAction.REQUEST_INFO: PaymentStatus.PROCESSING,
            ValidationAction.ESCALATE: PaymentStatus.PROCESSING
        }
        return mapping.get(action, PaymentStatus.PROCESSING)

    async def _notify_treasurer_assignment(self, treasurer_id: str, payment_id: str) -> None:
        """Notify treasurer of new payment assignment."""
        try:
            # Get treasurer communication details
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT telephone, canal_prefere, identifiant_canal
                    FROM profil_utilisateurs
                    WHERE user_id = ?
                    """,
                    (treasurer_id,)
                )
                treasurer = await cursor.fetchone()

                if treasurer:
                    message = (
                        f"📋 *Nouvelle validation de paiement requise*\n\n"
                        f"ID Paiement: {payment_id}\n"
                        f"Veuillez examiner et valider ce paiement dans votre tableau de bord.\n\n"
                        f"Merci de votre diligence.\n"
                        f"Gust-IA - Service Diocésain de la Catéchèse"
                    )

                    await self.messaging_service.send_message(
                        user_id=treasurer_id,
                        message=message,
                        channel=treasurer['canal_prefere']
                    )

        except Exception as e:
            logger.error(f"Failed to notify treasurer of assignment: {e}")

    async def _send_validation_notifications(
        self,
        payment_id: str,
        action: ValidationAction,
        notes: Optional[str],
        treasurer_id: str
    ) -> None:
        """Send validation notifications to payer."""
        try:
            # Get payment and payer details
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT p.*, u.user_id as payer_id, u.canal_prefere, u.identifiant_canal
                    FROM payments p
                    JOIN profil_utilisateurs u ON p.user_id = u.user_id
                    WHERE p.payment_id = ?
                    """,
                    (payment_id,)
                )
                payment = await cursor.fetchone()

                if payment:
                    messages = {
                        ValidationAction.APPROVE: (
                            f"✅ *Paiement Validé*\n\n"
                            f"Référence: {payment['payment_reference']}\n"
                            f"Montant: {payment['amount']} {payment['currency']}\n"
                            f"Statut: Validé par le trésorier\n\n"
                            f"L'inscription de votre enfant est maintenant confirmée.\n"
                            f"Merci pour votre paiement.\n\n"
                            f"Gust-IA - Service Diocésain de la Catéchèse"
                        ),
                        ValidationAction.REJECT: (
                            f"❌ *Paiement Rejeté*\n\n"
                            f"Référence: {payment['payment_reference']}\n"
                            f"Montant: {payment['amount']} {payment['currency']}\n"
                            f"Statut: Rejeté par le trésorier\n"
                            f"Motif: {notes or 'Non spécifié'}\n\n"
                            f"Veuillez contacter le secrétariat pour plus d'informations.\n\n"
                            f"Gust-IA - Service Diocésain de la Catéchèse"
                        ),
                        ValidationAction.REQUEST_INFO: (
                            f"⏳ *Informations Supplémentaires Requises*\n\n"
                            f"Référence: {payment['payment_reference']}\n"
                            f"Montant: {payment['amount']} {payment['currency']}\n\n"
                            f"Le trésorier a besoin d'informations supplémentaires:\n"
                            f"{notes or 'Veuillez contacter le secrétariat'}\n\n"
                            f"Gust-IA - Service Diocésain de la Catéchèse"
                        )
                    }

                    if action in messages:
                        await self.messaging_service.send_message(
                            user_id=payment['payer_id'],
                            message=messages[action],
                            channel=payment['canal_prefere']
                        )

        except Exception as e:
            logger.error(f"Failed to send validation notifications: {e}")

# Global service instance
_treasurer_validation_service = None

def get_treasurer_validation_service() -> TreasurerValidationService:
    """Get the treasurer validation service instance."""
    global _treasurer_validation_service
    if _treasurer_validation_service is None:
        _treasurer_validation_service = TreasurerValidationService()
    return _treasurer_validation_service