"""
Service data model for WhatsApp AI Concierge Service
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator


class ServiceType(str, Enum):
    """Service type enumeration"""
    RENSEIGNEMENT = "RENSEIGNEMENT"
    CATECHESE = "CATECHESE"
    CONTACT_HUMAIN = "CONTACT_HUMAIN"


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ServiceBase(BaseModel):
    """Base service model with common fields"""
    id: ServiceType = Field(..., description="Service identifier")
    name: str = Field(..., description="Service display name")
    description: str = Field(..., description="Service description")
    is_active: bool = Field(default=True, description="Whether the service is active")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Service configuration")
    capabilities: List[str] = Field(default_factory=list, description="Service capabilities")
    requirements: List[str] = Field(default_factory=list, description="Service requirements")


class ServiceCreate(ServiceBase):
    """Service model for creation"""
    pass


class ServiceUpdate(BaseModel):
    """Service model for updates"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    requirements: Optional[List[str]] = None


class Service(ServiceBase):
    """Complete service model"""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: ServiceStatus = Field(default=ServiceStatus.ACTIVE, description="Service status")
    version: str = Field(default="1.0.0", description="Service version")
    author: Optional[str] = Field(None, description="Service author")
    tags: List[str] = Field(default_factory=list, description="Service tags")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Service metrics")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True

    @validator('id')
    def validate_service_id(cls, v):
        """Validate service ID"""
        if v not in [member.value for member in ServiceType]:
            raise ValueError(f"Invalid service ID. Must be one of: {[member.value for member in ServiceType]}")
        return v

    @validator('capabilities')
    def validate_capabilities(cls, v):
        """Validate service capabilities"""
        if not isinstance(v, list):
            raise ValueError("Capabilities must be a list")
        return v

    @validator('requirements')
    def validate_requirements(cls, v):
        """Validate service requirements"""
        if not isinstance(v, list):
            raise ValueError("Requirements must be a list")
        return v

    @validator('metrics')
    def validate_metrics(cls, v):
        """Validate service metrics"""
        if not isinstance(v, dict):
            raise ValueError("Metrics must be a dictionary")
        return v

    @property
    def is_available(self) -> bool:
        """Check if service is available"""
        return self.is_active and self.status == ServiceStatus.ACTIVE

    @property
    def display_info(self) -> Dict[str, Any]:
        """Get display information for the service"""
        return {
            "id": self.id.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "version": self.version,
            "capabilities": self.capabilities,
            "tags": self.tags
        }

    @property
    def usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics from metrics"""
        return {
            "total_interactions": self.metrics.get("total_interactions", 0),
            "success_rate": self.metrics.get("success_rate", 0.0),
            "average_response_time": self.metrics.get("average_response_time", 0.0),
            "error_rate": self.metrics.get("error_rate", 0.0)
        }

    def update_metrics(self, interaction_success: bool, response_time: float):
        """Update service metrics"""
        if "total_interactions" not in self.metrics:
            self.metrics["total_interactions"] = 0
        if "successful_interactions" not in self.metrics:
            self.metrics["successful_interactions"] = 0
        if "total_response_time" not in self.metrics:
            self.metrics["total_response_time"] = 0.0

        self.metrics["total_interactions"] += 1
        self.metrics["total_response_time"] += response_time

        if interaction_success:
            self.metrics["successful_interactions"] += 1

        # Calculate rates
        if self.metrics["total_interactions"] > 0:
            self.metrics["success_rate"] = (
                self.metrics["successful_interactions"] / self.metrics["total_interactions"]
            )
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["total_interactions"]
            )

        self.metrics["error_rate"] = 1.0 - self.metrics["success_rate"]
        self.updated_at = datetime.now()

    def add_capability(self, capability: str):
        """Add capability to service"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.updated_at = datetime.now()

    def remove_capability(self, capability: str):
        """Remove capability from service"""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            self.updated_at = datetime.now()

    def set_maintenance(self, reason: str = ""):
        """Set service to maintenance mode"""
        self.status = ServiceStatus.MAINTENANCE
        if reason:
            self.config["maintenance_reason"] = reason
        self.updated_at = datetime.now()

    def activate_service(self):
        """Activate service"""
        self.status = ServiceStatus.ACTIVE
        self.is_active = True
        if "maintenance_reason" in self.config:
            del self.config["maintenance_reason"]
        self.updated_at = datetime.now()

    def deactivate_service(self):
        """Deactivate service"""
        self.status = ServiceStatus.INACTIVE
        self.is_active = False
        self.updated_at = datetime.now()


class ServiceResponse(Service):
    """Service model for API responses"""
    pass


class ServiceInDB(Service):
    """Service model as stored in database"""
    # Add any database-specific fields here
    pass


class ServiceWithStats(ServiceResponse):
    """Service model with additional statistics"""
    weekly_usage: Dict[str, int] = Field(default_factory=dict, description="Weekly usage data")
    monthly_usage: Dict[str, int] = Field(default_factory=dict, description="Monthly usage data")
    user_satisfaction: float = Field(default=0.0, description="User satisfaction score")
    common_intents: List[Dict[str, Any]] = Field(default_factory=list, description="Common user intents")


class ServiceListResponse(BaseModel):
    """Response model for service list"""
    services: list[ServiceResponse]
    total: int
    active_count: int
    inactive_count: int


class ServiceConfigTemplate(BaseModel):
    """Service configuration template"""
    service_id: ServiceType
    config_schema: Dict[str, Any]
    default_config: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str]


def get_default_services() -> List[ServiceCreate]:
    """
    Get default service configurations

    Returns:
        List of default services
    """
    return [
        ServiceCreate(
            id=ServiceType.RENSEIGNEMENT,
            name="Service de Renseignement",
            description="Handles general inquiries and information requests",
            is_active=True,
            capabilities=[
                "answer_questions",
                "provide_information",
                "language_detection",
                "basic_reasoning"
            ],
            requirements=["internet_access"],
            config={
                "max_response_length": 500,
                "confidence_threshold": 0.7,
                "timeout_seconds": 30
            }
        ),
        ServiceCreate(
            id=ServiceType.CATECHESE,
            name="Service de Catéchèse",
            description="Manages catechism-related questions and scheduling",
            is_active=True,
            capabilities=[
                "catechism_knowledge",
                "scheduling",
                "document_generation",
                "prayer_support"
            ],
            requirements=["internet_access", "document_storage"],
            config={
                "max_response_length": 800,
                "confidence_threshold": 0.8,
                "timeout_seconds": 45,
                "schedule_days_ahead": 30
            }
        ),
        ServiceCreate(
            id=ServiceType.CONTACT_HUMAIN,
            name="Service Contact Humain",
            description="Provides human agent escalation and contact information",
            is_active=True,
            capabilities=[
                "human_handoff",
                "contact_information",
                "emergency_response",
                "escalation_management"
            ],
            requirements=["human_agent_integration"],
            config={
                "max_response_length": 300,
                "confidence_threshold": 0.9,
                "timeout_seconds": 15,
                "available_hours": "9h-17h",
                "contact_phone": "+221771234567"
            }
        )
    ]


def validate_service_config(service_id: ServiceType, config: Dict[str, Any]) -> bool:
    """
    Validate service configuration

    Args:
        service_id: Service identifier
        config: Configuration to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic validation
    if not isinstance(config, dict):
        return False

    # Service-specific validation
    if service_id == ServiceType.RENSEIGNEMENT:
        required_fields = ["max_response_length", "confidence_threshold"]
    elif service_id == ServiceType.CATECHESE:
        required_fields = ["max_response_length", "confidence_threshold", "schedule_days_ahead"]
    elif service_id == ServiceType.CONTACT_HUMAIN:
        required_fields = ["max_response_length", "confidence_threshold", "available_hours"]
    else:
        return False

    return all(field in config for field in required_fields)