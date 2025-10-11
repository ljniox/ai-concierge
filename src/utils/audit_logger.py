"""
Audit Logging Utility for Account Creation System

This module provides comprehensive audit logging functionality for the automatic
account creation feature, ensuring GDPR compliance and complete audit trails.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from enum import Enum
import hashlib
import traceback

from src.models.audit import (
    AuditEvent, AccountCreationAudit, PhoneValidationAudit, RoleAssignmentAudit,
    ConsentAudit, DataAccessAudit, PlatformAccountAudit,
    AuditEventType, CreationStatus, PhoneValidationResult
)
from src.utils.logging import account_logger


class AuditLogger:
    """Centralized audit logging system."""

    def __init__(self, storage_backend="file"):
        """
        Initialize audit logger.

        Args:
            storage_backend: Backend for storing audit logs ("file", "database", "both")
        """
        self.storage_backend = storage_backend
        self.logger = logging.getLogger(__name__)
        self.pending_logs: List[Dict[str, Any]] = []
        self.batch_size = 100
        self.flush_interval = 300  # 5 minutes
        self.last_flush = datetime.utcnow()

    async def log_account_creation_started(
        self,
        phone_number: str,
        source: str,
        platform_user_id: str,
        request_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log the start of account creation process.

        Args:
            phone_number: Phone number being processed
            source: Platform source ('telegram' or 'whatsapp')
            platform_user_id: Platform-specific user ID
            request_data: Additional request data

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": AuditEventType.ACCOUNT_CREATION_STARTED,
            "phone_number": self._mask_phone_number(phone_number),
            "platform": source,
            "platform_user_id": self._mask_platform_user_id(platform_user_id),
            "request_data": request_data,
            "success": None,  # Not yet determined
            "processing_time_ms": None,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_account_creation_started(phone_number, source, platform_user_id)

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_account_creation_completed(
        self,
        event_id: str,
        phone_number: str,
        success: bool,
        user_id: Optional[int] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        platform: Optional[str] = None,
        platform_user_id: Optional[str] = None,
        parent_found: bool = False,
        parent_id: Optional[int] = None
    ) -> None:
        """
        Log the completion of account creation process.

        Args:
            event_id: Original event ID
            phone_number: Phone number
            success: Whether creation was successful
            user_id: Created user ID (if successful)
            error_message: Error message (if failed)
            processing_time_ms: Processing time in milliseconds
            platform: Platform name
            platform_user_id: Platform user ID
            parent_found: Whether parent was found in database
            parent_id: Parent database ID
        """
        event_data = {
            "event_type": AuditEventType.ACCOUNT_CREATION_SUCCESS if success else AuditEventType.ACCOUNT_CREATION_FAILED,
            "phone_number": self._mask_phone_number(phone_number),
            "platform": platform,
            "platform_user_id": self._mask_platform_user_id(platform_user_id),
            "success": success,
            "user_id": user_id,
            "error_message": error_message,
            "processing_time_ms": processing_time_ms,
            "parent_found": parent_found,
            "parent_id": parent_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        if success:
            account_logger.log_account_created(
                user_id=user_id,
                phone_number=phone_number,
                roles=["parent"],
                source=platform or "unknown"
            )
        else:
            account_logger.log_account_creation_failed(
                phone_number=phone_number,
                error_type="creation_failed",
                error_message=error_message or "Unknown error",
                source=platform or "unknown"
            )

        # Store audit event
        await self._store_audit_event(event_id, event_data)

    async def log_phone_validation(
        self,
        phone_number: str,
        validation_result: PhoneValidationResult,
        normalized_number: Optional[str] = None,
        is_mobile: Optional[bool] = None,
        carrier: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> str:
        """
        Log phone number validation result.

        Args:
            phone_number: Original phone number
            validation_result: Validation result
            normalized_number: Normalized phone number
            is_mobile: Whether number is mobile
            carrier: Phone carrier
            processing_time_ms: Processing time

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": AuditEventType.PHONE_VALIDATION,
            "phone_number": self._mask_phone_number(phone_number),
            "validation_result": validation_result.value,
            "normalized_number": normalized_number,
            "is_mobile": is_mobile,
            "carrier": carrier,
            "success": validation_result == PhoneValidationResult.VALID,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_phone_validation_result(
            phone_number,
            validation_result == PhoneValidationResult.VALID,
            {
                "normalized": normalized_number,
                "is_mobile": is_mobile,
                "carrier": carrier
            }
        )

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_parent_database_lookup(
        self,
        phone_number: str,
        parent_found: bool,
        parent_id: Optional[int] = None,
        parent_data: Optional[Dict[str, Any]] = None,
        lookup_time_ms: Optional[int] = None
    ) -> str:
        """
        Log parent database lookup result.

        Args:
            phone_number: Phone number searched
            parent_found: Whether parent was found
            parent_id: Parent database ID
            parent_data: Parent data if found
            lookup_time_ms: Lookup time

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": "PARENT_DATABASE_LOOKUP",
            "phone_number": self._mask_phone_number(phone_number),
            "parent_found": parent_found,
            "parent_id": parent_id,
            "parent_data": self._sanitize_parent_data(parent_data) if parent_data else None,
            "success": parent_found,
            "processing_time_ms": lookup_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_parent_database_lookup(
            phone_number,
            parent_found,
            parent_id
        )

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_role_assignment(
        self,
        user_id: int,
        role_name: str,
        assigned_by: Optional[int] = None,
        assignment_type: str = "assigned",
        expires_at: Optional[datetime] = None,
        assignment_reason: Optional[str] = None
    ) -> str:
        """
        Log role assignment or removal.

        Args:
            user_id: User ID
            role_name: Role name
            assigned_by: User ID who performed assignment
            assignment_type: Type of assignment ('assigned', 'removed')
            expires_at: Expiration date
            assignment_reason: Reason for assignment

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": AuditEventType.ROLE_ASSIGNED,
            "target_user_id": user_id,
            "role_name": role_name,
            "assigned_by": assigned_by,
            "assignment_type": assignment_type,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "assignment_reason": assignment_reason,
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_role_assignment(user_id, role_name, assigned_by)

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_consent_given(
        self,
        user_id: int,
        consent_type: str,
        consent_method: str = "automatic",
        consent_version: str = "1.0",
        withdrawal_reason: Optional[str] = None
    ) -> str:
        """
        Log consent management event.

        Args:
            user_id: User ID
            consent_type: Type of consent
            consent_method: How consent was obtained
            consent_version: Consent version
            withdrawal_reason: Reason for withdrawal

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        consent_given = withdrawal_reason is None

        event_data = {
            "event_type": AuditEventType.CONSENT_GIVEN if consent_given else AuditEventType.CONSENT_WITHDRAWN,
            "user_id": user_id,
            "consent_type": consent_type,
            "consent_method": consent_method,
            "consent_version": consent_version,
            "consent_given": consent_given,
            "withdrawal_reason": withdrawal_reason,
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_consent_given(user_id, consent_type)

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_platform_account_linked(
        self,
        user_id: int,
        platform: str,
        platform_user_id: str,
        link_type: str = "linked",
        verification_method: Optional[str] = None,
        previous_platform_user_id: Optional[str] = None
    ) -> str:
        """
        Log platform account linking event.

        Args:
            user_id: User ID
            platform: Platform name
            platform_user_id: Platform user ID
            link_type: Type of linking
            verification_method: Verification method used
            previous_platform_user_id: Previous platform user ID

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": AuditEventType.PLATFORM_ACCOUNT_LINKED,
            "user_id": user_id,
            "platform": platform,
            "platform_user_id": self._mask_platform_user_id(platform_user_id),
            "link_type": link_type,
            "verification_method": verification_method,
            "previous_platform_user_id": self._mask_platform_user_id(previous_platform_user_id),
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_platform_account_linked(user_id, platform, platform_user_id)

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_data_access(
        self,
        accessed_by: int,
        accessed_resource: str,
        access_type: str,
        record_count: Optional[int] = None,
        access_reason: Optional[str] = None,
        query_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log data access event.

        Args:
            accessed_by: User ID performing access
            accessed_resource: Resource being accessed
            access_type: Type of access
            record_count: Number of records accessed
            access_reason: Reason for access
            query_parameters: Query parameters used

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": AuditEventType.DATA_ACCESSED,
            "accessed_by": accessed_by,
            "accessed_resource": accessed_resource,
            "access_type": access_type,
            "record_count": record_count,
            "access_reason": access_reason,
            "query_parameters": query_parameters,
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_duplicate_account_prevented(
        self,
        phone_number: str,
        existing_user_id: int,
        platform: Optional[str] = None,
        platform_user_id: Optional[str] = None
    ) -> str:
        """
        Log prevention of duplicate account creation.

        Args:
            phone_number: Phone number
            existing_user_id: Existing user ID
            platform: Platform name
            platform_user_id: Platform user ID

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": "DUPLICATE_ACCOUNT_PREVENTED",
            "phone_number": self._mask_phone_number(phone_number),
            "existing_user_id": existing_user_id,
            "platform": platform,
            "platform_user_id": self._mask_platform_user_id(platform_user_id),
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_duplicate_account_prevented(
            phone_number,
            existing_user_id
        )

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def log_rate_limit_exceeded(
        self,
        identifier: str,
        limit_type: str,
        retry_after: Optional[int] = None
    ) -> str:
        """
        Log rate limit exceeded event.

        Args:
            identifier: Identifier (IP, phone number, etc.)
            limit_type: Type of rate limit
            retry_after: Retry after seconds

        Returns:
            Audit event ID
        """
        event_id = self._generate_event_id()

        event_data = {
            "event_type": "RATE_LIMIT_EXCEEDED",
            "identifier": self._mask_identifier(identifier),
            "limit_type": limit_type,
            "retry_after": retry_after,
            "success": False,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log to account logger
        account_logger.log_rate_limit_exceeded(identifier, limit_type)

        # Store audit event
        await self._store_audit_event(event_id, event_data)

        return event_id

    async def _store_audit_event(self, event_id: str, event_data: Dict[str, Any]) -> None:
        """
        Store audit event to backend(s).

        Args:
            event_id: Event ID
            event_data: Event data
        """
        # Add event ID and metadata
        event_data["event_id"] = event_id
        event_data["storage_timestamp"] = datetime.utcnow().isoformat()

        # Store based on backend configuration
        if self.storage_backend in ["file", "both"]:
            await self._store_to_file(event_id, event_data)

        if self.storage_backend in ["database", "both"]:
            await self._store_to_database(event_id, event_data)

        # Add to pending logs for batch processing
        self.pending_logs.append(event_data)

        # Check if batch flush is needed
        await self._check_batch_flush()

    async def _store_to_file(self, event_id: str, event_data: Dict[str, Any]) -> None:
        """Store audit event to file."""
        try:
            # Create audit directory if it doesn't exist
            import os
            audit_dir = "logs/audit"
            os.makedirs(audit_dir, exist_ok=True)

            # Create daily log file
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            filename = f"{audit_dir}/audit_{date_str}.jsonl"

            # Append event to file
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, default=str, ensure_ascii=False) + "\n")

        except Exception as e:
            self.logger.error(f"Failed to store audit event to file: {str(e)}")

    async def _store_to_database(self, event_id: str, event_data: Dict[str, Any]) -> None:
        """Store audit event to database."""
        try:
            # This would connect to the actual database
            # For now, just log that database storage would happen
            self.logger.debug(f"Would store audit event {event_id} to database")

            # In a real implementation, this would:
            # 1. Connect to the database
            # 2. Insert into account_creation_audit table
            # 3. Handle connection errors gracefully

        except Exception as e:
            self.logger.error(f"Failed to store audit event to database: {str(e)}")

    async def _check_batch_flush(self) -> None:
        """Check if batch flush is needed."""
        now = datetime.utcnow()

        # Check if we need to flush based on batch size or time interval
        if (len(self.pending_logs) >= self.batch_size or
            (now - self.last_flush).total_seconds() >= self.flush_interval):

            if self.pending_logs:
                await self._flush_pending_logs()
                self.pending_logs.clear()
                self.last_flush = now

    async def _flush_pending_logs(self) -> None:
        """Flush pending logs to storage."""
        try:
            # In a real implementation, this might batch insert to database
            self.logger.info(f"Flushing {len(self.pending_logs)} audit events to storage")
        except Exception as e:
            self.logger.error(f"Failed to flush pending audit logs: {str(e)}")

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = datetime.utcnow().isoformat()
        random_data = str(hash(timestamp + str(id(self)))
        return hashlib.md5(f"{timestamp}_{random_data}".encode()).hexdigest()[:16]

    def _mask_phone_number(self, phone_number: str) -> str:
        """Mask phone number for privacy."""
        if not phone_number or len(phone_number) <= 6:
            return "***"
        return phone_number[:3] + "***" + phone_number[-3:]

    def _mask_platform_user_id(self, platform_user_id: str) -> str:
        """Mask platform user ID for privacy."""
        if not platform_user_id or len(platform_user_id) <= 6:
            return "***"
        return platform_user_id[:3] + "***" + platform_user_id[-3:]

    def _mask_identifier(self, identifier: str) -> str:
        """Mask general identifier for privacy."""
        if not identifier or len(identifier) <= 6:
            return "***"
        return identifier[:3] + "***" + identifier[-3:]

    def _sanitize_parent_data(self, parent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parent data for audit logging."""
        sanitized = parent_data.copy()

        # Remove or mask sensitive fields
        sensitive_fields = ["email", "adresse", "notes"]
        for field in sensitive_fields:
            if field in sanitized:
                if field == "email":
                    sanitized[field] = sanitized[field][:2] + "***" if sanitized[field] else "***"
                else:
                    sanitized[field] = "[REDACTED]"

        return sanitized

    async def get_audit_trail(
        self,
        phone_number: Optional[str] = None,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail for specified criteria.

        Args:
            phone_number: Filter by phone number
            user_id: Filter by user ID
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of events

        Returns:
            List of audit events
        """
        # This would query the audit storage
        # For now, return empty list
        # In a real implementation, this would:
        # 1. Query database or files based on filters
        # 2. Apply privacy masking as needed
        # 3. Return formatted results

        self.logger.info(f"Audit trail requested: phone={phone_number}, user_id={user_id}, type={event_type}")
        return []

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate GDPR compliance report.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report
        """
        # This would generate a comprehensive compliance report
        # For now, return a basic structure

        report = {
            "report_period_start": start_date.isoformat(),
            "report_period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "total_events": 0,
            "events_by_type": {},
            "unique_users": 0,
            "unique_phone_numbers": 0,
            "compliance_status": "pending",
            "recommendations": [
                "Implement full database storage for audit events",
                "Add data retention policies",
                "Implement consent withdrawal tracking"
            ]
        }

        return report


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit operations
async def log_account_creation_start(
    phone_number: str,
    source: str,
    platform_user_id: str,
    request_data: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience function for logging account creation start."""
    return await audit_logger.log_account_creation_started(
        phone_number, source, platform_user_id, request_data
    )


async def log_account_creation_result(
    event_id: str,
    phone_number: str,
    success: bool,
    user_id: Optional[int] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
    **kwargs
) -> None:
    """Convenience function for logging account creation result."""
    await audit_logger.log_account_creation_completed(
        event_id, phone_number, success, user_id, error_message,
        processing_time_ms, **kwargs
    )


async def log_validation_result(
    phone_number: str,
    validation_result: PhoneValidationResult,
    **kwargs
) -> str:
    """Convenience function for logging phone validation result."""
    return await audit_logger.log_phone_validation(
        phone_number, validation_result, **kwargs
    )


async def log_role_change(
    user_id: int,
    role_name: str,
    assigned_by: Optional[int] = None,
    **kwargs
) -> str:
    """Convenience function for logging role changes."""
    return await audit_logger.log_role_assignment(
        user_id, role_name, assigned_by, **kwargs
    )