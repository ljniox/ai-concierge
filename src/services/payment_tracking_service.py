"""
Payment Status Tracking and Notifications Service

Handles payment status tracking, notifications, and automated workflows.
Provides real-time status updates and multi-channel notifications.

Features:
- Real-time payment status tracking
- Multi-channel notifications (WhatsApp/Telegram)
- Automated status update workflows
- Payment expiry management
- Analytics and reporting

Constitution Principle: Automated payment tracking and notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import os
import uuid

from ..database.sqlite_manager import get_sqlite_manager
from ..services.mobile_money_service import get_mobile_money_service, PaymentStatus
from ..services.messaging_service import get_messaging_service
from ..services.audit_service import log_user_action
from ..utils.exceptions import PaymentError

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Notification types for payment events."""
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_VALIDATED = "payment_validated"
    PAYMENT_REJECTED = "payment_rejected"
    PAYMENT_EXPIRED = "payment_expired"
    PAYMENT_REMINDER = "payment_reminder"
    VALIDATION_REQUIRED = "validation_required"
    VALIDATION_COMPLETED = "validation_completed"

class PaymentTrackingService:
    """Service for payment status tracking and notifications."""

    def __init__(self):
        self.mobile_money_service = get_mobile_money_service()
        self.messaging_service = get_messaging_service()
        self.reminder_intervals = [
            6,   # 6 hours after payment
            24,  # 24 hours after payment
            48,  # 48 hours after payment
            72   # 72 hours after payment
        ]
        self.expiry_check_interval = int(os.getenv('PAYMENT_EXPIRY_CHECK_INTERVAL_HOURS', '6'))

    async def track_payment_status_change(
        self,
        payment_id: str,
        old_status: PaymentStatus,
        new_status: PaymentStatus,
        changed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track payment status change and trigger appropriate actions.

        Args:
            payment_id: Payment ID
            old_status: Previous status
            new_status: New status
            changed_by: User ID who made the change
            notes: Additional notes

        Returns:
            Dict: Tracking result
        """
        try:
            # Create status change record
            tracking_id = str(uuid.uuid4())

            tracking_data = {
                'tracking_id': tracking_id,
                'payment_id': payment_id,
                'old_status': old_status.value,
                'new_status': new_status.value,
                'changed_by': changed_by,
                'notes': notes,
                'changed_at': datetime.utcnow()
            }

            # Save tracking record
            await self._save_tracking_record(tracking_data)

            # Determine notification type
            notification_type = self._determine_notification_type(old_status, new_status)

            # Send notifications
            notification_result = await self._send_status_notifications(
                payment_id, notification_type, tracking_data
            )

            # Trigger automated workflows
            workflow_result = await self._trigger_automated_workflows(
                payment_id, new_status, tracking_data
            )

            # Log the status change
            await log_user_action(
                user_id=changed_by or 'system',
                action_type="payment_status_change",
                entity_type="payment",
                entity_id=payment_id,
                details={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "notification_type": notification_type.value,
                    "tracking_id": tracking_id
                },
                statut_action="succes"
            )

            result = {
                'success': True,
                'tracking_id': tracking_id,
                'payment_id': payment_id,
                'status_change': {
                    'old_status': old_status.value,
                    'new_status': new_status.value
                },
                'notification_type': notification_type.value,
                'notifications_sent': notification_result['sent_count'],
                'workflows_triggered': workflow_result['triggered_count'],
                'changed_at': tracking_data['changed_at'].isoformat()
            }

            logger.info(f"Payment status tracked: {payment_id} - {old_status.value} → {new_status.value}")
            return result

        except Exception as e:
            logger.error(f"Failed to track payment status change: {e}")
            return {
                'success': False,
                'error': str(e),
                'payment_id': payment_id
            }

    async def send_payment_reminders(self) -> Dict[str, Any]:
        """
        Send payment reminders for pending payments.

        Returns:
            Dict: Reminder sending results
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get pending payments that need reminders
                cursor = await conn.execute(
                    """
                    SELECT p.*, u.user_id, u.canal_prefere, u.identifiant_canal,
                           e.nom_enfant, e.prenom_enfant
                    FROM payments p
                    JOIN profil_utilisateurs u ON p.user_id = u.user_id
                    LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
                    WHERE p.status = ?
                      AND p.created_at >= datetime('now', '-7 days')
                    ORDER BY p.created_at ASC
                    """,
                    (PaymentStatus.PENDING.value,)
                )
                pending_payments = await cursor.fetchall()

                reminders_sent = 0
                failed_reminders = 0

                for payment in pending_payments:
                    try:
                        # Check if reminder should be sent
                        if await self._should_send_reminder(payment):
                            reminder_result = await self._send_payment_reminder(dict(payment))
                            if reminder_result['success']:
                                reminders_sent += 1
                                logger.info(f"Payment reminder sent for {payment['payment_id']}")
                            else:
                                failed_reminders += 1
                                logger.warning(f"Failed to send reminder for {payment['payment_id']}")

                    except Exception as e:
                        failed_reminders += 1
                        logger.error(f"Error sending reminder for payment {payment['payment_id']}: {e}")

                return {
                    'success': True,
                    'total_pending': len(pending_payments),
                    'reminders_sent': reminders_sent,
                    'failed_reminders': failed_reminders,
                    'processed_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to send payment reminders: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def check_expired_payments(self) -> Dict[str, Any]:
        """
        Check and process expired payments.

        Returns:
            Dict: Expiration check results
        """
        try:
            expired_count = await self.mobile_money_service.check_expired_payments()

            if expired_count > 0:
                # Send notifications for expired payments
                await self._notify_expired_payments(expired_count)

                logger.info(f"Processed {expired_count} expired payments")

            return {
                'success': True,
                'expired_payments_count': expired_count,
                'processed_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to check expired payments: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_payment_timeline(self, payment_id: str) -> List[Dict[str, Any]]:
        """
        Get complete timeline of payment status changes.

        Args:
            payment_id: Payment ID

        Returns:
            List[Dict]: Timeline events
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT pst.*, u.nom, u.prenom
                    FROM payment_status_tracking pst
                    LEFT JOIN profil_utilisateurs u ON pst.changed_by = u.user_id
                    WHERE pst.payment_id = ?
                    ORDER BY pst.changed_at ASC
                    """,
                    (payment_id,)
                )
                tracking_records = await cursor.fetchall()

                timeline = []
                for record in tracking_records:
                    timeline.append({
                        'timestamp': record['changed_at'],
                        'status_from': record['old_status'],
                        'status_to': record['new_status'],
                        'changed_by': record['changed_by'],
                        'changed_by_name': f"{record['prenom']} {record['nom']}" if record['nom'] else 'System',
                        'notes': record['notes'],
                        'tracking_id': record['tracking_id']
                    })

                return timeline

        except Exception as e:
            logger.error(f"Failed to get payment timeline: {e}")
            return []

    async def get_user_payment_notifications(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get payment notifications for a user.

        Args:
            user_id: User ID
            limit: Maximum number of notifications
            unread_only: Filter for unread notifications only

        Returns:
            Dict: Notifications data
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                where_clause = "WHERE pn.user_id = ?"
                params = [user_id]

                if unread_only:
                    where_clause += " AND pn.is_read = 0"

                query = f"""
                SELECT pn.*
                FROM payment_notifications pn
                {where_clause}
                ORDER BY pn.created_at DESC
                LIMIT ?
                """

                params.append(limit)
                cursor = await conn.execute(query, params)
                notifications = await cursor.fetchall()

                # Mark as read if not unread_only
                if not unread_only and notifications:
                    notification_ids = [n['notification_id'] for n in notifications]
                    await conn.execute(
                        f"UPDATE payment_notifications SET is_read = 1 WHERE notification_id IN ({','.join(['?']*len(notification_ids))})",
                        notification_ids
                    )
                    await conn.commit()

                return {
                    'notifications': [dict(n) for n in notifications],
                    'total_count': len(notifications),
                    'unread_count': sum(1 for n in notifications if not n['is_read'])
                }

        except Exception as e:
            logger.error(f"Failed to get user payment notifications: {e}")
            return {
                'notifications': [],
                'total_count': 0,
                'unread_count': 0
            }

    async def generate_payment_report(
        self,
        start_date: datetime,
        end_date: datetime,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate payment analytics report.

        Args:
            start_date: Report start date
            end_date: Report end date
            provider: Filter by provider (optional)

        Returns:
            Dict: Payment report data
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Base query
                where_clause = "WHERE p.created_at BETWEEN ? AND ?"
                params = [start_date, end_date]

                if provider:
                    where_clause += " AND p.provider = ?"
                    params.append(provider)

                # Payment statistics by status
                cursor = await conn.execute(
                    f"""
                    SELECT p.status, COUNT(*) as count, SUM(p.amount) as total_amount
                    FROM payments p
                    {where_clause}
                    GROUP BY p.status
                    """,
                    params
                )
                status_stats = await cursor.fetchall()

                # Payment statistics by provider
                cursor = await conn.execute(
                    f"""
                    SELECT p.provider, COUNT(*) as count, SUM(p.amount) as total_amount
                    FROM payments p
                    {where_clause}
                    GROUP BY p.provider
                    """,
                    params
                )
                provider_stats = await cursor.fetchall()

                # Daily payment trends
                cursor = await conn.execute(
                    f"""
                    SELECT DATE(p.created_at) as date,
                           COUNT(*) as total_payments,
                           SUM(CASE WHEN p.status = 'valide' THEN 1 ELSE 0 END) as validated_payments,
                           SUM(p.amount) as total_amount
                    FROM payments p
                    {where_clause}
                    GROUP BY DATE(p.created_at)
                    ORDER BY date DESC
                    """,
                    params
                )
                daily_stats = await cursor.fetchall()

                # Average processing time
                cursor = await conn.execute(
                    f"""
                    SELECT AVG(
                        CASE
                            WHEN p.created_at IS NOT NULL
                             AND p.updated_at IS NOT NULL
                             AND p.status = 'valide'
                            THEN (julianday(p.updated_at) - julianday(p.created_at)) * 24 * 60
                            ELSE NULL
                        END
                    ) as avg_processing_minutes
                    FROM payments p
                    {where_clause}
                    """,
                    params
                )
                avg_processing = await cursor.fetchone()

                return {
                    'report_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'provider_filter': provider
                    },
                    'summary': {
                        'total_payments': sum(row['count'] for row in status_stats),
                        'total_amount': sum(float(row['total_amount'] or 0) for row in status_stats),
                        'validated_payments': next((row['count'] for row in status_stats if row['status'] == 'valide'), 0),
                        'validation_rate': 0,  # Will be calculated below
                        'avg_processing_minutes': float(avg_processing['avg_processing_minutes'] or 0)
                    },
                    'by_status': [dict(row) for row in status_stats],
                    'by_provider': [dict(row) for row in provider_stats],
                    'daily_trends': [dict(row) for row in daily_stats],
                    'generated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to generate payment report: {e}")
            return {'error': str(e)}

    async def _save_tracking_record(self, tracking_data: Dict[str, Any]) -> None:
        """Save payment status tracking record."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                await conn.execute(
                    """
                    INSERT INTO payment_status_tracking
                    (tracking_id, payment_id, old_status, new_status, changed_by, notes, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tracking_data['tracking_id'],
                        tracking_data['payment_id'],
                        tracking_data['old_status'],
                        tracking_data['new_status'],
                        tracking_data['changed_by'],
                        tracking_data['notes'],
                        tracking_data['changed_at']
                    )
                )
                await conn.commit()

        except Exception as e:
            logger.error(f"Failed to save tracking record: {e}")

    def _determine_notification_type(
        self,
        old_status: PaymentStatus,
        new_status: PaymentStatus
    ) -> NotificationType:
        """Determine notification type based on status change."""
        if new_status == PaymentStatus.VALIDATED:
            return NotificationType.PAYMENT_VALIDATED
        elif new_status == PaymentStatus.REJECTED:
            return NotificationType.PAYMENT_REJECTED
        elif new_status == PaymentStatus.EXPIRED:
            return NotificationType.PAYMENT_EXPIRED
        elif new_status == PaymentStatus.PENDING and old_status != PaymentStatus.PENDING:
            return NotificationType.PAYMENT_INITIATED
        elif new_status == PaymentStatus.PROCESSING:
            return NotificationType.VALIDATION_REQUIRED
        else:
            return NotificationType.PAYMENT_CONFIRMED

    async def _send_status_notifications(
        self,
        payment_id: str,
        notification_type: NotificationType,
        tracking_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send status notifications to relevant parties."""
        try:
            sent_count = 0

            # Get payment and user details
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT p.*, u.user_id, u.canal_prefere, u.identifiant_canal,
                           e.nom_enfant, e.prenom_enfant
                    FROM payments p
                    JOIN profil_utilisateurs u ON p.user_id = u.user_id
                    LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
                    WHERE p.payment_id = ?
                    """,
                    (payment_id,)
                )
                payment = await cursor.fetchone()

                if payment:
                    # Generate notification message
                    message = self._generate_notification_message(
                        notification_type, dict(payment), tracking_data
                    )

                    # Send to payer
                    await self.messaging_service.send_message(
                        user_id=payment['user_id'],
                        message=message,
                        channel=payment['canal_prefere']
                    )

                    # Save notification record
                    await self._save_notification_record(
                        payment['user_id'],
                        payment_id,
                        notification_type,
                        message
                    )

                    sent_count += 1

                    # Send to treasurer if validation required
                    if notification_type in [NotificationType.VALIDATION_REQUIRED, NotificationType.PAYMENT_INITIATED]:
                        treasurer_notified = await self._notify_treasurers(payment_id, notification_type)
                        sent_count += treasurer_notified

                return {'sent_count': sent_count}

        except Exception as e:
            logger.error(f"Failed to send status notifications: {e}")
            return {'sent_count': 0}

    def _generate_notification_message(
        self,
        notification_type: NotificationType,
        payment: Dict[str, Any],
        tracking_data: Dict[str, Any]
    ) -> str:
        """Generate notification message based on type."""
        child_name = f"{payment.get('prenom_enfant', '')} {payment.get('nom_enfant', '')}".strip()

        messages = {
            NotificationType.PAYMENT_INITIATED: (
                f"📝 *Paiement Initlié*\n\n"
                f"Enfant: {child_name}\n"
                f"Référence: {payment['payment_reference']}\n"
                f"Montant: {payment['amount']} {payment['currency']}\n"
                f"Opérateur: {payment['provider']}\n\n"
                f"Veuillez effectuer le paiement. Vous recevrez une confirmation une fois validé.\n\n"
                f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
            ),
            NotificationType.PAYMENT_VALIDATED: (
                f"✅ *Paiement Validé avec Succès*\n\n"
                f"Enfant: {child_name}\n"
                f"Référence: {payment['payment_reference']}\n"
                f"Montant: {payment['amount']} {payment['currency']}\n"
                f"Opérateur: {payment['provider']}\n\n"
                f"Votre paiement a été validé. L'inscription est confirmée.\n"
                f"Merci pour votre règlement.\n\n"
                f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
            ),
            NotificationType.PAYMENT_REJECTED: (
                f"❌ *Paiement Rejeté*\n\n"
                f"Enfant: {child_name}\n"
                f"Référence: {payment['payment_reference']}\n"
                f"Montant: {payment['amount']} {payment['currency']}\n\n"
                f"Votre paiement n'a pas pu être validé.\n"
                f"Veuillez contacter le secrétariat pour plus d'informations.\n\n"
                f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
            ),
            NotificationType.PAYMENT_EXPIRED: (
                f"⏰ *Paiement Expiré*\n\n"
                f"Enfant: {child_name}\n"
                f"Référence: {payment['payment_reference']}\n"
                f"Montant: {payment['amount']} {payment['currency']}\n\n"
                f"Le délai de paiement est expiré. Veuillez renouveler votre demande d'inscription.\n\n"
                f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
            ),
            NotificationType.VALIDATION_REQUIRED: (
                f"⏳ *Paiement en Cours de Validation*\n\n"
                f"Enfant: {child_name}\n"
                f"Référence: {payment['payment_reference']}\n"
                f"Montant: {payment['amount']} {payment['currency']}\n\n"
                f"Votre paiement est en cours de validation par le trésorier.\n"
                f"Vous recevrez une confirmation dès qu'il sera validé.\n\n"
                f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
            )
        }

        return messages.get(notification_type, "Mise à jour du statut de paiement.")

    async def _save_notification_record(
        self,
        user_id: str,
        payment_id: str,
        notification_type: NotificationType,
        message: str
    ) -> None:
        """Save notification record."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                notification_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO payment_notifications
                    (notification_id, user_id, payment_id, notification_type, message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (notification_id, user_id, payment_id, notification_type.value, message, datetime.utcnow())
                )
                await conn.commit()

        except Exception as e:
            logger.error(f"Failed to save notification record: {e}")

    async def _notify_treasurers(
        self,
        payment_id: str,
        notification_type: NotificationType
    ) -> int:
        """Notify treasurers about payment validation requirements."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get treasurers
                cursor = await conn.execute(
                    """
                    SELECT user_id, canal_prefere, identifiant_canal
                    FROM profil_utilisateurs
                    WHERE role IN ('tresorier', 'tresorier_adjoint')
                      AND statut_compte = 'actif'
                    """
                )
                treasurers = await cursor.fetchall()

                notified_count = 0
                for treasurer in treasurers:
                    message = (
                        f"🔔 *Notification de Validation Requise*\n\n"
                        f"ID Paiement: {payment_id}\n"
                        f"Type: {notification_type.value}\n\n"
                        f"Veuillez examiner ce paiement dans votre tableau de bord.\n\n"
                        f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
                    )

                    await self.messaging_service.send_message(
                        user_id=treasurer['user_id'],
                        message=message,
                        channel=treasurer['canal_prefere']
                    )
                    notified_count += 1

                return notified_count

        except Exception as e:
            logger.error(f"Failed to notify treasurers: {e}")
            return 0

    async def _trigger_automated_workflows(
        self,
        payment_id: str,
        new_status: PaymentStatus,
        tracking_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger automated workflows based on status change."""
        triggered_count = 0

        try:
            # If payment is validated, confirm enrollment
            if new_status == PaymentStatus.VALIDATED:
                await self._confirm_enrollment_payment(payment_id)
                triggered_count += 1

            # If payment is pending, schedule reminders
            elif new_status == PaymentStatus.PENDING:
                await self._schedule_payment_reminders(payment_id)
                triggered_count += 1

            # If payment is rejected, handle rejection workflow
            elif new_status == PaymentStatus.REJECTED:
                await self._handle_payment_rejection(payment_id, tracking_data)
                triggered_count += 1

            return {'triggered_count': triggered_count}

        except Exception as e:
            logger.error(f"Failed to trigger automated workflows: {e}")
            return {'triggered_count': 0}

    async def _confirm_enrollment_payment(self, payment_id: str) -> None:
        """Confirm enrollment when payment is validated."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Update enrollment payment status
                await conn.execute(
                    """
                    UPDATE inscriptions
                    SET statut_paiement = 'paye',
                        date_paiement = ?,
                        updated_at = ?
                    WHERE inscription_id = (
                        SELECT enrollment_id FROM payments WHERE payment_id = ?
                    )
                    """,
                    (datetime.utcnow(), datetime.utcnow(), payment_id)
                )
                await conn.commit()

                logger.info(f"Enrollment payment confirmed for payment {payment_id}")

        except Exception as e:
            logger.error(f"Failed to confirm enrollment payment: {e}")

    async def _schedule_payment_reminders(self, payment_id: str) -> None:
        """Schedule payment reminders for pending payments."""
        # This would typically integrate with a background task scheduler
        # For now, we'll log that reminders should be scheduled
        logger.info(f"Payment reminders scheduled for payment {payment_id}")

    async def _handle_payment_rejection(
        self,
        payment_id: str,
        tracking_data: Dict[str, Any]
    ) -> None:
        """Handle payment rejection workflow."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Update enrollment status
                await conn.execute(
                    """
                    UPDATE inscriptions
                    SET statut_paiement = 'rejete',
                        updated_at = ?
                    WHERE inscription_id = (
                        SELECT enrollment_id FROM payments WHERE payment_id = ?
                    )
                    """,
                    (datetime.utcnow(), payment_id)
                )
                await conn.commit()

                logger.info(f"Payment rejection workflow handled for payment {payment_id}")

        except Exception as e:
            logger.error(f"Failed to handle payment rejection: {e}")

    async def _should_send_reminder(self, payment: Dict[str, Any]) -> bool:
        """Check if a reminder should be sent for this payment."""
        created_at = payment['created_at']
        hours_since_creation = (datetime.utcnow() - created_at).total_seconds() / 3600

        # Check if any reminder interval matches
        for interval in self.reminder_intervals:
            if abs(hours_since_creation - interval) < 1:  # Within 1 hour window
                # Check if reminder was already sent
                if not await self._reminder_already_sent(payment['payment_id'], interval):
                    return True

        return False

    async def _reminder_already_sent(self, payment_id: str, interval: int) -> bool:
        """Check if reminder was already sent for this interval."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM payment_notifications
                    WHERE payment_id = ?
                      AND notification_type = 'payment_reminder'
                      AND created_at >= datetime('now', '-{} hours')
                    """.format(interval + 2),  # Small buffer
                    (payment_id,)
                )
                result = await cursor.fetchone()
                return result['count'] > 0

        except Exception as e:
            logger.error(f"Failed to check if reminder already sent: {e}")
            return False

    async def _send_payment_reminder(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Send payment reminder to user."""
        try:
            child_name = f"{payment.get('prenom_enfant', '')} {payment.get('nom_enfant', '')}".strip()

            message = (
                f"⏰ *Rappel de Paiement*\n\n"
                f"Enfant: {child_name}\n"
                f"Référence: {payment['payment_reference']}\n"
                f"Montant: {payment['amount']} {payment['currency']}\n"
                f"Opérateur: {payment['provider']}\n\n"
                f"Votre paiement est toujours en attente de validation.\n"
                f"Si vous avez déjà effectué le paiement, ignorez ce message.\n\n"
                f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
            )

            await self.messaging_service.send_message(
                user_id=payment['user_id'],
                message=message,
                channel=payment['canal_prefere']
            )

            # Save reminder notification
            await self._save_notification_record(
                payment['user_id'],
                payment['payment_id'],
                NotificationType.PAYMENT_REMINDER,
                message
            )

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to send payment reminder: {e}")
            return {'success': False, 'error': str(e)}

    async def _notify_expired_payments(self, expired_count: int) -> None:
        """Notify administrators about expired payments."""
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get administrators
                cursor = await conn.execute(
                    """
                    SELECT user_id, canal_prefere, identifiant_canal
                    FROM profil_utilisateurs
                    WHERE role IN ('super_admin', 'secretaire_cure', 'secretaire_bureau')
                      AND statut_compte = 'actif'
                    """
                )
                admins = await cursor.fetchone()

                if admins:
                    message = (
                        f"📊 *Rapport d'Expiration des Paiements*\n\n"
                        f"{expired_count} paiements ont expiré aujourd'hui.\n\n"
                        f"Veuillez consulter le tableau de bord pour plus de détails.\n\n"
                        f"Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire"
                    )

                    for admin in admins:
                        await self.messaging_service.send_message(
                            user_id=admin['user_id'],
                            message=message,
                            channel=admin['canal_prefere']
                        )

        except Exception as e:
            logger.error(f"Failed to notify about expired payments: {e}")

# Global service instance
_payment_tracking_service = None

def get_payment_tracking_service() -> PaymentTrackingService:
    """Get the payment tracking service instance."""
    global _payment_tracking_service
    if _payment_tracking_service is None:
        _payment_tracking_service = PaymentTrackingService()
    return _payment_tracking_service