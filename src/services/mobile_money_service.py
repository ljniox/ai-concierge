"""
Mobile Money Payment Processing Service

Handles payment processing for multiple mobile money providers:
- Orange Money
- Wave
- Free Money (MTN)
- Wari

Features:
- Payment reference generation
- Payment validation via API
- Receipt OCR processing
- Payment status tracking
- Automatic notifications

Constitution Principle: Secure mobile money payment processing
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from enum import Enum
import json
import os

import aiohttp
import easyocr

from ..database.sqlite_manager import get_sqlite_manager
from ..utils.exceptions import ValidationError, PaymentError
from ..services.ocr_service import get_ocr_service
from ..services.audit_service import log_user_action

logger = logging.getLogger(__name__)

class PaymentProvider(Enum):
    """Mobile money providers available in Senegal."""
    ORANGE = "orange_money"
    WAVE = "wave"
    FREE_MONEY = "free_money"
    WARI = "wari"
    CORIS = "coris_money"
    PROPARCO = "proparco"

class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "en_attente"
    PROCESSING = "en_cours"
    VALIDATED = "valide"
    REJECTED = "rejete"
    EXPIRED = "expire"
    CANCELLED = "annule"

class MobileMoneyService:
    """Service for processing mobile money payments."""

    def __init__(self):
        self.enrollment_fee = Decimal('5000.00')  # Fixed fee as specified
        self.payment_timeout = int(os.getenv('PAYMENT_TIMEOUT_HOURS', '24'))
        self.ocr_service = get_ocr_service()

        # Payment reference patterns
        self.reference_patterns = {
            PaymentProvider.ORANGE: r'^(OM|CX)\d{8,12}$',
            PaymentProvider.WAVE: r'^WV\d{8,15}$',
            PaymentProvider.FREE_MONEY: r'^(FM|MTN)\d{8,12}$',
            PaymentProvider.WARI: r'^WR\d{8,12}$',
            PaymentProvider.CORIS: r'^CM\d{8,12}$',
            PaymentProvider.PROPARCO: r'^PP\d{8,12}$'
        }

        # Provider configurations
        self.provider_configs = {
            PaymentProvider.ORANGE: {
                'name': 'Orange Money',
                'short_code': 'OM',
                'prefixes': ['22177', '22178', '22176'],
                'color': '#FF6600',
                'logo_url': '/static/providers/orange_money.png'
            },
            PaymentProvider.WAVE: {
                'name': 'Wave',
                'short_code': 'WV',
                'prefixes': ['22177', '22178', '22176', '22170', '22133'],
                'color': '#00D4AA',
                'logo_url': '/static/providers/wave.png'
            },
            PaymentProvider.FREE_MONEY: {
                'name': 'Free Money',
                'short_code': 'FM',
                'prefixes': ['22176'],
                'color': '#E31E24',
                'logo_url': '/static/providers/free_money.png'
            },
            PaymentProvider.WARI: {
                'name': 'Wari',
                'short_code': 'WR',
                'prefixes': ['22177', '22178', '22176'],
                'color': '#0066CC',
                'logo_url': '/static/providers/wari.png'
            },
            PaymentProvider.CORIS: {
                'name': 'Coris Money',
                'short_code': 'CM',
                'prefixes': ['22177', '22178'],
                'color': '#FF9900',
                'logo_url': '/static/providers/coris_money.png'
            },
            PaymentProvider.PROPARCO: {
                'name': 'Proparco',
                'short_code': 'PP',
                'prefixes': ['22133'],
                'color': '#003366',
                'logo_url': '/static/providers/proparco.png'
            }
        }

    def generate_payment_reference(self, provider: PaymentProvider) -> str:
        """
        Generate a unique payment reference for the given provider.

        Args:
            provider: Mobile money provider

        Returns:
            str: Generated payment reference
        """
        config = self.provider_configs[provider]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8].upper()

        reference = f"{config['short_code']}{timestamp}{unique_id}"
        logger.info(f"Generated payment reference: {reference} for {provider.value}")

        return reference

    def validate_phone_number(self, phone: str, provider: PaymentProvider) -> bool:
        """
        Validate phone number for the given provider.

        Args:
            phone: Phone number to validate
            provider: Mobile money provider

        Returns:
            bool: True if valid
        """
        # Clean phone number
        clean_phone = re.sub(r'[^\d]', '', phone)

        # Add country code if missing
        if len(clean_phone) == 9 and clean_phone.startswith('7'):
            clean_phone = f'221{clean_phone}'
        elif len(clean_phone) == 12 and not clean_phone.startswith('221'):
            clean_phone = f'221{clean_phone[-9:]}'

        # Check against provider prefixes
        valid_prefixes = self.provider_configs[provider]['prefixes']
        return any(clean_phone.startswith(prefix) for prefix in valid_prefixes)

    def validate_payment_reference(self, reference: str, provider: Optional[PaymentProvider] = None) -> Tuple[bool, Optional[PaymentProvider]]:
        """
        Validate payment reference format.

        Args:
            reference: Payment reference to validate
            provider: Expected provider (optional)

        Returns:
            Tuple[bool, Optional[PaymentProvider]]: Valid and detected provider
        """
        reference = reference.strip().upper()

        for prov, pattern in self.reference_patterns.items():
            if re.match(pattern, reference):
                if provider and prov != provider:
                    return False, None
                return True, prov

        return False, None

    async def create_payment_record(
        self,
        enrollment_id: str,
        user_id: str,
        provider: PaymentProvider,
        phone_number: str,
        payment_reference: str
    ) -> Dict[str, Any]:
        """
        Create a payment record in the database.

        Args:
            enrollment_id: Enrollment ID
            user_id: User ID making the payment
            provider: Mobile money provider
            phone_number: Payer phone number
            payment_reference: Payment reference

        Returns:
            Dict: Payment record data
        """
        payment_id = str(uuid.uuid4())

        payment_data = {
            'payment_id': payment_id,
            'enrollment_id': enrollment_id,
            'user_id': user_id,
            'provider': provider.value,
            'phone_number': phone_number,
            'payment_reference': payment_reference,
            'amount': self.enrollment_fee,
            'currency': 'XOF',
            'status': PaymentStatus.PENDING.value,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=self.payment_timeout)
        }

        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Insert payment record
                columns = list(payment_data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = list(payment_data.values())

                query = f"""
                INSERT INTO payments ({', '.join(columns)})
                VALUES ({placeholders})
                """

                await conn.execute(query, values)
                await conn.commit()

                # Log payment creation
                await log_user_action(
                    user_id=user_id,
                    action_type="create_payment",
                    entity_type="payment",
                    entity_id=payment_id,
                    details={
                        "enrollment_id": enrollment_id,
                        "provider": provider.value,
                        "amount": float(self.enrollment_fee),
                        "reference": payment_reference
                    },
                    statut_action="succes"
                )

                logger.info(f"Created payment record: {payment_id}")

                return payment_data

        except Exception as e:
            logger.error(f"Failed to create payment record: {e}")
            raise PaymentError(f"Failed to create payment: {e}")

    async def validate_payment_with_provider(
        self,
        payment_reference: str,
        provider: PaymentProvider,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Validate payment with provider API (mock implementation).

        In production, this would integrate with actual provider APIs.

        Args:
            payment_reference: Payment reference to validate
            provider: Mobile money provider
            phone_number: Payer phone number

        Returns:
            Dict: Validation result
        """
        # Mock validation for demonstration
        # In production, integrate with actual provider APIs
        await asyncio.sleep(2)  # Simulate API call

        # Mock successful validation
        validation_result = {
            'reference': payment_reference,
            'provider': provider.value,
            'status': 'success',
            'amount': float(self.enrollment_fee),
            'currency': 'XOF',
            'transaction_date': datetime.utcnow().isoformat(),
            'validated_at': datetime.utcnow().isoformat(),
            'confirmation_code': str(uuid.uuid4())[:8].upper()
        }

        logger.info(f"Payment validation successful: {payment_reference}")

        return validation_result

    async def update_payment_status(
        self,
        payment_id: str,
        status: PaymentStatus,
        validation_data: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update payment status in database.

        Args:
            payment_id: Payment ID
            status: New status
            validation_data: Validation response data
            notes: Additional notes

        Returns:
            bool: True if updated successfully
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                update_data = {
                    'status': status.value,
                    'updated_at': datetime.utcnow()
                }

                if validation_data:
                    update_data['validation_data'] = json.dumps(validation_data)

                if notes:
                    update_data['notes'] = notes

                # Build update query
                set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
                values = list(update_data.values()) + [payment_id]

                query = f"UPDATE payments SET {set_clause} WHERE payment_id = ?"

                cursor = await conn.execute(query, values)
                await conn.commit()

                if cursor.rowcount > 0:
                    logger.info(f"Updated payment {payment_id} status to {status.value}")

                    # If payment is validated, update enrollment status
                    if status == PaymentStatus.VALIDATED:
                        await self._update_enrollment_payment_status(payment_id, True)

                    return True
                else:
                    logger.warning(f"Payment {payment_id} not found for status update")
                    return False

        except Exception as e:
            logger.error(f"Failed to update payment status: {e}")
            return False

    async def _update_enrollment_payment_status(self, payment_id: str, is_paid: bool) -> None:
        """
        Update enrollment payment status when payment is validated.

        Args:
            payment_id: Payment ID
            is_paid: Whether payment is completed
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get enrollment_id from payment
                cursor = await conn.execute(
                    "SELECT enrollment_id FROM payments WHERE payment_id = ?",
                    (payment_id,)
                )
                payment = await cursor.fetchone()

                if payment:
                    # Update enrollment payment status
                    await conn.execute(
                        "UPDATE inscriptions SET statut_paiement = ? WHERE inscription_id = ?",
                        ('paye' if is_paid else 'impaye', payment['enrollment_id'])
                    )
                    await conn.commit()

                    logger.info(f"Updated enrollment {payment['enrollment_id']} payment status")

        except Exception as e:
            logger.error(f"Failed to update enrollment payment status: {e}")

    async def get_payment_by_reference(self, payment_reference: str) -> Optional[Dict[str, Any]]:
        """
        Get payment record by reference.

        Args:
            payment_reference: Payment reference

        Returns:
            Optional[Dict]: Payment record or None
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    "SELECT * FROM payments WHERE payment_reference = ?",
                    (payment_reference,)
                )
                payment = await cursor.fetchone()

                if payment:
                    return dict(payment)
                return None

        except Exception as e:
            logger.error(f"Failed to get payment by reference: {e}")
            return None

    async def get_user_payments(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all payments for a user.

        Args:
            user_id: User ID

        Returns:
            List[Dict]: Payment records
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT p.*, e.nom_enfant, e.prenom_enfant
                    FROM payments p
                    LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
                    WHERE p.user_id = ?
                    ORDER BY p.created_at DESC
                    """,
                    (user_id,)
                )
                payments = await cursor.fetchall()

                return [dict(payment) for payment in payments]

        except Exception as e:
            logger.error(f"Failed to get user payments: {e}")
            return []

    async def get_pending_payments(self) -> List[Dict[str, Any]]:
        """
        Get all pending payments for treasurer validation.

        Returns:
            List[Dict]: Pending payment records
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    SELECT p.*, e.nom_enfant, e.prenom_enfant, u.nom, u.prenom
                    FROM payments p
                    LEFT JOIN inscriptions e ON p.enrollment_id = e.inscription_id
                    LEFT JOIN profil_utilisateurs u ON p.user_id = u.user_id
                    WHERE p.status = ?
                    ORDER BY p.created_at ASC
                    """,
                    (PaymentStatus.PENDING.value,)
                )
                payments = await cursor.fetchall()

                return [dict(payment) for payment in payments]

        except Exception as e:
            logger.error(f"Failed to get pending payments: {e}")
            return []

    async def check_expired_payments(self) -> int:
        """
        Check and mark expired payments.

        Returns:
            int: Number of payments marked as expired
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(
                    """
                    UPDATE payments
                    SET status = ?, updated_at = ?
                    WHERE status = ? AND expires_at < ?
                    """,
                    (PaymentStatus.EXPIRED.value, datetime.utcnow(),
                     PaymentStatus.PENDING.value, datetime.utcnow())
                )
                await conn.commit()

                expired_count = cursor.rowcount
                if expired_count > 0:
                    logger.info(f"Marked {expired_count} payments as expired")

                return expired_count

        except Exception as e:
            logger.error(f"Failed to check expired payments: {e}")
            return 0

    def get_provider_info(self, provider: PaymentProvider) -> Dict[str, Any]:
        """
        Get provider configuration information.

        Args:
            provider: Mobile money provider

        Returns:
            Dict: Provider information
        """
        return self.provider_configs[provider].copy()

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of all available payment providers.

        Returns:
            List[Dict]: Provider information
        """
        return [
            {
                'id': provider.value,
                'name': config['name'],
                'short_code': config['short_code'],
                'prefixes': config['prefixes'],
                'color': config['color'],
                'logo_url': config['logo_url']
            }
            for provider, config in self.provider_configs.items()
        ]

    async def get_payment_statistics(self) -> Dict[str, Any]:
        """
        Get payment processing statistics.

        Returns:
            Dict: Payment statistics
        """
        try:
            manager = get_sqlite_manager()
            async with manager.get_connection('catechese') as conn:
                # Get counts by status
                cursor = await conn.execute(
                    """
                    SELECT status, COUNT(*) as count, SUM(amount) as total
                    FROM payments
                    GROUP BY status
                    """
                )
                status_stats = await cursor.fetchall()

                # Get counts by provider
                cursor = await conn.execute(
                    """
                    SELECT provider, COUNT(*) as count, SUM(amount) as total
                    FROM payments
                    GROUP BY provider
                    """
                )
                provider_stats = await cursor.fetchall()

                # Get daily stats for last 30 days
                cursor = await conn.execute(
                    """
                    SELECT DATE(created_at) as date, COUNT(*) as count, SUM(amount) as total
                    FROM payments
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """
                )
                daily_stats = await cursor.fetchall()

                return {
                    'by_status': [dict(row) for row in status_stats],
                    'by_provider': [dict(row) for row in provider_stats],
                    'daily': [dict(row) for row in daily_stats],
                    'total_amount': float(self.enrollment_fee),
                    'currency': 'XOF'
                }

        except Exception as e:
            logger.error(f"Failed to get payment statistics: {e}")
            return {}

# Global service instance
_mobile_money_service = None

def get_mobile_money_service() -> MobileMoneyService:
    """Get the mobile money service instance."""
    global _mobile_money_service
    if _mobile_money_service is None:
        _mobile_money_service = MobileMoneyService()
    return _mobile_money_service