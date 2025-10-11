"""
Account creation audit model for the automatic account creation system.

This module defines the AccountCreationAudit model which provides
comprehensive audit trails for all account creation activities.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, Integer, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB, INET
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseSQLModel, AccountCreationStatus, Platform


class AccountCreationAudit(BaseSQLModel):
    """
    Account creation audit model for comprehensive activity tracking.

    This model provides detailed audit trails for all account creation
    attempts, successes, failures, and security events.
    """

    __tablename__ = "account_creation_audit"

    # Core relationship fields
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    session_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Request details
    phone_number = Column(String(20), nullable=False, index=True)
    normalized_phone = Column(String(20), nullable=False)
    platform = Column(String(20), nullable=False, index=True)
    platform_user_id = Column(String(100), nullable=False)

    # Processing details
    status = Column(
        String(20),
        nullable=False,
        index=True
    )
    result_code = Column(String(50), nullable=True)
    result_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Data validation results
    phone_validation_result = Column(JSONB, nullable=True)
    parent_lookup_result = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Security fields
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Audit metadata
    metadata_json = Column(JSONB, default=dict, nullable=True)

    # Relationships
    user = relationship("UserAccount", back_populates="audit_records")
    session = relationship("UserSession", back_populates="audit_records")

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_account_audit_phone_status", "normalized_phone", "status"),
        Index("idx_account_audit_platform_created", "platform", "created_at"),
        Index("idx_account_audit_user_created", "user_id", "created_at"),
        Index("idx_account_audit_processing_time", "processing_time_ms"),
        {
            "schema": None,  # Uses default schema
        }
    )

    def __repr__(self) -> str:
        """String representation of AccountCreationAudit."""
        return f"<AccountCreationAudit(id={self.id}, phone={self.phone_number[:4]}****, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """Check if audit record is completed."""
        return self.completed_at is not None

    @property
    def processing_duration_ms(self) -> Optional[int]:
        """
        Get actual processing duration in milliseconds.

        Returns:
            Processing duration in milliseconds or None if not completed
        """
        if self.processing_time_ms is not None:
            return self.processing_time_ms
        elif self.completed_at is not None:
            delta = self.completed_at - self.created_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def is_successful(self) -> bool:
        """Check if account creation was successful."""
        return self.status in [
            AccountCreationStatus.ACCOUNT_CREATED,
            AccountCreationStatus.PARENT_FOUND,
            AccountCreationStatus.PHONE_VALIDATED
        ]

    @property
    def is_failure(self) -> bool:
        """Check if account creation failed."""
        return self.status in [
            AccountCreationStatus.FAILED,
            AccountCreationStatus.DUPLICATE
        ]

    @property
    def display_phone(self) -> str:
        """Get masked phone number for display."""
        if len(self.phone_number) > 7:
            return self.phone_number[:4] + '*' * (len(self.phone_number) - 7) + self.phone_number[-3:]
        else:
            return '*' * len(self.phone_number)

    @property
    def processing_steps(self) -> Dict[str, Any]:
        """Get processing steps from metadata."""
        return self.metadata_json.get("processing_steps", {}) if self.metadata_json else {}

    def mark_completed(self, result_code: str, result_message: str, session: Optional[Session] = None) -> None:
        """
        Mark audit record as completed.

        Args:
            result_code: Result code
            result_message: Result message
            session: Database session (optional)
        """
        self.completed_at = datetime.now(timezone.utc)
        self.result_code = result_code
        self.result_message = result_message

        if session:
            session.add(self)
            session.commit()

    def update_status(self, new_status: str, session: Optional[Session] = None) -> None:
        """
        Update audit status.

        Args:
            new_status: New status
            session: Database session (optional)
        """
        if new_status not in AccountCreationStatus.all_values():
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        if session:
            session.add(self)
            session.commit()

    def add_processing_step(self, step_name: str, step_data: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Add a processing step to the audit record.

        Args:
            step_name: Name of the processing step
            step_data: Step data
            session: Database session (optional)
        """
        if not self.metadata_json:
            self.metadata_json = {}
        if "processing_steps" not in self.metadata_json:
            self.metadata_json["processing_steps"] = {}

        self.metadata_json["processing_steps"][step_name] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": step_data
        }

        if session:
            session.add(self)
            session.commit()

    def set_phone_validation_result(self, validation_result: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Set phone validation result.

        Args:
            validation_result: Phone validation result
            session: Database session (optional)
        """
        self.phone_validation_result = validation_result
        self.add_processing_step("phone_validation", validation_result, session)

    def set_parent_lookup_result(self, lookup_result: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Set parent lookup result.

        Args:
            lookup_result: Parent lookup result
            session: Database session (optional)
        """
        self.parent_lookup_result = lookup_result
        self.add_processing_step("parent_lookup", lookup_result, session)

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

    def add_security_event(self, event_type: str, event_data: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Add security event to audit record.

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
        Convert audit record to dictionary.

        Args:
            include_sensitive: Whether to include sensitive information

        Returns:
            Dictionary representation of audit record
        """
        data = super().to_dict()

        # Add computed properties
        data.update({
            "is_completed": self.is_completed,
            "processing_duration_ms": self.processing_duration_ms,
            "is_successful": self.is_successful,
            "is_failure": self.is_failure,
            "display_phone": self.display_phone,
            "processing_steps": self.processing_steps
        })

        # Mask sensitive data unless explicitly requested
        if not include_sensitive:
            data["phone_number"] = self.display_phone
            data["normalized_phone"] = self.display_phone
            data["platform_user_id"] = data["platform_user_id"][:10] + "***" if data.get("platform_user_id") else None
            data["ip_address"] = None
            data["user_agent"] = None

        return data

    @classmethod
    def create_audit_record(
        cls,
        session: Session,
        phone_number: str,
        normalized_phone: str,
        platform: str,
        platform_user_id: str,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AccountCreationAudit":
        """
        Create a new audit record.

        Args:
            session: Database session
            phone_number: Original phone number
            normalized_phone: Normalized phone number
            platform: Platform
            platform_user_id: Platform-specific user ID
            user_id: User ID (optional)
            session_id: Session ID (optional)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AccountCreationAudit instance
        """
        audit_record = cls(
            phone_number=phone_number,
            normalized_phone=normalized_phone,
            platform=platform,
            platform_user_id=platform_user_id,
            user_id=user_id,
            session_id=session_id,
            status=AccountCreationStatus.INITIATED,
            ip_address=ip_address,
            user_agent=user_agent
        )

        session.add(audit_record)
        session.commit()
        session.refresh(audit_record)

        return audit_record

    @classmethod
    def find_by_phone(cls, session: Session, phone_number: str, limit: int = 10) -> list["AccountCreationAudit"]:
        """
        Find audit records by phone number.

        Args:
            session: Database session
            phone_number: Phone number
            limit: Maximum number of results

        Returns:
            List of AccountCreationAudit instances
        """
        return session.query(cls).filter(
            cls.normalized_phone == phone_number,
            cls.is_deleted == False
        ).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_user_audit_history(
        cls,
        session: Session,
        user_id: UUID,
        limit: int = 50
    ) -> list["AccountCreationAudit"]:
        """
        Get audit history for a user.

        Args:
            session: Database session
            user_id: User ID
            limit: Maximum number of results

        Returns:
            List of AccountCreationAudit instances
        """
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_deleted == False
        ).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_failed_attempts(
        cls,
        session: Session,
        hours: int = 24,
        platform: Optional[str] = None
    ) -> list["AccountCreationAudit"]:
        """
        Get failed account creation attempts.

        Args:
            session: Database session
            hours: Number of hours to look back
            platform: Optional platform filter

        Returns:
            List of failed AccountCreationAudit instances
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = session.query(cls).filter(
            cls.created_at >= cutoff_time,
            cls.status.in_([AccountCreationStatus.FAILED, AccountCreationStatus.DUPLICATE]),
            cls.is_deleted == False
        )

        if platform:
            query = query.filter(cls.platform == platform)

        return query.all()

    @classmethod
    def get_success_rate(
        cls,
        session: Session,
        hours: int = 24,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get account creation success rate statistics.

        Args:
            session: Database session
            hours: Number of hours to look back
            platform: Optional platform filter

        Returns:
            Dictionary with success rate statistics
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        base_query = session.query(cls).filter(
            cls.created_at >= cutoff_time,
            cls.is_deleted == False
        )

        if platform:
            base_query = base_query.filter(cls.platform == platform)

        # Total attempts
        total_attempts = base_query.count()

        # Successful attempts
        successful_attempts = base_query.filter(
            cls.status == AccountCreationStatus.ACCOUNT_CREATED
        ).count()

        # Failed attempts
        failed_attempts = base_query.filter(
            cls.status.in_([AccountCreationStatus.FAILED, AccountCreationStatus.DUPLICATE])
        ).count()

        # Average processing time
        avg_processing_time = base_query.filter(
            cls.processing_time_ms.isnot(None)
        ).with_entities(func.avg(cls.processing_time_ms)).scalar()

        success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0

        return {
            "period_hours": hours,
            "platform": platform or "all",
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate_percent": round(success_rate, 2),
            "average_processing_time_ms": int(avg_processing_time) if avg_processing_time else None
        }

    @classmethod
    def get_processing_analytics(cls, session: Session, days: int = 7) -> Dict[str, Any]:
        """
        Get processing analytics and performance metrics.

        Args:
            session: Database session
            days: Number of days to analyze

        Returns:
            Dictionary with processing analytics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Daily processing stats
        daily_stats = session.query(
            func.date(cls.created_at).label("date"),
            func.count(cls.id).label("total_attempts"),
            func.sum(func.case([(cls.status == AccountCreationStatus.ACCOUNT_CREATED, 1)], else_=0)).label("successful"),
            func.avg(cls.processing_time_ms).label("avg_processing_time")
        ).filter(
            cls.created_at >= cutoff_date,
            cls.is_deleted == False
        ).group_by(func.date(cls.created_at)).all()

        # Platform performance comparison
        platform_stats = session.query(
            cls.platform,
            func.count(cls.id).label("total"),
            func.sum(func.case([(cls.status == AccountCreationStatus.ACCOUNT_CREATED, 1)], else_=0)).label("successful"),
            func.avg(cls.processing_time_ms).label("avg_time")
        ).filter(
            cls.created_at >= cutoff_date,
            cls.is_deleted == False
        ).group_by(cls.platform).all()

        # Most common failure reasons
        failure_reasons = session.query(
            cls.result_code,
            func.count(cls.id).label("count")
        ).filter(
            cls.created_at >= cutoff_date,
            cls.status.in_([AccountCreationStatus.FAILED, AccountCreationStatus.DUPLICATE]),
            cls.is_deleted == False,
            cls.result_code.isnot(None)
        ).group_by(cls.result_code).order_by(func.count(cls.id).desc()).limit(10).all()

        return {
            "period_days": days,
            "daily_breakdown": [
                {
                    "date": str(stat.date),
                    "total_attempts": stat.total_attempts,
                    "successful": stat.successful or 0,
                    "success_rate": round((stat.successful or 0) / stat.total_attempts * 100, 2) if stat.total_attempts > 0 else 0,
                    "avg_processing_time_ms": int(stat.avg_processing_time) if stat.avg_processing_time else None
                }
                for stat in daily_stats
            ],
            "platform_performance": [
                {
                    "platform": stat.platform,
                    "total": stat.total,
                    "successful": stat.successful or 0,
                    "success_rate": round((stat.successful or 0) / stat.total * 100, 2) if stat.total > 0 else 0,
                    "avg_processing_time_ms": int(stat.avg_time) if stat.avg_time else None
                }
                for stat in platform_stats
            ],
            "common_failure_reasons": [
                {
                    "reason_code": stat.result_code,
                    "count": stat.count
                }
                for stat in failure_reasons
            ]
        }

    @classmethod
    def detect_anomalous_activity(
        cls,
        session: Session,
        hours: int = 1,
        threshold_attempts: int = 10
    ) -> Dict[str, Any]:
        """
        Detect anomalous account creation activity.

        Args:
            session: Database session
            hours: Time window to check
            threshold_attempts: Threshold for considering activity anomalous

        Returns:
            Dictionary with anomalous activity detection results
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # High volume from single IP
        ip_activity = session.query(
            cls.ip_address,
            func.count(cls.id).label("attempt_count")
        ).filter(
            cls.created_at >= cutoff_time,
            cls.ip_address.isnot(None),
            cls.is_deleted == False
        ).group_by(cls.ip_address).having(func.count(cls.id) > threshold_attempts).all()

        # High volume from single platform user
        platform_user_activity = session.query(
            cls.platform,
            cls.platform_user_id,
            func.count(cls.id).label("attempt_count")
        ).filter(
            cls.created_at >= cutoff_time,
            cls.is_deleted == False
        ).group_by(cls.platform, cls.platform_user_id).having(func.count(cls.id) > threshold_attempts).all()

        # High failure rate from specific sources
        failure_hotspots = session.query(
            cls.ip_address,
            func.count(cls.id).label("total"),
            func.sum(func.case([(cls.status.in_([AccountCreationStatus.FAILED, AccountCreationStatus.DUPLICATE]), 1)], else_=0)).label("failures")
        ).filter(
            cls.created_at >= cutoff_time,
            cls.ip_address.isnot(None),
            cls.is_deleted == False
        ).group_by(cls.ip_address).having(
            (func.sum(func.case([(cls.status.in_([AccountCreationStatus.FAILED, AccountCreationStatus.DUPLICATE]), 1)], else_=0)) * 1.0 / func.count(cls.id)) > 0.8
        ).all()

        return {
            "time_window_hours": hours,
            "threshold_attempts": threshold_attempts,
            "high_volume_ips": [
                {"ip_address": str(stat.ip_address), "attempt_count": stat.attempt_count}
                for stat in ip_activity
            ],
            "high_volume_platform_users": [
                {
                    "platform": stat.platform,
                    "platform_user_id": stat.platform_user_id[:10] + "***",
                    "attempt_count": stat.attempt_count
                }
                for stat in platform_user_activity
            ],
            "high_failure_rate_ips": [
                {
                    "ip_address": str(stat.ip_address),
                    "total_attempts": stat.total,
                    "failed_attempts": stat.failures,
                    "failure_rate": round(stat.failures / stat.total * 100, 2)
                }
                for stat in failure_hotspots
            ],
            "anomaly_detected": len(ip_activity) > 0 or len(platform_user_activity) > 0 or len(failure_hotspots) > 0
        }


# Import for timedelta
from datetime import timedelta