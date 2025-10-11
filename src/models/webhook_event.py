"""
Webhook event model for the automatic account creation system.

This module defines the WebhookEvent model which logs all incoming webhook
events for security, debugging, and audit purposes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, Integer, DateTime, Index, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB, INET
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseSQLModel, ProcessingStatus, Platform


class WebhookEvent(BaseSQLModel):
    """
    Webhook event model for comprehensive webhook logging.

    This model provides detailed logging of all incoming webhook events
    with security verification, processing tracking, and audit capabilities.
    """

    __tablename__ = "webhook_events"

    # Event identification
    platform = Column(String(20), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_id = Column(String(255), nullable=True, index=True)  # Platform-specific event ID

    # Request details
    webhook_url = Column(Text, nullable=False)
    request_method = Column(String(10), nullable=False)
    request_headers = Column(JSONB, nullable=False, default=dict)
    request_body_size = Column(Integer, nullable=True)
    request_body_hash = Column(String(64), nullable=True)  # SHA-256 hash

    # Security verification
    signature_verified = Column(Boolean, nullable=False, default=False, index=True)
    signature_details = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)

    # Processing details
    processing_status = Column(
        String(20),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )
    processing_error = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Relations
    session_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Event metadata
    metadata_json = Column(JSONB, default=dict, nullable=True)

    # Relationships
    session = relationship("UserSession", back_populates="webhook_events")
    user = relationship("UserAccount")

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_webhook_events_platform_status", "platform", "processing_status"),
        Index("idx_webhook_events_signature_verified", "signature_verified", "received_at"),
        Index("idx_webhook_events_event_id", "event_id", "platform"),
        Index("idx_webhook_events_processing_time", "processing_time_ms"),
        {
            "schema": None,  # Uses default schema
        }
    )

    def __repr__(self) -> str:
        """String representation of WebhookEvent."""
        return f"<WebhookEvent(id={self.id}, platform={self.platform}, event_type={self.event_type})>"

    @property
    def is_processed(self) -> bool:
        """Check if webhook event has been processed."""
        return self.processed_at is not None

    @property
    def is_processing_complete(self) -> bool:
        """Check if processing is complete (success or failure)."""
        return self.processing_status in [
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
            ProcessingStatus.IGNORED
        ]

    @property
    def is_successful(self) -> bool:
        """Check if webhook processing was successful."""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if webhook processing failed."""
        return self.processing_status == ProcessingStatus.FAILED

    @property
    def processing_duration_ms(self) -> Optional[int]:
        """
        Get actual processing duration in milliseconds.

        Returns:
            Processing duration in milliseconds or None if not processed
        """
        if self.processing_time_ms is not None:
            return self.processing_time_ms
        elif self.processed_at is not None:
            delta = self.processed_at - self.received_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def event_age_seconds(self) -> int:
        """Get event age in seconds."""
        delta = datetime.now(timezone.utc) - self.received_at
        return int(delta.total_seconds())

    @property
    def has_valid_signature(self) -> bool:
        """Check if webhook has a valid signature."""
        return self.signature_verified and self.signature_details is not None

    @property
    def signature_algorithm(self) -> Optional[str]:
        """Get signature algorithm used."""
        if self.signature_details:
            return self.signature_details.get("algorithm")
        return None

    def mark_processing_started(self, session: Optional[Session] = None) -> None:
        """
        Mark webhook processing as started.

        Args:
            session: Database session (optional)
        """
        self.processing_status = ProcessingStatus.PROCESSING
        if session:
            session.add(self)
            session.commit()

    def mark_completed(
        self,
        processing_time_ms: Optional[int] = None,
        session_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        session: Optional[Session] = None
    ) -> None:
        """
        Mark webhook processing as completed.

        Args:
            processing_time_ms: Processing time in milliseconds
            session_id: Related session ID
            user_id: Related user ID
            session: Database session (optional)
        """
        self.processing_status = ProcessingStatus.COMPLETED
        self.processed_at = datetime.now(timezone.utc)
        self.processing_time_ms = processing_time_ms

        if session_id:
            self.session_id = session_id
        if user_id:
            self.user_id = user_id

        if session:
            session.add(self)
            session.commit()

    def mark_failed(self, error_message: str, session: Optional[Session] = None) -> None:
        """
        Mark webhook processing as failed.

        Args:
            error_message: Error message
            session: Database session (optional)
        """
        self.processing_status = ProcessingStatus.FAILED
        self.processed_at = datetime.now(timezone.utc)
        self.processing_error = error_message

        if session:
            session.add(self)
            session.commit()

    def mark_ignored(self, reason: str, session: Optional[Session] = None) -> None:
        """
        Mark webhook as ignored.

        Args:
            reason: Reason for ignoring
            session: Database session (optional)
        """
        self.processing_status = ProcessingStatus.IGNORED
        self.processed_at = datetime.now(timezone.utc)
        self.processing_error = reason

        if session:
            session.add(self)
            session.commit()

    def set_signature_verification(
        self,
        verified: bool,
        algorithm: Optional[str] = None,
        signature: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> None:
        """
        Set signature verification results.

        Args:
            verified: Whether signature was verified
            algorithm: Signature algorithm used
            signature: The signature itself
            details: Additional verification details
            session: Database session (optional)
        """
        self.signature_verified = verified
        self.signature_details = {
            "algorithm": algorithm,
            "signature": signature,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            **(details or {})
        }

        if session:
            session.add(self)
            session.commit()

    def set_processing_time(self, processing_time_ms: int, session: Optional[Session] = None) -> None:
        """
        Set processing time.

        Args:
            processing_time_ms: Processing time in milliseconds
            session: Database session (optional)
        """
        self.processing_time_ms = processing_time_ms
        if session:
            session.add(self)
            session.commit()

    def add_processing_step(self, step_name: str, step_data: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Add a processing step to the event metadata.

        Args:
            step_name: Name of the processing step
            step_data: Step data
            session: Database session (optional)
        """
        if not self.metadata_json:
            self.metadata_json = {}
        if "processing_steps" not in self.metadata_json:
            self.metadata_json["processing_steps"] = []

        processing_step = {
            "step": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": step_data
        }

        self.metadata_json["processing_steps"].append(processing_step)

        if session:
            session.add(self)
            session.commit()

    def add_security_event(self, event_type: str, event_data: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Add security event to webhook event.

        Args:
            event_type: Type of security event
            event_data: Event data
            session: Database session (optional)
        """
        if not self.metadata_json:
            self.metadata_json = {}
        if "security_events" not in self.metadata_json:
            self.metadata_json["security_events"] = []

        security_event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": event_data
        }

        self.metadata_json["security_events"].append(security_event)

        if session:
            session.add(self)
            session.commit()

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert webhook event to dictionary.

        Args:
            include_sensitive: Whether to include sensitive information

        Returns:
            Dictionary representation of webhook event
        """
        data = super().to_dict()

        # Add computed properties
        data.update({
            "is_processed": self.is_processed,
            "is_processing_complete": self.is_processing_complete,
            "is_successful": self.is_successful,
            "is_failed": self.is_failed,
            "processing_duration_ms": self.processing_duration_ms,
            "event_age_seconds": self.event_age_seconds,
            "has_valid_signature": self.has_valid_signature,
            "signature_algorithm": self.signature_algorithm
        })

        # Mask sensitive data unless explicitly requested
        if not include_sensitive:
            data["request_headers"] = {
                k: v if k.lower() not in ["authorization", "x-signature", "signature"] else "***REDACTED***"
                for k, v in (data.get("request_headers") or {}).items()
            }
            data["signature_details"] = {
                k: v if k not in ["signature", "signing_secret"] else "***REDACTED***"
                for k, v in (data.get("signature_details") or {}).items()
            } if data.get("signature_details") else None
            data["ip_address"] = None

        return data

    @classmethod
    def create_webhook_event(
        cls,
        session: Session,
        platform: str,
        event_type: str,
        webhook_url: str,
        request_method: str,
        request_headers: Dict[str, Any],
        request_body_size: Optional[int] = None,
        request_body_hash: Optional[str] = None,
        event_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> "WebhookEvent":
        """
        Create a new webhook event record.

        Args:
            session: Database session
            platform: Platform (whatsapp, telegram)
            event_type: Type of webhook event
            webhook_url: Webhook URL
            request_method: HTTP method
            request_headers: Request headers
            request_body_size: Request body size in bytes
            request_body_hash: SHA-256 hash of request body
            event_id: Platform-specific event ID
            ip_address: Client IP address

        Returns:
            Created WebhookEvent instance
        """
        webhook_event = cls(
            platform=platform,
            event_type=event_type,
            webhook_url=webhook_url,
            request_method=request_method,
            request_headers=request_headers,
            request_body_size=request_body_size,
            request_body_hash=request_body_hash,
            event_id=event_id,
            ip_address=ip_address,
            processing_status=ProcessingStatus.PENDING
        )

        session.add(webhook_event)
        session.commit()
        session.refresh(webhook_event)

        return webhook_event

    @classmethod
    def find_by_event_id(cls, session: Session, platform: str, event_id: str) -> Optional["WebhookEvent"]:
        """
        Find webhook event by platform and event ID.

        Args:
            session: Database session
            platform: Platform
            event_id: Event ID

        Returns:
            WebhookEvent instance or None
        """
        return session.query(cls).filter(
            cls.platform == platform,
            cls.event_id == event_id,
            cls.is_deleted == False
        ).first()

    @classmethod
    def get_pending_events(cls, session: Session, platform: Optional[str] = None) -> list["WebhookEvent"]:
        """
        Get pending webhook events.

        Args:
            session: Database session
            platform: Optional platform filter

        Returns:
            List of pending WebhookEvent instances
        """
        query = session.query(cls).filter(
            cls.processing_status == ProcessingStatus.PENDING,
            cls.is_deleted == False
        )

        if platform:
            query = query.filter(cls.platform == platform)

        return query.order_by(cls.received_at.asc()).all()

    @classmethod
    def get_failed_events(
        cls,
        session: Session,
        hours: int = 24,
        platform: Optional[str] = None
    ) -> list["WebhookEvent"]:
        """
        Get failed webhook events.

        Args:
            session: Database session
            hours: Number of hours to look back
            platform: Optional platform filter

        Returns:
            List of failed WebhookEvent instances
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = session.query(cls).filter(
            cls.processing_status == ProcessingStatus.FAILED,
            cls.received_at >= cutoff_time,
            cls.is_deleted == False
        )

        if platform:
            query = query.filter(cls.platform == platform)

        return query.order_by(cls.received_at.desc()).all()

    @classmethod
    def get_events_by_status(
        cls,
        session: Session,
        status: str,
        hours: int = 24,
        platform: Optional[str] = None
    ) -> list["WebhookEvent"]:
        """
        Get webhook events by processing status.

        Args:
            session: Database session
            status: Processing status
            hours: Number of hours to look back
            platform: Optional platform filter

        Returns:
            List of WebhookEvent instances
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = session.query(cls).filter(
            cls.processing_status == status,
            cls.received_at >= cutoff_time,
            cls.is_deleted == False
        )

        if platform:
            query = query.filter(cls.platform == platform)

        return query.order_by(cls.received_at.desc()).all()

    @classmethod
    def get_processing_statistics(
        cls,
        session: Session,
        hours: int = 24,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get webhook processing statistics.

        Args:
            session: Database session
            hours: Number of hours to analyze
            platform: Optional platform filter

        Returns:
            Dictionary with processing statistics
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        base_query = session.query(cls).filter(
            cls.received_at >= cutoff_time,
            cls.is_deleted == False
        )

        if platform:
            base_query = base_query.filter(cls.platform == platform)

        # Total events
        total_events = base_query.count()

        # Events by status
        status_stats = base_query.with_entities(
            cls.processing_status,
            func.count(cls.id).label("count")
        ).group_by(cls.processing_status).all()

        # Signature verification stats
        signature_stats = base_query.with_entities(
            cls.signature_verified,
            func.count(cls.id).label("count")
        ).group_by(cls.signature_verified).all()

        # Average processing time
        avg_processing_time = base_query.filter(
            cls.processing_time_ms.isnot(None)
        ).with_entities(func.avg(cls.processing_time_ms)).scalar()

        # Platform breakdown if not filtered
        platform_stats = None
        if not platform:
            platform_breakdown = base_query.with_entities(
                cls.platform,
                func.count(cls.id).label("count")
            ).group_by(cls.platform).all()
            platform_stats = {stat.platform: stat.count for stat in platform_breakdown}

        return {
            "period_hours": hours,
            "platform": platform or "all",
            "total_events": total_events,
            "by_status": {stat.processing_status: stat.count for stat in status_stats},
            "signature_verification": {
                "verified": next((stat.count for stat in signature_stats if stat.signature_verified), 0),
                "unverified": next((stat.count for stat in signature_stats if not stat.signature_verified), 0)
            },
            "average_processing_time_ms": int(avg_processing_time) if avg_processing_time else None,
            "platform_breakdown": platform_stats
        }

    @classmethod
    def detect_anomalous_webhooks(
        cls,
        session: Session,
        hours: int = 1,
        threshold_events: int = 100
    ) -> Dict[str, Any]:
        """
        Detect anomalous webhook activity.

        Args:
            session: Database session
            hours: Time window to check
            threshold_events: Threshold for considering activity anomalous

        Returns:
            Dictionary with anomalous webhook detection results
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # High volume from single IP
        ip_activity = session.query(
            cls.ip_address,
            func.count(cls.id).label("event_count")
        ).filter(
            cls.received_at >= cutoff_time,
            cls.ip_address.isnot(None),
            cls.is_deleted == False
        ).group_by(cls.ip_address).having(func.count(cls.id) > threshold_events).all()

        # High volume of invalid signatures
        invalid_signature_activity = session.query(
            cls.ip_address,
            func.count(cls.id).label("invalid_count")
        ).filter(
            cls.received_at >= cutoff_time,
            cls.signature_verified == False,
            cls.ip_address.isnot(None),
            cls.is_deleted == False
        ).group_by(cls.ip_address).having(func.count(cls.id) > threshold_events / 10).all()

        # High failure rate from specific sources
        failure_hotspots = session.query(
            cls.ip_address,
            func.count(cls.id).label("total"),
            func.sum(func.case([(cls.processing_status == ProcessingStatus.FAILED, 1)], else_=0)).label("failures")
        ).filter(
            cls.received_at >= cutoff_time,
            cls.ip_address.isnot(None),
            cls.is_deleted == False
        ).group_by(cls.ip_address).having(
            (func.sum(func.case([(cls.processing_status == ProcessingStatus.FAILED, 1)], else_=0)) * 1.0 / func.count(cls.id)) > 0.5
        ).all()

        return {
            "time_window_hours": hours,
            "threshold_events": threshold_events,
            "high_volume_ips": [
                {"ip_address": str(stat.ip_address), "event_count": stat.event_count}
                for stat in ip_activity
            ],
            "invalid_signature_ips": [
                {"ip_address": str(stat.ip_address), "invalid_signature_count": stat.invalid_count}
                for stat in invalid_signature_activity
            ],
            "high_failure_rate_ips": [
                {
                    "ip_address": str(stat.ip_address),
                    "total_events": stat.total,
                    "failed_events": stat.failures,
                    "failure_rate": round(stat.failures / stat.total * 100, 2)
                }
                for stat in failure_hotspots
            ],
            "anomaly_detected": len(ip_activity) > 0 or len(invalid_signature_activity) > 0 or len(failure_hotspots) > 0
        }

    @classmethod
    def cleanup_old_events(cls, session: Session, days: int = 30) -> int:
        """
        Clean up old webhook events.

        Args:
            session: Database session
            days: Number of days to keep events

        Returns:
            Number of events cleaned up
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        old_events = session.query(cls).filter(
            cls.received_at < cutoff_date,
            cls.processing_status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.IGNORED]),
            cls.is_deleted == False
        ).all()

        count = 0
        for event in old_events:
            event.delete(session, soft=True)
            count += 1

        return count


# Import for timedelta
from datetime import timedelta