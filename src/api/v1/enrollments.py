"""
Enrollment API Endpoints

REST API endpoints for enrollment management with OCR integration.
Supports the complete enrollment workflow with 5000 FCFA flat fee.

Endpoints:
- POST /enrollments - Create new enrollment
- GET /enrollments - List enrollments with filters
- GET /enrollments/{id} - Get enrollment details
- PATCH /enrollments/{id} - Update enrollment
- POST /enrollments/{id}/documents - Upload document
- GET /enrollments/{id}/documents - List documents
- POST /enrollments/{id}/transition - Status transition

Constitution Principle II: Type safety and comprehensive validation
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging

from ...services.enrollment_service import get_enrollment_service
from ...services.document_storage_service import get_document_storage_service
from ...models.enrollment import InscriptionCreate, InscriptionUpdate, InscriptionSummary, InscriptionFilter
from ...models.document import DocumentValidationRequest, DocumentSummary
from ...middleware.permissions import require_permission, require_resource_access
from ...api.v1.auth import get_current_user
from ...utils.exceptions import ValidationError, BusinessLogicError, DocumentError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("/", response_model=InscriptionSummary, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    enrollment_data: InscriptionCreate,
    current_user: dict = Depends(require_permission("create_inscription"))
):
    """
    Create a new student enrollment.

    Fixed fee: 5000 FCFA
    Business Rules:
    - Check for existing enrollments in same year
    - Validate child's age (5-18 years)
    - Generate unique inscription number
    - Set initial status to 'brouillon'

    Requires: create_inscription permission
    """
    try:
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.create_enrollment(
            enrollment_data=enrollment_data,
            user_id=current_user['user_id']
        )

        return InscriptionSummary(
            id=enrollment.id,
            numero_unique=enrollment.numero_unique,
            nom_enfant=enrollment.nom_enfant,
            prenom_enfant=enrollment.prenom_enfant,
            annee_catechetique=enrollment.annee_catechetique,
            niveau=enrollment.niveau,
            statut=enrollment.statut,
            montant_total=enrollment.montant_total,
            montant_paye=enrollment.montant_paye,
            solde_restant=enrollment.montant_total - enrollment.montant_paye,
            created_at=enrollment.created_at
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create enrollment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create enrollment"
        )


@router.get("/", response_model=List[InscriptionSummary])
async def list_enrollments(
    annee_catechetique: Optional[str] = None,
    statut: Optional[str] = None,
    nom_enfant: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List enrollments with optional filters.

    Parents can only see their own enrollments.
    Staff can see all enrollments based on permissions.
    """
    try:
        enrollment_service = get_enrollment_service()

        # Build filters
        filters = {}
        if annee_catechetique:
            filters['annee_catechetique'] = annee_catechetique
        if statut:
            filters['statut'] = statut

        # Apply user-specific filtering
        if current_user['role'] == 'parent':
            filters['parent_id'] = current_user['user_id']
        elif nom_enfant:
            filters['nom_enfant'] = nom_enfant

        enrollments, total = await enrollment_service.search_enrollments(
            filters=filters,
            limit=limit,
            offset=offset
        )

        # Convert to summaries
        summaries = []
        for enrollment in enrollments:
            summary = InscriptionSummary(
                id=enrollment.id,
                numero_unique=enrollment.numero_unique,
                nom_enfant=enrollment.nom_enfant,
                prenom_enfant=enrollment.prenom_enfant,
                annee_catechetique=enrollment.annee_catechetique,
                niveau=enrollment.niveau,
                statut=enrollment.statut,
                montant_total=enrollment.montant_total,
                montant_paye=enrollment.montant_paye,
                solde_restant=enrollment.montant_total - enrollment.montant_paye,
                created_at=enrollment.created_at
            )
            summaries.append(summary)

        return summaries

    except Exception as e:
        logger.error(f"List enrollments failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enrollments"
        )


@router.get("/{inscription_id}", response_model=InscriptionSummary)
async def get_enrollment(
    inscription_id: str,
    current_user: dict = Depends(require_resource_access("inscription", "view"))
):
    """
    Get enrollment details by ID.

    Parents can only view their own enrollments.
    Staff can view based on permissions.
    """
    try:
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.get_enrollment_by_id(inscription_id)

        # Additional permission check for parents
        if current_user['role'] == 'parent' and enrollment.parent_id != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return InscriptionSummary(
            id=enrollment.id,
            numero_unique=enrollment.numero_unique,
            nom_enfant=enrollment.nom_enfant,
            prenom_enfant=enrollment.prenom_enfant,
            annee_catechetique=enrollment.annee_catechetique,
            niveau=enrollment.niveau,
            statut=enrollment.statut,
            montant_total=enrollment.montant_total,
            montant_paye=enrollment.montant_paye,
            solde_restant=enrollment.montant_total - enrollment.montant_paye,
            created_at=enrollment.created_at
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get enrollment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enrollment"
        )


@router.patch("/{inscription_id}", response_model=InscriptionSummary)
async def update_enrollment(
    inscription_id: str,
    update_data: InscriptionUpdate,
    current_user: dict = Depends(require_resource_access("inscription", "edit"))
):
    """
    Update enrollment details.

    Only enrollments in 'brouillon' or 'en_attente_paiement' status can be modified.
    Parents can only update their own enrollments.
    """
    try:
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.update_enrollment(
            inscription_id=inscription_id,
            update_data=update_data,
            user_id=current_user['user_id']
        )

        return InscriptionSummary(
            id=enrollment.id,
            numero_unique=enrollment.numero_unique,
            nom_enfant=enrollment.nom_enfant,
            prenom_enfant=enrollment.prenom_enfant,
            annee_catechetique=enrollment.annee_catechetique,
            niveau=enrollment.niveau,
            statut=enrollment.statut,
            montant_total=enrollment.montant_total,
            montant_paye=enrollment.montant_paye,
            solde_restant=enrollment.montant_total - enrollment.montant_paye,
            created_at=enrollment.created_at
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update enrollment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update enrollment"
        )


@router.post("/{inscription_id}/documents", response_model=DocumentSummary)
async def upload_document(
    inscription_id: str,
    file: UploadFile = File(...),
    type_document: str = Form(...),
    current_user: dict = Depends(require_resource_access("inscription", "edit"))
):
    """
    Upload a document for an enrollment.

    Supported types:
    - extrait_naissance: Birth certificate
    - extrait_bapteme: Baptism certificate
    - attestation_transfert: Transfer attestation
    - preuve_paiement: Payment proof

    File size limit: 10MB
    Supported formats: PDF, JPG, PNG, HEIC
    """
    try:
        # Validate enrollment exists and user has access
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.get_enrollment_by_id(inscription_id)

        if current_user['role'] == 'parent' and enrollment.parent_id != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Read file content
        file_content = await file.read()

        # Upload document
        document_service = get_document_storage_service()
        document = await document_service.upload_document(
            file_data=file_content,
            filename=file.filename,
            inscription_id=inscription_id,
            document_type=type_document,
            user_id=current_user['user_id']
        )

        return DocumentSummary(
            id=document.id,
            inscription_id=document.inscription_id,
            type_document=document.type_document,
            type_display=document.get_type_display(),
            format=document.format,
            taille_bytes=document.taille_bytes,
            uploaded_at=document.uploaded_at,
            statut_ocr=document.statut_ocr,
            status_display=document.get_status_display(),
            confiance_ocr=document.confiance_ocr,
            valide_par_parent=document.valide_par_parent
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DocumentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/{inscription_id}/documents", response_model=List[DocumentSummary])
async def list_enrollment_documents(
    inscription_id: str,
    current_user: dict = Depends(require_resource_access("inscription", "view"))
):
    """
    List all documents for an enrollment.
    """
    try:
        # Validate enrollment exists and user has access
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.get_enrollment_by_id(inscription_id)

        if current_user['role'] == 'parent' and enrollment.parent_id != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get documents
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT * FROM documents WHERE inscription_id = ? ORDER BY uploaded_at DESC"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (inscription_id,))
            rows = await cursor.fetchall()

        documents = []
        for row in rows:
            doc_data = dict(row)
            document = Document.from_db_row(doc_data)

            summary = DocumentSummary(
                id=document.id,
                inscription_id=document.inscription_id,
                type_document=document.type_document,
                type_display=document.get_type_display(),
                format=document.format,
                taille_bytes=document.taille_bytes,
                uploaded_at=document.uploaded_at,
                statut_ocr=document.statut_ocr,
                status_display=document.get_status_display(),
                confiance_ocr=document.confiance_ocr,
                valide_par_parent=document.valide_par_parent
            )
            documents.append(summary)

        return documents

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{inscription_id}/documents/{document_id}")
async def get_document_file(
    inscription_id: str,
    document_id: str,
    current_user: dict = Depends(require_resource_access("inscription", "view"))
):
    """
    Download document file content.
    """
    try:
        # Validate enrollment access
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.get_enrollment_by_id(inscription_id)

        if current_user['role'] == 'parent' and enrollment.parent_id != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get document file
        document_service = get_document_storage_service()
        file_content = await document_service.get_document_file(document_id)

        # Get document info for content type
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT format, type_document FROM documents WHERE id = ?"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            doc_info = await cursor.fetchone()

        if not doc_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Determine content type
        content_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'heic': 'image/heic'
        }

        content_type = content_types.get(doc_info['format'], 'application/octet-stream')

        # Return file
        return StreamingResponse(
            iter([file_content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={doc_info['type_document']}_{document_id}.{doc_info['format']}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document file failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.post("/{inscription_id}/transition")
async def transition_enrollment_status(
    inscription_id: str,
    new_status: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(require_permission("enrollment_management"))
):
    """
    Transition enrollment to a new status.

    Available transitions:
    - brouillon → en_attente_paiement
    - en_attente_paiement → active (if payment complete)
    - en_attente_paiement → paiement_partiel
    - paiement_partiel → active
    - Any status → annulee

    Requires: enrollment_management permission
    """
    try:
        enrollment_service = get_enrollment_service()
        enrollment = await enrollment_service.transition_status(
            inscription_id=inscription_id,
            new_status=new_status,
            user_id=current_user['user_id'],
            reason=reason
        )

        return {
            "message": f"Enrollment {enrollment.numero_unique} status updated to {new_status}",
            "inscription_id": enrollment.id,
            "numero_unique": enrollment.numero_unique,
            "old_status": enrollment.statut,
            "new_status": new_status
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Status transition failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transition status"
        )