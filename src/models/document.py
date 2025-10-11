"""
Document Models for OCR Processing

Pydantic models for document management with OCR extraction,
validation, and file storage integration.

Features:
- Document metadata and OCR results
- File upload validation (≤10MB per FR-002)
- French document OCR extraction
- Parent validation workflow

Constitution Principle II: Type safety throughout codebase
Research Decision: research.md#1 - OCR Library Selection
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

from .base import DatabaseModel, TimestampMixin, DocumentType, StatutOCR


class ExtractionData(BaseModel):
    """OCR extracted data structure."""
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[str] = None
    lieu_naissance: Optional[str] = None
    date_bapteme: Optional[str] = None
    paroisse_bapteme: Optional[str] = None
    nom_pretre_bapteme: Optional[str] = None
    paroisse_origine: Optional[str] = None
    annee_catechisme_precedente: Optional[str] = None
    reference_document: Optional[str] = None
    confidence_scores: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            k: v for k, v in self.__dict__.items()
            if v is not None
        }


class DocumentCreate(BaseModel):
    """Request model for document upload."""
    inscription_id: str = Field(..., description="Enrollment ID")
    type_document: str = Field(..., description="Document type")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="File format")

    @validator('type_document')
    def validate_type_document(cls, v):
        """Validate document type."""
        valid_types = [
            DocumentType.EXTRAIT_NAISSANCE,
            DocumentType.EXTRAIT_BAPTEME,
            DocumentType.ATTESTATION_TRANSFERT,
            DocumentType.PREUVE_PAIEMENT
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid document type. Valid types: {', '.join(valid_types)}")
        return v

    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size (max 10MB per FR-002)."""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f"File size exceeds maximum allowed size (10MB)")
        if v <= 0:
            raise ValueError("File size must be greater than 0")
        return v

    @validator('format')
    def validate_format(cls, v):
        """Validate file format."""
        valid_formats = ['pdf', 'jpg', 'jpeg', 'png', 'heic']
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid file format. Valid formats: {', '.join(valid_formats)}")
        return v.lower()


class DocumentUpdate(BaseModel):
    """Request model for document updates."""
    statut_ocr: Optional[str] = None
    donnees_extraites: Optional[Dict[str, Any]] = None
    donnees_validees: Optional[Dict[str, Any]] = None
    confiance_ocr: Optional[float] = None
    valide_par_parent: Optional[bool] = None
    error_message: Optional[str] = None

    @validator('statut_ocr')
    def validate_statut_ocr(cls, v):
        """Validate OCR status."""
        if v is not None:
            valid_statuses = [
                StatutOCR.EN_ATTENTE,
                StatutOCR.EN_COURS,
                StatutOCR.SUCCES,
                StatutOCR.ECHEC,
                StatutOCR.MANUEL
            ]
            if v not in valid_statuses:
                raise ValueError(f"Invalid OCR status. Valid statuses: {', '.join(valid_statuses)}")
        return v

    @validator('confiance_ocr')
    def validate_confiance_ocr(cls, v):
        """Validate confidence score (0.0-1.0)."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class Document(DatabaseModel, TimestampMixin):
    """
    Complete document model with OCR processing metadata.

    Represents uploaded documents with OCR extraction results
    and parent validation workflow.
    """
    id: str = Field(..., description="Document UUID")
    inscription_id: str = Field(..., description="Enrollment ID")
    type_document: str = Field(..., description="Document type")
    fichier_path: str = Field(..., description="File path in storage")
    format: str = Field(..., description="File format (pdf, jpg, png, heic)")
    taille_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    statut_ocr: str = Field(..., description="OCR processing status")
    donnees_extraites: Optional[str] = Field(None, description="Raw OCR data (JSON)")
    donnees_validees: Optional[str] = Field(None, description="Parent-validated data (JSON)")
    confiance_ocr: Optional[float] = Field(None, description="Overall OCR confidence (0.0-1.0)")
    valide_par_parent: bool = Field(default=False, description="Parent has validated OCR data")
    validated_at: Optional[datetime] = Field(None, description="Parent validation timestamp")
    error_message: Optional[str] = Field(None, description="OCR processing error details")

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return round(self.taille_bytes / (1024 * 1024), 2)

    @property
    def is_image(self) -> bool:
        """Check if document is an image file."""
        return self.format in ['jpg', 'jpeg', 'png', 'heic']

    @property
    def is_pdf(self) -> bool:
        """Check if document is a PDF file."""
        return self.format == 'pdf'

    @property
    def ocr_completed(self) -> bool:
        """Check if OCR processing is complete (success or failure)."""
        return self.statut_ocr in [StatutOCR.SUCCES, StatutOCR.ECHEC, StatutOCR.MANUEL]

    @property
    def ocr_successful(self) -> bool:
        """Check if OCR processing was successful."""
        return self.statut_ocr == StatutOCR.SUCCES

    @property
    def requires_parent_validation(self) -> bool:
        """Check if document requires parent validation."""
        return (self.ocr_successful and
                self.confiance_ocr is not None and
                self.confiance_ocr >= 0.7 and
                not self.valide_par_parent)

    @property
    def is_validated(self) -> bool:
        """Check if document has been validated by parent."""
        return self.valide_par_parent

    @property
    def extraction_data(self) -> Optional[ExtractionData]:
        """Get parsed extraction data."""
        if not self.donnees_extraites:
            return None

        try:
            import json
            data = json.loads(self.donnees_extraites)
            return ExtractionData(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    @property
    def validated_data(self) -> Optional[ExtractionData]:
        """Get parent-validated data."""
        if not self.donnees_validees:
            return None

        try:
            import json
            data = json.loads(self.donnees_validees)
            return ExtractionData(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    def get_display_data(self) -> Optional[ExtractionData]:
        """Get data to display (validated data preferred, extracted data fallback)."""
        return self.validated_data or self.extraction_data

    def can_be_processed(self) -> bool:
        """Check if document can be processed by OCR."""
        return self.statut_ocr == StatutOCR.EN_ATTENTE

    def can_be_validated_by_parent(self) -> bool:
        """Check if parent can validate this document."""
        return (self.ocr_successful and
                not self.valide_par_parent and
                self.confiance_ocr is not None and
                self.confiance_ocr >= 0.7)

    def get_type_display(self) -> str:
        """Get human-readable document type display."""
        type_map = {
            DocumentType.EXTRAIT_NAISSANCE: "Extrait de Naissance",
            DocumentType.EXTRAIT_BAPTEME: "Extrait de Baptême",
            DocumentType.ATTESTATION_TRANSFERT: "Attestation de Transfert",
            DocumentType.PREUVE_PAIEMENT: "Preuve de Paiement"
        }
        return type_map.get(self.type_document, self.type_document)

    def get_status_display(self) -> str:
        """Get human-readable status display."""
        status_map = {
            StatutOCR.EN_ATTENTE: "En attente de traitement",
            StatutOCR.EN_COURS: "Traitement OCR en cours...",
            StatutOCR.SUCCES: "OCR terminé avec succès",
            StatutOCR.ECHEC: "Échec du traitement OCR",
            StatutOCR.MANUEL: "Saisie manuelle requise"
        }
        return status_map.get(self.statut_ocr, self.statut_ocr)


class DocumentSummary(BaseModel):
    """Summary model for document lists."""
    id: str
    inscription_id: str
    type_document: str
    type_display: str
    format: str
    taille_bytes: int
    uploaded_at: datetime
    statut_ocr: str
    status_display: str
    confiance_ocr: Optional[float]
    valide_par_parent: bool

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return round(self.taille_bytes / (1024 * 1024), 2)

    @property
    def confidence_percentage(self) -> Optional[int]:
        """Get confidence as percentage."""
        if self.confiance_ocr is not None:
            return int(self.confiance_ocr * 100)
        return None


class DocumentValidationRequest(BaseModel):
    """Request model for parent OCR validation."""
    donnees_validees: ExtractionData = Field(..., description="Validated OCR data")

    def to_json(self) -> str:
        """Convert to JSON string for storage."""
        return self.donnees_validees.json()


class OCRProcessingRequest(BaseModel):
    """Request model for OCR processing."""
    document_id: str = Field(..., description="Document ID to process")
    force_reprocess: bool = Field(default=False, description="Force reprocessing even if already processed")


class OCRProcessingResult(BaseModel):
    """Result model for OCR processing."""
    document_id: str
    statut_ocr: str
    donnees_extraites: Optional[Dict[str, Any]]
    confiance_ocr: Optional[float]
    error_message: Optional[str]
    processing_time_seconds: Optional[float]


# Document business logic functions
def validate_document_requirements(inscription_data: Dict[str, Any]) -> List[str]:
    """
    Get required document types based on enrollment data.

    Args:
        inscription_data: Enrollment information

    Returns:
        List of required document types
    """
    required = [DocumentType.EXTRAIT_NAISSANCE]

    if inscription_data.get('date_bapteme'):
        required.append(DocumentType.EXTRAIT_BAPTEME)

    if inscription_data.get('paroisse_origine'):
        required.append(DocumentType.ATTESTATION_TRANSFERT)

    return required


def check_document_completion(inscription_id: str, documents: List[Document]) -> Dict[str, Any]:
    """
    Check if all required documents are uploaded and validated.

    Args:
        inscription_id: Enrollment ID
        documents: List of documents for the enrollment

    Returns:
        Dict with completion status
    """
    # Group documents by type
    doc_by_type = {doc.type_document: doc for doc in documents}

    # Determine required types based on enrollment data
    # This would typically come from the enrollment record
    required_types = [DocumentType.EXTRAIT_NAISSANCE]  # Simplified

    completed = []
    missing = []
    pending_validation = []

    for doc_type in required_types:
        if doc_type in doc_by_type:
            doc = doc_by_type[doc_type]
            if doc.valide_par_parent:
                completed.append(doc_type)
            elif doc.ocr_successful:
                pending_validation.append(doc_type)
            else:
                missing.append(doc_type)
        else:
            missing.append(doc_type)

    return {
        "completed": completed,
        "missing": missing,
        "pending_validation": pending_validation,
        "is_fully_validated": len(missing) == 0 and len(pending_validation) == 0,
        "has_all_uploaded": len(missing) == 0
    }


def calculate_document_storage_path(inscription_id: str, document_type: str, filename: str) -> str:
    """
    Calculate storage path for document in MinIO.

    Args:
        inscription_id: Enrollment ID
        document_type: Document type
        filename: Original filename

    Returns:
        str: Storage path (e.g., "2025/inscription_id/type.ext")
    """
    from datetime import datetime
    year = datetime.now().year

    # Clean filename and extract extension
    clean_filename = filename.replace(' ', '_').lower()
    if '.' in clean_filename:
        name_part, ext = clean_filename.rsplit('.', 1)
    else:
        name_part = clean_filename
        ext = 'unknown'

    # Create unique filename
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    storage_filename = f"{name_part}_{unique_id}.{ext}"

    return f"{year}/{inscription_id}/{document_type}/{storage_filename}"