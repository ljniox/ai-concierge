"""
Document API Endpoints

REST API endpoints for document management with OCR validation.
Supports document upload, OCR processing, and parent validation workflow.

Endpoints:
- GET /documents/{id} - Get document details with OCR results
- POST /documents/{id} - Validate OCR extracted data
- POST /documents/{id}/reprocess - Re-run OCR processing
- GET /documents/{id}/status - Get processing status

Constitution Principle II: Type safety and comprehensive validation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
import logging

from ...services.ocr_service import get_ocr_service
from ...services.document_storage_service import get_document_storage_service
from ...models.document import Document, DocumentSummary, DocumentValidationRequest
from ...middleware.permissions import require_resource_access
from ...api.v1.auth import get_current_user
from ...utils.exceptions import ValidationError, OCRError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentSummary)
async def get_document(
    document_id: str,
    current_user: dict = Depends(require_resource_access("document", "view"))
):
    """
    Get document details with OCR results.

    Returns:
    - Document metadata
    - OCR extraction results
    - Confidence scores
    - Validation status
    """
    try:
        # Get document from database
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT * FROM documents WHERE id = ?"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        document = Document.from_db_row(dict(row))

        # Check user access (parent can only view their own documents)
        if current_user['role'] == 'parent':
            # Get enrollment to check parent ownership
            enrollment_query = "SELECT parent_id FROM inscriptions WHERE id = ?"
            cursor = await conn.execute(enrollment_query, (document.inscription_id,))
            enrollment = await cursor.fetchone()

            if not enrollment or enrollment['parent_id'] != current_user['user_id']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.get("/{document_id}/details")
async def get_document_details(
    document_id: str,
    current_user: dict = Depends(require_resource_access("document", "view"))
):
    """
    Get detailed document information including OCR extraction data.

    Returns:
    - Complete document metadata
    - Raw OCR extracted data
    - Parent-validated data (if available)
    - Processing history
    """
    try:
        # Get document with full details
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT * FROM documents WHERE id = ?"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        document = Document.from_db_row(dict(row))

        # Check access permissions
        if current_user['role'] == 'parent':
            enrollment_query = "SELECT parent_id FROM inscriptions WHERE id = ?"
            cursor = await conn.execute(enrollment_query, (document.inscription_id,))
            enrollment = await cursor.fetchone()

            if not enrollment or enrollment['parent_id'] != current_user['user_id']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        # Prepare response with OCR data
        response = {
            "id": document.id,
            "inscription_id": document.inscription_id,
            "type_document": document.type_document,
            "type_display": document.get_type_display(),
            "format": document.format,
            "taille_bytes": document.taille_bytes,
            "file_size_mb": document.file_size_mb,
            "uploaded_at": document.uploaded_at.isoformat(),
            "statut_ocr": document.statut_ocr,
            "status_display": document.get_status_display(),
            "confiance_ocr": document.confiance_ocr,
            "confiance_percentage": int(document.confiance_ocr * 100) if document.confiance_ocr else None,
            "valide_par_parent": document.valide_par_parent,
            "validated_at": document.validated_at.isoformat() if document.validated_at else None,
            "error_message": document.error_message,
            "extraction_data": document.extraction_data.dict() if document.extraction_data else None,
            "validated_data": document.validated_data.dict() if document.validated_data else None,
            "display_data": document.get_display_data().dict() if document.get_display_data() else None,
            "can_be_validated": document.can_be_validated_by_parent(),
            "is_image": document.is_image,
            "is_pdf": document.is_pdf,
            "ocr_completed": document.ocr_completed,
            "ocr_successful": document.ocr_successful
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document details failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document details"
        )


@router.post("/{document_id}/validate")
async def validate_document_ocr(
    document_id: str,
    validation_request: DocumentValidationRequest,
    current_user: dict = Depends(require_resource_access("document", "edit"))
):
    """
    Validate OCR extracted data as parent.

    Parents can:
    - Accept OCR extracted data as-is
    - Modify extracted data before validation
    - Mark data as validated

    Only documents with confidence >= 70% can be validated.
    """
    try:
        # Get document
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT * FROM documents WHERE id = ?"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        document = Document.from_db_row(dict(row))

        # Check if document can be validated
        if not document.can_be_validated_by_parent():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document cannot be validated. Status: {document.statut_ocr}, Confidence: {document.confiance_ocr}"
            )

        # Check parent ownership
        if current_user['role'] == 'parent':
            enrollment_query = "SELECT parent_id FROM inscriptions WHERE id = ?"
            cursor = await conn.execute(enrollment_query, (document.inscription_id,))
            enrollment = await cursor.fetchone()

            if not enrollment or enrollment['parent_id'] != current_user['user_id']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        # Save validated data
        import json
        validated_data_json = validation_request.to_json()

        update_query = """
        UPDATE documents
        SET donnees_validees = ?,
            valide_par_parent = TRUE,
            validated_at = datetime('now')
        WHERE id = ?
        """

        await conn.execute(update_query, (validated_data_json, document_id))
        await conn.commit()

        # Log validation
        from ...services.audit_service import log_user_action
        await log_user_action(
            user_id=current_user['user_id'],
            action_type="validate_ocr",
            entity_type="document",
            entity_id=document_id,
            details={
                "document_type": document.type_document,
                "confidence_ocr": document.confiance_ocr,
                "validation_data_keys": list(validation_request.donnees_validees.dict().keys())
            },
            statut_action="succes"
        )

        logger.info(f"Document {document_id} validated by parent {current_user['user_id']}")

        return {
            "message": "Document validated successfully",
            "document_id": document_id,
            "validated_fields": list(validation_request.donnees_validees.dict().keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate document"
        )


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    force_reprocess: bool = False,
    current_user: dict = Depends(require_resource_access("document", "edit"))
):
    """
    Re-run OCR processing for a document.

    Useful when:
    - Initial OCR processing failed
    - Better image preprocessing is needed
    - Document needs re-analysis after improvements

    Admin/staff only operation.
    """
    try:
        # Check permissions (parents cannot reprocess)
        if current_user['role'] == 'parent':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reprocessing documents requires staff permissions"
            )

        # Get document to verify it exists
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT * FROM documents WHERE id = ?"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Trigger OCR reprocessing
        ocr_service = get_ocr_service()
        result = await ocr_service.process_document(document_id, force_reprocess=force_reprocess)

        # Log reprocessing
        from ...services.audit_service import log_user_action
        await log_user_action(
            user_id=current_user['user_id'],
            action_type="reprocess_document",
            entity_type="document",
            entity_id=document_id,
            details={
                "force_reprocess": force_reprocess,
                "ocr_confidence": result.get('confiance_ocr'),
                "ocr_status": result.get('statut_ocr')
            },
            statut_action="succes"
        )

        return {
            "message": "Document reprocessing initiated",
            "document_id": document_id,
            "processing_status": result.get('statut_ocr'),
            "confidence_score": result.get('confiance_ocr')
        }

    except HTTPException:
        raise
    except OCRError as e:
        logger.error(f"Document reprocessing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OCR processing failed: {e}"
        )
    except Exception as e:
        logger.error(f"Document reprocessing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess document"
        )


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: dict = Depends(require_resource_access("document", "view"))
):
    """
    Get real-time document processing status.

    Useful for:
    - Polling OCR processing progress
    - Checking validation status
    - Monitoring error states
    """
    try:
        # Get document status
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = """
        SELECT statut_ocr, confiance_ocr, valide_par_parent, validated_at,
               error_message, uploaded_at, created_at
        FROM documents WHERE id = ?
        """
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check access permissions
        document_query = "SELECT inscription_id FROM documents WHERE id = ?"
        cursor = await conn.execute(document_query, (document_id,))
        doc_info = await cursor.fetchone()

        if current_user['role'] == 'parent':
            enrollment_query = "SELECT parent_id FROM inscriptions WHERE id = ?"
            cursor = await conn.execute(enrollment_query, (doc_info['inscription_id'],))
            enrollment = await cursor.fetchone()

            if not enrollment or enrollment['parent_id'] != current_user['user_id']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        # Calculate processing time
        processing_time = None
        if row['created_at'] and row['statut_ocr'] != 'en_attente':
            try:
                from datetime import datetime
                created = datetime.fromisoformat(row['created_at'])
                now = datetime.utcnow()
                processing_time = (now - created).total_seconds()
            except:
                pass

        response = {
            "document_id": document_id,
            "statut_ocr": row['statut_ocr'],
            "status_display": {
                "en_attente": "En attente de traitement",
                "en_cours": "Traitement OCR en cours...",
                "succes": "OCR terminé avec succès",
                "echec": "Échec du traitement OCR",
                "manuel": "Saisie manuelle requise"
            }.get(row['statut_ocr'], row['statut_ocr']),
            "confiance_ocr": row['confiance_ocr'],
            "confiance_percentage": int(row['confiance_ocr'] * 100) if row['confiance_ocr'] else None,
            "valide_par_parent": bool(row['valide_par_parent']),
            "validated_at": row['validated_at'],
            "error_message": row['error_message'],
            "uploaded_at": row['uploaded_at'],
            "processing_time_seconds": processing_time,
            "can_be_validated": (
                row['statut_ocr'] == 'succes' and
                row['confiance_ocr'] is not None and
                row['confiance_ocr'] >= 0.7 and
                not row['valide_par_parent']
            ),
            "is_fully_processed": row['statut_ocr'] in ['succes', 'echec', 'manuel'],
            "requires_action": (
                row['statut_ocr'] == 'echec' or
                (row['statut_ocr'] == 'succes' and not row['valide_par_parent'])
            )
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document status"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: dict = Depends(require_resource_access("document", "view"))
):
    """
    Download original document file.

    Returns the file with appropriate content type and filename.
    """
    try:
        # Get document info
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT inscription_id, format, type_document FROM documents WHERE id = ?"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (document_id,))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check access permissions
        if current_user['role'] == 'parent':
            enrollment_query = "SELECT parent_id FROM inscriptions WHERE id = ?"
            cursor = await conn.execute(enrollment_query, (row['inscription_id'],))
            enrollment = await cursor.fetchone()

            if not enrollment or enrollment['parent_id'] != current_user['user_id']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        # Get file content
        document_service = get_document_storage_service()
        file_content = await document_service.get_document_file(document_id)

        # Determine content type
        content_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'heic': 'image/heic'
        }

        content_type = content_types.get(row['format'], 'application/octet-stream')

        # Return file
        return StreamingResponse(
            iter([file_content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={row['type_document']}_{document_id}.{row['format']}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download document failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )