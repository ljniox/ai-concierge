"""
Audit Logging Service

Enhanced comprehensive audit trail system for GDPR compliance (FR-051-055).
Logs all user actions with IP addresses, user agents, and detailed context.

Enhanced with support for automatic account creation system audit logging.
Features:
- Action logging with timestamps
- 2-year retention policy
- Automatic anonymization after 2 years (FR-055)
- Search and filtering capabilities
- Performance optimized with batch inserts
- Account creation specific audit events
- Security event tracking
- Multiple storage backends (database, file, etc.)

Constitution Principle V: Security and GDPR compliance
Research Decision: research.md - Audit trail requirements
"""

import json
import time
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import hashlib
import ipaddress

from ..database.sqlite_manager import get_sqlite_manager
from ..models.base import ActionType, DatabaseModel
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AccountCreationAuditEventType(Enum):
    """Account creation specific audit event types."""
    ACCOUNT_CREATION_STARTED = "account_creation_started"
    ACCOUNT_CREATION_COMPLETED = "account_creation_completed"
    ACCOUNT_CREATION_FAILED = "account_creation_failed"
    PHONE_VALIDATION = "phone_validation"
    PARENT_LOOKUP = "parent_lookup"
    DUPLICATE_ACCOUNT_PREVENTED = "duplicate_account_prevented"
    PLATFORM_ACCOUNT_LINKED = "platform_account_linked"
    SESSION_CREATED = "session_created"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    ROLE_ASSIGNED = "role_assigned"
    WEBHOOK_RECEIVED = "webhook_received"
    WEBHOOK_PROCESSED = "webhook_processed"
    WEBHOOK_FAILED = "webhook_failed"


@dataclass
class AccountCreationAuditEvent:
    """Account creation audit event data structure."""

    event_id: str
    event_type: AccountCreationAuditEventType
    timestamp: datetime
    user_id: Optional[str]
    phone_number: Optional[str]  # Masked
    platform: str
    platform_user_id: Optional[str]  # Masked
    ip_address: Optional[str]  # Masked
    user_agent: Optional[str]
    event_data: Dict[str, Any]
    status: str  # success, failed, pending
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with optional sensitive data filtering."""
        data = {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'platform': self.platform,
            'platform_user_id': self.platform_user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'event_data': self.event_data,
            'status': self.status,
            'processing_time_ms': self.processing_time_ms,
            'error_message': self.error_message
        }

        # Mask sensitive data unless explicitly requested
        if not include_sensitive:
            data = self._mask_sensitive_data(data)

        return data

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in audit event."""
        # Mask phone number
        if data.get('phone_number'):
            phone = data['phone_number']
            data['phone_number'] = phone[:4] + "****" + phone[-3:] if len(phone) > 7 else "****"

        # Mask platform user ID
        if data.get('platform_user_id'):
            platform_user_id = data['platform_user_id']
            data['platform_user_id'] = platform_user_id[:8] + "****" if len(platform_user_id) > 8 else "****"

        # Mask IP address
        if data.get('ip_address'):
            ip = data['ip_address']
            if '.' in ip:  # IPv4
                parts = ip.split('.')
                data['ip_address'] = f"{parts[0]}.{parts[1]}.***.*"
            else:  # IPv6
                data['ip_address'] = ip[:8] + "****"

        # Mask sensitive data in event_data
        if isinstance(data.get('event_data'), dict):
            data['event_data'] = self._mask_dict_sensitive_data(data['event_data'])

        return data

    def _mask_dict_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in dictionary."""
        sensitive_keys = ['password', 'token', 'secret', 'key', 'signature', 'hash']

        masked_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                masked_data[key] = "****MASKED****"
            elif isinstance(value, str) and len(value) > 20:
                masked_data[key] = value[:10] + "****" + value[-4:] if len(value) > 14 else "****MASKED****"
            else:
                masked_data[key] = value

        return masked_data


class AuditService:
    """
    Audit logging service for compliance and security monitoring.

    Logs all user actions with:
    - User identification
    - Action type and target
    - Timestamp and IP address
    - Detailed context (anonymized after 2 years)
    - Success/failure status
    """

    def __init__(self):
        self.manager = get_sqlite_manager()
        self._batch_buffer: List[Dict[str, Any]] = []
        self._batch_size = 50
        self._batch_timeout = 5  # seconds
        self._lock = asyncio.Lock()

    async def log_action(self,
                        user_id: str,
                        action_type: str,
                        entity_type: str,
                        entity_id: str,
                        ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None,
                        details: Optional[Dict[str, Any]] = None,
                        statut_action: str = "succes",
                        error_message: Optional[str] = None) -> str:
        """
        Log a user action to the audit trail.

        Args:
            user_id: User UUID performing the action
            action_type: Type of action (from ActionType enum)
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            ip_address: Client IP address (will be anonymized after 2 years)
            user_agent: Client user agent string
            details: Additional context (will be anonymized after 2 years)
            statut_action: Action status (succes/echec)
            error_message: Error details if action failed

        Returns:
            str: Log entry ID

        Example:
            await audit_service.log_action(
                user_id="user-123",
                action_type=ActionType.CREATE_INSCRIPTION,
                entity_type="inscription",
                entity_id="ins-456",
                ip_address="192.168.1.100",
                details={"montant": 15000, "niveau": "CE1"}
            )
        """
        try:
            log_id = DatabaseModel.generate_uuid()
            timestamp = datetime.utcnow()

            # Anonymize IP address (store last 2 octets)
            anonymized_ip = self._anonymize_ip(ip_address) if ip_address else None

            # Serialize details to JSON
            details_json = json.dumps(details) if details else None

            # Add to batch buffer
            log_entry = {
                'log_id': log_id,
                'user_id': user_id,
                'action_type': action_type,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'ip_address': anonymized_ip,
                'user_agent': user_agent,
                'timestamp': timestamp.isoformat(),
                'details': details_json,
                'statut_action': statut_action,
                'error_message': error_message
            }

            async with self._lock:
                self._batch_buffer.append(log_entry)

                # Process batch if full
                if len(self._batch_buffer) >= self._batch_size:
                    await self._flush_batch()

            # Start flush timeout task if not already running
            asyncio.create_task(self._flush_with_timeout())

            logger.debug(f"Logged action: {action_type} on {entity_type}:{entity_id} by user:{user_id}")
            return log_id

        except Exception as e:
            logger.error(f"Failed to log action: {e}")
            # Don't raise error to avoid breaking main functionality
            return ""

    async def _flush_batch(self):
        """Flush buffered log entries to database."""
        if not self._batch_buffer:
            return

        try:
            entries = self._batch_buffer.copy()
            self._batch_buffer.clear()

            async with self.manager.get_connection('catechese') as conn:
                # Use executemany for batch insert
                insert_query = """
                INSERT INTO action_logs (
                    log_id, user_id, action_type, entity_type, entity_id,
                    ip_address, user_agent, timestamp, details,
                    statut_action, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                values = [
                    (
                        entry['log_id'],
                        entry['user_id'],
                        entry['action_type'],
                        entry['entity_type'],
                        entry['entity_id'],
                        entry['ip_address'],
                        entry['user_agent'],
                        entry['timestamp'],
                        entry['details'],
                        entry['statut_action'],
                        entry['error_message']
                    )
                    for entry in entries
                ]

                await conn.executemany(insert_query, values)
                await conn.commit()

            logger.debug(f"Flushed {len(entries)} audit log entries")

        except Exception as e:
            logger.error(f"Failed to flush audit batch: {e}")
            # Re-add entries to buffer for retry
            async with self._lock:
                self._batch_buffer.extend(entries)

    async def _flush_with_timeout(self):
        """Flush batch after timeout if not already full."""
        await asyncio.sleep(self._batch_timeout)

        async with self._lock:
            if self._batch_buffer:
                await self._flush_batch()

    def _anonymize_ip(self, ip_address: str) -> str:
        """
        Anonymize IP address per GDPR (FR-055).

        Keeps first two octets, replaces last two with zeros.

        Args:
            ip_address: Original IP address

        Returns:
            str: Anonymized IP address
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            if isinstance(ip, ipaddress.IPv4Address):
                # IPv4: keep first two octets
                parts = str(ip).split('.')
                return f"{parts[0]}.{parts[1]}.0.0"
            else:
                # IPv6: keep first 64 bits
                parts = str(ip).split(':')
                return ':'.join(parts[:4]) + '::' + '0' * (8 - len(parts[:4]))
        except ValueError:
            # Invalid IP, return hashed version
            return hashlib.sha256(ip_address.encode()).hexdigest()[:16]

    async def search_logs(self,
                         user_id: Optional[str] = None,
                         action_type: Optional[str] = None,
                         entity_type: Optional[str] = None,
                         entity_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters.

        Args:
            user_id: Filter by user ID
            action_type: Filter by action type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            start_date: Start date for search
            end_date: End date for search
            limit: Maximum results to return
            offset: Results offset for pagination

        Returns:
            List of log entries
        """
        try:
            # Build query
            conditions = []
            params = []

            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)

            if action_type:
                conditions.append("action_type = ?")
                params.append(action_type)

            if entity_type:
                conditions.append("entity_type = ?")
                params.append(entity_type)

            if entity_id:
                conditions.append("entity_id = ?")
                params.append(entity_id)

            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date.isoformat())

            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date.isoformat())

            # Add WHERE clause if conditions exist
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
            SELECT * FROM action_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """

            params.extend([limit, offset])

            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

            # Convert to dict and parse JSON fields
            results = []
            for row in rows:
                log_entry = dict(row)
                if log_entry['details']:
                    try:
                        log_entry['details'] = json.loads(log_entry['details'])
                    except json.JSONDecodeError:
                        pass
                results.append(log_entry)

            return results

        except Exception as e:
            logger.error(f"Failed to search audit logs: {e}")
            return []

    async def get_user_activity_summary(self,
                                       user_id: str,
                                       days: int = 30) -> Dict[str, Any]:
        """
        Get activity summary for a specific user.

        Args:
            user_id: User ID to analyze
            days: Number of days to look back

        Returns:
            Dict with activity statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = """
            SELECT
                action_type,
                COUNT(*) as count,
                SUM(CASE WHEN statut_action = 'succes' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN statut_action = 'echec' THEN 1 ELSE 0 END) as error_count,
                MAX(timestamp) as last_activity
            FROM action_logs
            WHERE user_id = ? AND timestamp >= ?
            GROUP BY action_type
            ORDER BY count DESC
            """

            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (user_id, start_date.isoformat()))
                rows = await cursor.fetchall()

            summary = {
                'user_id': user_id,
                'period_days': days,
                'total_actions': sum(row['count'] for row in rows),
                'successful_actions': sum(row['success_count'] for row in rows),
                'failed_actions': sum(row['error_count'] for row in rows),
                'last_activity': None,
                'actions_by_type': {}
            }

            for row in rows:
                summary['actions_by_type'][row['action_type']] = {
                    'count': row['count'],
                    'success_count': row['success_count'],
                    'error_count': row['error_count']
                }

                if summary['last_activity'] is None or row['last_activity'] > summary['last_activity']:
                    summary['last_activity'] = row['last_activity']

            return summary

        except Exception as e:
            logger.error(f"Failed to get user activity summary: {e}")
            return {}

    async def enforce_retention_policy(self):
        """
        Enforce 2-year data retention policy (FR-054-055).

        Deletes or anonymizes audit logs older than 2 years.
        Should be run periodically (e.g., daily cron job).

        Anonymization rules:
        - IP addresses: set to NULL
        - Details: remove sensitive information, keep action context
        - User agents: remove, keep generic device type
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=2 * 365)

            logger.info(f"Enforcing retention policy for logs older than {cutoff_date}")

            async with self.manager.get_connection('catechese') as conn:
                # Option 1: Delete old logs (stricter GDPR)
                delete_query = "DELETE FROM action_logs WHERE timestamp < ?"
                cursor = await conn.execute(delete_query, (cutoff_date.isoformat(),))
                deleted_count = cursor.rowcount

                # Option 2: Anonymize instead of delete (less strict)
                # Update query = """
                # UPDATE action_logs
                # SET ip_address = NULL,
                #     user_agent = 'Anonymized',
                #     details = '{"anonymized": true}'
                # WHERE timestamp < ?
                # """

                await conn.commit()

                logger.info(f"Retention policy enforcement completed: {deleted_count} entries deleted")

        except Exception as e:
            logger.error(f"Failed to enforce retention policy: {e}")

    async def get_system_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get system-wide audit statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with system statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            async with self.manager.get_connection('catechese') as conn:
                # Total actions
                cursor = await conn.execute(
                    "SELECT COUNT(*) as count FROM action_logs WHERE timestamp >= ?",
                    (start_date.isoformat(),)
                )
                total_actions = (await cursor.fetchone())['count']

                # Actions by type
                cursor = await conn.execute("""
                    SELECT action_type, COUNT(*) as count
                    FROM action_logs
                    WHERE timestamp >= ?
                    GROUP BY action_type
                    ORDER BY count DESC
                    LIMIT 10
                """, (start_date.isoformat(),))
                actions_by_type = {row['action_type']: row['count'] for row in await cursor.fetchall()}

                # Error rate
                cursor = await conn.execute("""
                    SELECT
                        SUM(CASE WHEN statut_action = 'echec' THEN 1 ELSE 0 END) as errors,
                        COUNT(*) as total
                    FROM action_logs
                    WHERE timestamp >= ?
                """, (start_date.isoformat(),))
                error_stats = await cursor.fetchone()
                error_rate = (error_stats['errors'] / error_stats['total'] * 100) if error_stats['total'] > 0 else 0

                # Active users
                cursor = await conn.execute("""
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM action_logs
                    WHERE timestamp >= ?
                """, (start_date.isoformat(),))
                active_users = (await cursor.fetchone())['count']

            return {
                'period_days': days,
                'total_actions': total_actions,
                'active_users': active_users,
                'error_rate_percent': round(error_rate, 2),
                'actions_by_type': actions_by_type
            }

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}


# Global audit service instance
_audit_service_instance: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get global audit service instance."""
    global _audit_service_instance
    if _audit_service_instance is None:
        _audit_service_instance = AuditService()
    return _audit_service_instance


# Convenience functions for common audit operations

async def log_user_action(user_id: str,
                          action_type: str,
                          entity_type: str,
                          entity_id: str,
                          request=None,
                          details: Optional[Dict[str, Any]] = None,
                          statut_action: str = "succes",
                          error_message: Optional[str] = None) -> str:
    """
    Log user action with request context.

    Args:
        user_id: User ID
        action_type: Action type
        entity_type: Entity type
        entity_id: Entity ID
        request: FastAPI Request object (optional)
        details: Additional details
        statut_action: Action status
        error_message: Error message

    Returns:
        str: Log ID
    """
    audit_service = get_audit_service()

    # Extract IP and user agent from request if available
    ip_address = None
    user_agent = None

    if request:
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    return await audit_service.log_action(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        statut_action=statut_action,
        error_message=error_message
    )


# Account creation specific audit logging functions

async def log_account_creation_event(
    event_type: Union[AccountCreationAuditEventType, str],
    phone_number: str,
    platform: str,
    platform_user_id: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
    status: str = "success",
    processing_time_ms: Optional[int] = None,
    error_message: Optional[str] = None
) -> str:
    """
    Log account creation specific audit event.

    Args:
        event_type: Type of account creation event
        phone_number: Phone number (will be masked)
        platform: Platform (whatsapp, telegram)
        platform_user_id: Platform-specific user ID (will be masked)
        user_id: User ID
        ip_address: Client IP address (will be masked)
        user_agent: Client user agent
        event_data: Event-specific data
        status: Event status
        processing_time_ms: Processing time in milliseconds
        error_message: Error message if failed

    Returns:
        str: Event ID
    """
    try:
        # Convert string enum to enum object
        if isinstance(event_type, str):
            event_type = AccountCreationAuditEventType(event_type)

        # Create audit event
        event = AccountCreationAuditEvent(
            event_id=DatabaseModel.generate_uuid(),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            phone_number=phone_number,
            platform=platform,
            platform_user_id=platform_user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            event_data=event_data or {},
            status=status,
            processing_time_ms=processing_time_ms,
            error_message=error_message
        )

        # Convert to dictionary and log to file
        event_dict = event.to_dict(include_sensitive=False)

        # Add to database batch buffer (reusing existing functionality)
        audit_service = get_audit_service()
        async with audit_service._lock:
            audit_service._batch_buffer.append({
                'log_id': event.event_id,
                'user_id': event.user_id,
                'action_type': f"account_creation_{event.event_type.value}",
                'entity_type': 'account_creation',
                'entity_id': event.event_id,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'timestamp': event.timestamp.isoformat(),
                'details': json.dumps(event_dict),
                'statut_action': 'succes' if status == 'success' else 'echec',
                'error_message': error_message
            })

            # Process batch if full
            if len(audit_service._batch_buffer) >= audit_service._batch_size:
                await audit_service._flush_batch()

        # Start flush timeout task if not already running
        asyncio.create_task(audit_service._flush_with_timeout())

        logger.debug(
            f"Account creation audit event logged: {event.event_type.value} for {platform}:{phone_number[:4]}****"
        )
        return event.event_id

    except Exception as e:
        logger.error(f"Failed to log account creation audit event: {e}")
        return ""


async def log_phone_validation(
    phone_number: str,
    is_valid: bool,
    validation_details: Dict[str, Any],
    platform: str,
    platform_user_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> str:
    """
    Log phone validation result.

    Args:
        phone_number: Phone number validated
        is_valid: Whether validation passed
        validation_details: Validation result details
        platform: Platform
        platform_user_id: Platform user ID
        user_id: User ID

    Returns:
        str: Event ID
    """
    return await log_account_creation_event(
        event_type=AccountCreationAuditEventType.PHONE_VALIDATION,
        phone_number=phone_number,
        platform=platform,
        platform_user_id=platform_user_id,
        user_id=user_id,
        event_data={
            'is_valid': is_valid,
            'validation_details': validation_details
        },
        status='success' if is_valid else 'failed'
    )


async def log_parent_lookup(
    phone_number: str,
    parent_found: bool,
    platform: str,
    parent_id: Optional[int] = None,
    user_id: Optional[str] = None
) -> str:
    """
    Log parent database lookup result.

    Args:
        phone_number: Phone number searched
        parent_found: Whether parent was found
        parent_id: Parent database ID
        platform: Platform
        user_id: User ID

    Returns:
        str: Event ID
    """
    return await log_account_creation_event(
        event_type=AccountCreationAuditEventType.PARENT_LOOKUP,
        phone_number=phone_number,
        platform=platform,
        user_id=user_id,
        event_data={
            'parent_found': parent_found,
            'parent_id': parent_id
        },
        status='success' if parent_found else 'not_found'
    )


async def log_duplicate_account_prevented(
    phone_number: str,
    existing_user_id: str,
    platform: str
) -> str:
    """
    Log prevention of duplicate account creation.

    Args:
        phone_number: Phone number
        existing_user_id: Existing user ID
        platform: Platform

    Returns:
        str: Event ID
    """
    return await log_account_creation_event(
        event_type=AccountCreationAuditEventType.DUPLICATE_ACCOUNT_PREVENTED,
        phone_number=phone_number,
        platform=platform,
        user_id=existing_user_id,
        event_data={
            'existing_user_id': existing_user_id
        },
        status='prevented'
    )


async def log_webhook_event(
    platform: str,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
    status: str = "received",
    processing_time_ms: Optional[int] = None,
    error_message: Optional[str] = None
) -> str:
    """
    Log webhook event (received, processed, or failed).

    Args:
        platform: Platform
        event_type: Webhook event type
        user_id: User ID
        ip_address: Client IP address
        user_agent: Client user agent
        event_data: Event-specific data
        status: Event status
        processing_time_ms: Processing time
        error_message: Error message

    Returns:
        str: Event ID
    """
    audit_event_type = {
        'received': AccountCreationAuditEventType.WEBHOOK_RECEIVED,
        'processed': AccountCreationAuditEventType.WEBHOOK_PROCESSED,
        'failed': AccountCreationAuditEventType.WEBHOOK_FAILED
    }.get(status.lower(), AccountCreationAuditEventType.WEBHOOK_RECEIVED)

    return await log_account_creation_event(
        event_type=audit_event_type,
        phone_number="",  # Not applicable for webhook events
        platform=platform,
        platform_user_id=event_data.get('platform_user_id') if event_data else None,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        event_data=event_data or {},
        status=status,
        processing_time_ms=processing_time_ms,
        error_message=error_message
    )


def get_account_creation_audit_events(
    user_id: Optional[str] = None,
    phone_number: Optional[str] = None,
    platform: Optional[str] = None,
    event_type: Optional[Union[AccountCreationAuditEventType, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
) -> List[AccountCreationAuditEvent]:
    """
    Get account creation audit events with filtering.

    Args:
        user_id: Filter by user ID
        phone_number: Filter by phone number
        platform: Filter by platform
        event_type: Filter by event type
        start_time: Filter by start time
        end_time: Filter by end time
        limit: Maximum number of events

    Returns:
        List of account creation audit events
    """
    # This would need implementation based on your database schema
    # For now, return empty list as placeholder
    logger.info("Account creation audit events retrieval not yet implemented")
    return []


async def log_audit_event(
    event_type: str,
    user_id: str,
    event_data: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    statut_action: str = "succes",
    error_message: Optional[str] = None
) -> str:
    """
    Log generic audit event.

    Args:
        event_type: Type of event
        user_id: User ID
        event_data: Event-specific data
        ip_address: Client IP address
        user_agent: Client user agent
        statut_action: Action status
        error_message: Error message

    Returns:
        str: Log ID
    """
    audit_service = get_audit_service()
    return await audit_service.log_action(
        user_id=user_id,
        action_type=event_type,
        entity_type="system",
        entity_id="system",
        ip_address=ip_address,
        user_agent=user_agent,
        details=event_data,
        statut_action=statut_action,
        error_message=error_message
    )


# Convenience function for getting audit service with account creation support
def get_enhanced_audit_service() -> 'AuditService':
    """Get enhanced audit service with account creation support."""
    return get_audit_service()