"""
Base database models for the automatic account creation system.

This module provides base classes and shared functionality for all database models
including UUID primary keys, timestamp fields, and common database operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, TypeVar, Type, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, DateTime, String, Boolean, Text, func, event
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr, Session, relationship
from sqlalchemy.sql import select
import sqlalchemy as sa

Base = declarative_base()

ModelType = TypeVar("ModelType", bound="BaseModel")


class BaseSQLModel(Base):
    """
    Base SQLAlchemy model with common fields and functionality.

    All database models should inherit from this class to get:
    - UUID primary key
    - Timestamp fields (created_at, updated_at)
    - Automatic updated_at timestamp management
    - Soft delete support
    """

    __abstract__ = True

    id = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    metadata_json = Column(
        JSONB,
        default=dict,
        nullable=True
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        exclude_fields = exclude_fields or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value

        return result

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def create(cls, session: Session, **kwargs) -> "BaseSQLModel":
        """Create and save new instance."""
        instance = cls(**kwargs)
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return instance

    def save(self, session: Session) -> None:
        """Save current instance."""
        session.add(self)
        session.commit()
        session.refresh(self)

    def delete(self, session: Session, soft: bool = True) -> None:
        """Delete instance (soft delete by default)."""
        if soft:
            self.is_deleted = True
            session.add(self)
            session.commit()
        else:
            session.delete(self)
            session.commit()

    @classmethod
    def get_by_id(cls, session: Session, id: UUID) -> Optional["BaseSQLModel"]:
        """Get instance by ID."""
        return session.query(cls).filter(
            cls.id == id,
            cls.is_deleted == False
        ).first()

    @classmethod
    def get_all(cls, session: Session, limit: Optional[int] = None) -> List["BaseSQLModel"]:
        """Get all non-deleted instances."""
        query = session.query(cls).filter(cls.is_deleted == False)
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def exists(cls, session: Session, **filters) -> bool:
        """Check if record exists with given filters."""
        return session.query(
            session.query(cls).filter(
                cls.is_deleted == False,
                *[getattr(cls, k) == v for k, v in filters.items()]
            ).exists()
        ).scalar()


# Event listener for automatic updated_at timestamp
@event.listens_for(BaseSQLModel, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """Automatically update updated_at field before update."""
    target.updated_at = datetime.now(timezone.utc)


class BaseModel(BaseModel):
    """
    Base Pydantic model with common fields and validation.

    All Pydantic models should inherit from this class to get:
    - Common field validation
    - Automatic timestamp handling
    - UUID field support
    - JSON metadata support
    """

    class Config:
        from_attributes = True
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

    id: UUID = Field(default_factory=uuid4, description="Primary key")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        """Ensure updated_at is always set to current time."""
        return datetime.now(timezone.utc)


# ==============================================================================
# ACCOUNT CREATION SPECIFIC MODELS
# ==============================================================================

class AccountStatus:
    """Account status enum for user accounts."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"

    @classmethod
    def all_values(cls):
        return [cls.ACTIVE, cls.INACTIVE, cls.SUSPENDED, cls.DELETED]


class ConsentLevel:
    """GDPR consent level enum."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"

    @classmethod
    def all_values(cls):
        return [cls.MINIMAL, cls.STANDARD, cls.FULL]


class CreatedVia:
    """Account creation platform enum."""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    MANUAL = "manual"

    @classmethod
    def all_values(cls):
        return [cls.WHATSAPP, cls.TELEGRAM, cls.MANUAL]


class SessionType:
    """Session type enum."""
    ACCOUNT_CREATION = "account_creation"
    GENERAL = "general"
    ADMIN = "admin"

    @classmethod
    def all_values(cls):
        return [cls.ACCOUNT_CREATION, cls.GENERAL, cls.ADMIN]


class SessionStatus:
    """Session status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    TERMINATED = "terminated"

    @classmethod
    def all_values(cls):
        return [cls.ACTIVE, cls.INACTIVE, cls.EXPIRED, cls.TERMINATED]


class Platform:
    """Messaging platform enum."""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

    @classmethod
    def all_values(cls):
        return [cls.WHATSAPP, cls.TELEGRAM]


class ProcessingStatus:
    """Webhook processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    IGNORED = "ignored"

    @classmethod
    def all_values(cls):
        return [cls.PENDING, cls.PROCESSING, cls.COMPLETED, cls.FAILED, cls.IGNORED]


class AccountCreationStatus:
    """Account creation status enum."""
    INITIATED = "initiated"
    PHONE_VALIDATED = "phone_validated"
    PARENT_FOUND = "parent_found"
    ACCOUNT_CREATED = "account_created"
    FAILED = "failed"
    DUPLICATE = "duplicate"

    @classmethod
    def all_values(cls):
        return [cls.INITIATED, cls.PHONE_VALIDATED, cls.PARENT_FOUND, cls.ACCOUNT_CREATED, cls.FAILED, cls.DUPLICATE]


class DatabaseManager:
    """Helper class for database operations."""

    @staticmethod
    def soft_delete(session: Session, model_class: Type[BaseSQLModel], id: UUID) -> bool:
        """Soft delete a record by ID."""
        instance = model_class.get_by_id(session, id)
        if instance:
            instance.delete(session, soft=True)
            return True
        return False

    @staticmethod
    def restore(session: Session, model_class: Type[BaseSQLModel], id: UUID) -> bool:
        """Restore a soft-deleted record by ID."""
        instance = session.query(model_class).filter(
            model_class.id == id,
            model_class.is_deleted == True
        ).first()

        if instance:
            instance.is_deleted = False
            session.add(instance)
            session.commit()
            return True
        return False

    @staticmethod
    def count_active(session: Session, model_class: Type[BaseSQLModel]) -> int:
        """Count active (non-deleted) records."""
        return session.query(model_class).filter(
            model_class.is_deleted == False
        ).count()

    @staticmethod
    def paginate(
        session: Session,
        model_class: Type[BaseSQLModel],
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[BaseSQLModel], int]:
        """
        Paginate results with optional filtering.

        Returns:
            Tuple of (records, total_count)
        """
        query = session.query(model_class).filter(model_class.is_deleted == False)

        if filters:
            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)

        total = query.count()

        offset = (page - 1) * per_page
        records = query.offset(offset).limit(per_page).all()

        return records, total


# Alias for legacy compatibility
DatabaseModel = BaseModel


# ==============================================================================
# LEGACY MODELS (Backward Compatibility)
# ==============================================================================

class TimestampMixin(BaseModel):
    """Mixin for models with created_at/updated_at timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    @classmethod
    def now(cls) -> datetime:
        """Get current UTC timestamp."""
        return datetime.utcnow()


class AuditMixin(TimestampMixin):
    """
    Mixin for models requiring audit trail fields.

    Includes:
    - created_at, updated_at (from TimestampMixin)
    - created_by, validated_by
    """

    created_by: str  # user_id
    validated_by: Optional[str] = None  # user_id
    validated_at: Optional[datetime] = None


# Common enums as Python classes (for type safety)
class InscriptionStatut:
    """Inscription status enum (FR-240)."""
    BROUILLON = "brouillon"
    EN_ATTENTE_PAIEMENT = "en_attente_paiement"
    PAIEMENT_PARTIEL = "paiement_partiel"
    ACTIVE = "active"
    ANNULEE = "annulee"

    @classmethod
    def all_values(cls):
        return [cls.BROUILLON, cls.EN_ATTENTE_PAIEMENT, cls.PAIEMENT_PARTIEL, cls.ACTIVE, cls.ANNULEE]


class DocumentType:
    """Document type enum (FR-010)."""
    EXTRAIT_NAISSANCE = "extrait_naissance"
    EXTRAIT_BAPTEME = "extrait_bapteme"
    ATTESTATION_TRANSFERT = "attestation_transfert"
    PREUVE_PAIEMENT = "preuve_paiement"

    @classmethod
    def all_values(cls):
        return [cls.EXTRAIT_NAISSANCE, cls.EXTRAIT_BAPTEME, cls.ATTESTATION_TRANSFERT, cls.PREUVE_PAIEMENT]


class StatutOCR:
    """OCR status enum (FR-010)."""
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    SUCCES = "succes"
    ECHEC = "echec"
    MANUEL = "manuel"

    @classmethod
    def all_values(cls):
        return [cls.EN_ATTENTE, cls.EN_COURS, cls.SUCCES, cls.ECHEC, cls.MANUEL]


class ModePaiement:
    """Payment method enum (FR-011, FR-056)."""
    CASH = "cash"
    ORANGE_MONEY = "orange_money"
    WAVE = "wave"
    FREE_MONEY = "free_money"
    RECU_PAPIER = "recu_papier"

    @classmethod
    def all_values(cls):
        return [cls.CASH, cls.ORANGE_MONEY, cls.WAVE, cls.FREE_MONEY, cls.RECU_PAPIER]


class StatutPaiement:
    """Payment status enum (FR-015)."""
    EN_ATTENTE_VALIDATION = "en_attente_validation"
    VALIDE = "valide"
    REJETE = "rejete"

    @classmethod
    def all_values(cls):
        return [cls.EN_ATTENTE_VALIDATION, cls.VALIDE, cls.REJETE]


class UserRole:
    """User roles enum (FR-021, FR-022)."""
    SUPER_ADMIN = "super_admin"
    SACRISTAIN = "sacristain"
    CURE = "cure"
    SECRETAIRE_CURE = "secretaire_cure"
    PRESIDENT_BUREAU = "president_bureau"
    SECRETAIRE_BUREAU = "secretaire_bureau"
    SECRETAIRE_ADJOINT_BUREAU = "secretaire_adjoint_bureau"
    TRESORIER_BUREAU = "tresorier_bureau"
    TRESORIER_ADJOINT_BUREAU = "tresorier_adjoint_bureau"
    RESPONSABLE_ORGANISATION_BUREAU = "responsable_organisation_bureau"
    CHARGE_RELATIONS_EXTERIEURES_BUREAU = "charge_relations_exterieures_bureau"
    CHARGE_RELATIONS_EXTERIEURES_ADJOINT_BUREAU = "charge_relations_exterieures_adjoint_bureau"
    CATECHISTE = "catechiste"
    PARENT = "parent"

    @classmethod
    def all_values(cls):
        return [
            cls.SUPER_ADMIN, cls.SACRISTAIN, cls.CURE, cls.SECRETAIRE_CURE,
            cls.PRESIDENT_BUREAU, cls.SECRETAIRE_BUREAU, cls.SECRETAIRE_ADJOINT_BUREAU,
            cls.TRESORIER_BUREAU, cls.TRESORIER_ADJOINT_BUREAU,
            cls.RESPONSABLE_ORGANISATION_BUREAU,
            cls.CHARGE_RELATIONS_EXTERIEURES_BUREAU,
            cls.CHARGE_RELATIONS_EXTERIEURES_ADJOINT_BUREAU,
            cls.CATECHISTE, cls.PARENT
        ]

    @classmethod
    def treasurer_roles(cls):
        """Roles with treasurer permissions (FR-028)."""
        return [cls.TRESORIER_BUREAU, cls.TRESORIER_ADJOINT_BUREAU]

    @classmethod
    def admin_roles(cls):
        """Roles with administrative access."""
        return [cls.SUPER_ADMIN, cls.CURE, cls.PRESIDENT_BUREAU, cls.SECRETAIRE_BUREAU]


class ActionType:
    """Audit log action types (FR-052)."""
    CREATE_INSCRIPTION = "create_inscription"
    MODIFY_INSCRIPTION = "modify_inscription"
    UPLOAD_DOCUMENT = "upload_document"
    VALIDATE_OCR = "validate_ocr"
    SUBMIT_PAIEMENT = "submit_paiement"
    VALIDATE_PAIEMENT = "validate_paiement"
    REJECT_PAIEMENT = "reject_paiement"
    MODIFY_PROFIL = "modify_profil"
    ACCESS_DATA = "access_data"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"

    @classmethod
    def all_values(cls):
        return [
            cls.CREATE_INSCRIPTION, cls.MODIFY_INSCRIPTION, cls.UPLOAD_DOCUMENT,
            cls.VALIDATE_OCR, cls.SUBMIT_PAIEMENT, cls.VALIDATE_PAIEMENT,
            cls.REJECT_PAIEMENT, cls.MODIFY_PROFIL, cls.ACCESS_DATA,
            cls.UNAUTHORIZED_ACCESS_ATTEMPT
        ]