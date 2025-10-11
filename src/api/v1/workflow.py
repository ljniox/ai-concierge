"""
Enrollment Workflow API Endpoints

API endpoints for the conversational enrollment workflow.
Integrates with WhatsApp/Telegram for step-by-step enrollment process.

Endpoints:
- POST /workflow/start - Start new enrollment workflow
- POST /workflow/{user_id}/message - Process user message
- POST /workflow/{user_id}/document - Process document upload
- GET /workflow/{user_id}/status - Get workflow status

Constitution Principle: User-friendly conversational interface
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging

from ...services.enrollment_workflow_service import get_enrollment_workflow_service, WorkflowStep
from ...middleware.permissions import require_permission
from ...api.v1.auth import get_current_user
from ...utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/start")
async def start_enrollment_workflow(
    telephone: str,
    channel: str = "whatsapp",
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new enrollment workflow.

    Args:
        telephone: User's phone number
        channel: Communication channel (whatsapp/telegram)
        current_user: Authenticated user

    Returns:
        Dict: Initial workflow step and message
    """
    try:
        workflow_service = get_enrollment_workflow_service()

        # Extract phone number from user profile if not provided
        if not telephone:
            # Get from user profile
            from ...database.sqlite_manager import get_sqlite_manager
            manager = get_sqlite_manager()

            query = "SELECT telephone FROM profil_utilisateurs WHERE user_id = ?"
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (current_user['user_id'],))
                result = await cursor.fetchone()

            if result:
                telephone = result['telephone']
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number required to start workflow"
                )

        # Start workflow
        result = await workflow_service.start_workflow(
            user_id=current_user['user_id'],
            telephone=telephone,
            channel=channel
        )

        return JSONResponse({
            "success": True,
            "workflow_id": result["workflow_id"],
            "step": result["step"],
            "message": result["message"],
            "options": result["options"]
        })

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start enrollment workflow"
        )


@router.post("/{user_id}/message")
async def process_workflow_message(
    user_id: str,
    message: str,
    current_user: dict = Depends(require_permission("create_inscription"))
):
    """
    Process a user message in the enrollment workflow.

    Args:
        user_id: Workflow/user ID
        message: User's message
        current_user: Authenticated user

    Returns:
        Dict: Next step and response message
    """
    try:
        # Verify user can access this workflow
        if current_user['user_id'] != user_id and current_user['role'] not in ['super_admin', 'secretaire_cure', 'secretaire_bureau']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        workflow_service = get_enrollment_workflow_service()
        result = await workflow_service.process_user_input(
            user_id=user_id,
            user_input=message
        )

        return JSONResponse({
            "success": True,
            "step": result["step"],
            "message": result["message"],
            "options": result.get("options"),
            "next_step": result.get("next_step")
        })

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to process workflow message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.post("/{user_id}/document")
async def process_workflow_document(
    user_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("create_inscription"))
):
    """
    Process a document upload in the enrollment workflow.

    Args:
        user_id: Workflow/user ID
        file: Uploaded file
        current_user: Authenticated user

    Returns:
        Dict: Processing result
    """
    try:
        # Verify user can access this workflow
        if current_user['user_id'] != user_id and current_user['role'] not in ['super_admin', 'secretaire_cure', 'secretaire_bureau']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Read file content
        file_content = await file.read()

        workflow_service = get_enrollment_workflow_service()
        result = await workflow_service.process_user_input(
            user_id=user_id,
            user_input="",  # No text input, just document
            file_data=file_content,
            filename=file.filename
        )

        return JSONResponse({
            "success": True,
            "step": result["step"],
            "message": result["message"],
            "options": result.get("options"),
            "filename": file.filename,
            "file_size": len(file_content)
        })

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to process workflow document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )


@router.get("/{user_id}/status")
async def get_workflow_status(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current status of an enrollment workflow.

    Args:
        user_id: Workflow/user ID
        current_user: Authenticated user

    Returns:
        Dict: Current workflow status
    """
    try:
        # Verify user can access this workflow
        if current_user['user_id'] != user_id and current_user['role'] not in ['super_admin', 'secretaire_cure', 'secretaire_bureau']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        workflow_service = get_enrollment_workflow_service()
        status = workflow_service.get_workflow_status(user_id)

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        # Get step information
        step_descriptions = {
            WorkflowStep.INITIAL_CHOICE.value: "Choix entre nouvelle inscription et réinscription",
            WorkflowStep.REENROLLMENT_SELECT.value: "Sélection du catéchumène existant",
            WorkflowStep.REENROLLMENT_CONFIRM.value: "Confirmation de la classe prédéfinie",
            WorkflowStep.AGE_VERIFICATION.value: "Vérification de l'âge via OCR",
            WorkflowStep.CLASS_SELECTION.value: "Sélection de la classe appropriée",
            WorkflowStep.PARENT_INFO.value: "Collecte des informations parent",
            WorkflowStep.CHILD_INFO.value: "Collecte des informations enfant",
            WorkflowStep.CONFIRM_DATA.value: "Confirmation des données OCR",
            WorkflowStep.YEAR_SELECTION.value: "Sélection de l'année d'inscription",
            WorkflowStep.PAYMENT_PROOF.value: "Preuve de paiement",
            WorkflowStep.TREASURER_VALIDATION.value: "Validation par le trésorier",
            WorkflowStep.COMPLETED.value: "Inscription terminée",
            WorkflowStep.PENDING_HUMAN.value: "En attente d'intervention humaine"
        }

        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "current_step": status["current_step"].value,
            "step_description": step_descriptions.get(status["current_step"].value, "Étape inconnue"),
            "enrollment_type": status.get("enrollment_type"),
            "created_at": status["created_at"].isoformat(),
            "updated_at": status["updated_at"].isoformat(),
            "data_summary": {
                "has_legacy_parent": status.get("legacy_parent") is not None,
                "has_selected_class": "selected_class" in status.get("data", {}),
                "has_parent_info": "parent_info" in status.get("data", {}),
                "has_child_info": "child_info" in status.get("data", {}),
                "has_payment_proof": "payment_document_id" in status.get("data", {}) or "payment_reference" in status.get("data", {}),
                "pending_enrollment_id": status.get("data", {}).get("pending_enrollment_id"),
                "pending_numero_unique": status.get("data", {}).get("pending_numero_unique")
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow status"
        )


@router.post("/{user_id}/reset")
async def reset_workflow(
    user_id: str,
    current_user: dict = Depends(require_permission("create_inscription"))
):
    """
    Reset a user's workflow (cancel current workflow).

    Args:
        user_id: Workflow/user ID
        current_user: Authenticated user

    Returns:
        Dict: Reset confirmation
    """
    try:
        # Verify user can access this workflow
        if current_user['user_id'] != user_id and current_user['role'] not in ['super_admin', 'secretaire_cure', 'secretaire_bureau']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        workflow_service = get_enrollment_workflow_service()

        if user_id in workflow_service.workflows:
            # Clean up workflow
            del workflow_service.workflows[user_id]

            # Log the reset
            from ...services.audit_service import log_user_action
            await log_user_action(
                user_id=current_user['user_id'],
                action_type="reset_workflow",
                entity_type="workflow",
                entity_id=user_id,
                details={"reset_by": current_user['user_id']},
                statut_action="succes"
            )

            return JSONResponse({
                "success": True,
                "message": "Workflow reset successfully",
                "user_id": user_id
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset workflow"
        )


@router.get("/admin/status")
async def get_all_workflows_status(
    current_user: dict = Depends(require_permission("enrollment_management"))
):
    """
    Get status of all active workflows (admin only).

    Args:
        current_user: Authenticated admin user

    Returns:
        List: All active workflows status
    """
    try:
        workflow_service = get_enrollment_workflow_service()

        workflows = []
        for user_id, workflow in workflow_service.workflows.items():
            # Calculate workflow duration
            duration = datetime.utcnow() - workflow["created_at"]

            workflows.append({
                "user_id": user_id,
                "telephone": workflow["telephone"],
                "channel": workflow["channel"],
                "current_step": workflow["current_step"].value,
                "enrollment_type": workflow.get("enrollment_type"),
                "created_at": workflow["created_at"].isoformat(),
                "updated_at": workflow["updated_at"].isoformat(),
                "duration_minutes": int(duration.total_seconds() / 60),
                "has_pending_enrollment": "pending_enrollment_id" in workflow.get("data", {}),
                "needs_human_intervention": workflow["current_step"] == WorkflowStep.PENDING_HUMAN
            })

        # Sort by creation time (newest first)
        workflows.sort(key=lambda x: x["created_at"], reverse=True)

        return JSONResponse({
            "success": True,
            "total_workflows": len(workflows),
            "active_workflows": len(workflows),
            "workflows": workflows
        })

    except Exception as e:
        logger.error(f"Failed to get all workflows status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflows status"
        )


@router.post("/admin/{user_id}/intervene")
async def human_intervention(
    user_id: str,
    intervention_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("enrollment_management"))
):
    """
    Admin intervention in a user's workflow.

    Args:
        user_id: Workflow/user ID
        intervention_data: Intervention details
        current_user: Authenticated admin user

    Returns:
        Dict: Intervention result
    """
    try:
        workflow_service = get_enrollment_workflow_service()

        if user_id not in workflow_service.workflows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        workflow = workflow_service.workflows[user_id]

        # Log intervention
        from ...services.audit_service import log_user_action
        await log_user_action(
            user_id=current_user['user_id'],
            action_type="human_intervention",
            entity_type="workflow",
            entity_id=user_id,
            details={
                "intervention_type": intervention_data.get("type"),
                "admin_notes": intervention_data.get("notes"),
                "workflow_step": workflow["current_step"].value
            },
            statut_action="succes"
        )

        return JSONResponse({
            "success": True,
            "message": "Human intervention logged successfully",
            "user_id": user_id,
            "intervention_by": current_user['user_id']
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to log human intervention: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process intervention"
        )