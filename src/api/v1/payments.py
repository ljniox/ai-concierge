"""
Payment Validation API Endpoints

API endpoints for payment processing, validation, and tracking.
Handles mobile money payments, receipt OCR, and treasurer validation.

Endpoints:
- POST /payments/initiate - Initiate new payment
- POST /payments/{payment_id}/validate - Validate payment with OCR
- POST /payments/{payment_id}/upload-receipt - Upload payment receipt
- GET /payments/{payment_id}/status - Get payment status
- GET /payments/queue - Get treasurer validation queue
- POST /validations/{validation_id}/process - Process treasurer validation
- GET /payments/statistics - Get payment statistics

Constitution Principle: Secure payment processing and validation
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from ...services.mobile_money_service import get_mobile_money_service, PaymentProvider, PaymentStatus
from ...services.payment_ocr_service import get_payment_ocr_service
from ...services.treasurer_validation_service import get_treasurer_validation_service, ValidationAction
from ...services.payment_tracking_service import get_payment_tracking_service
from ...middleware.permissions import require_permission
from ...api.v1.auth import get_current_user
from ...utils.exceptions import ValidationError, PaymentError, OCRError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/initiate")
async def initiate_payment(
    enrollment_id: str,
    provider: PaymentProvider,
    phone_number: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Initiate a new payment for enrollment.

    Args:
        enrollment_id: Enrollment ID
        provider: Mobile money provider
        phone_number: Payer phone number
        current_user: Authenticated user

    Returns:
        Dict: Payment initiation result
    """
    try:
        mobile_money_service = get_mobile_money_service()

        # Validate phone number for provider
        if not mobile_money_service.validate_phone_number(phone_number, provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phone number for {provider.value}"
            )

        # Generate payment reference
        payment_reference = mobile_money_service.generate_payment_reference(provider)

        # Create payment record
        payment_data = await mobile_money_service.create_payment_record(
            enrollment_id=enrollment_id,
            user_id=current_user['user_id'],
            provider=provider,
            phone_number=phone_number,
            payment_reference=payment_reference
        )

        # Track payment initiation
        tracking_service = get_payment_tracking_service()
        await tracking_service.track_payment_status_change(
            payment_id=payment_data['payment_id'],
            old_status=PaymentStatus.PENDING,  # No previous status
            new_status=PaymentStatus.PENDING,
            changed_by=current_user['user_id']
        )

        return JSONResponse({
            "success": True,
            "payment": {
                "payment_id": payment_data['payment_id'],
                "payment_reference": payment_reference,
                "provider": provider.value,
                "amount": float(payment_data['amount']),
                "currency": payment_data['currency'],
                "phone_number": phone_number,
                "expires_at": payment_data['expires_at'].isoformat(),
                "status": payment_data['status']
            },
            "instructions": {
                "message": f"Effectuez le paiement de {payment_data['amount']} {payment_data['currency']} via {provider.value}",
                "steps": [
                    f"1. Allez dans votre application {provider.value}",
                    f"2. Choisissez 'Transférer de l'argent'",
                    f"3. Entrez le numéro de téléphone: {phone_number}",
                    f"4. Entrez le montant: {payment_data['amount']} {payment_data['currency']}",
                    f"5. Confirmez la transaction",
                    f"6. Gardez la référence: {payment_reference}",
                    f"7. Envoyez une photo du reçu pour validation"
                ]
            },
            "next_steps": [
                "Effectuez le paiement via votre application mobile",
                "Téléchargez le reçu de paiement",
                "Attendez la validation par le trésorier"
            ]
        })

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to initiate payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )

@router.post("/{payment_id}/upload-receipt")
async def upload_payment_receipt(
    payment_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload payment receipt for OCR processing.

    Args:
        payment_id: Payment ID
        file: Receipt image file
        current_user: Authenticated user

    Returns:
        Dict: Upload and OCR processing result
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )

        # Get payment details
        mobile_money_service = get_mobile_money_service()
        payment = await mobile_money_service.get_payment_by_reference(payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment['user_id'] != current_user['user_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        if payment['status'] != PaymentStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is not in pending status"
            )

        # Read file content
        file_content = await file.read()

        # Save uploaded file
        import os
        upload_dir = "uploads/receipts"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = f"{upload_dir}/{payment_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Process receipt with OCR
        payment_ocr_service = get_payment_ocr_service()
        ocr_result = await payment_ocr_service.process_payment_receipt(
            file_path,
            expected_amount=payment['amount'],
            expected_provider=PaymentProvider(payment['provider'])
        )

        if not ocr_result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OCR processing failed: {ocr_result['error']}"
            )

        # Update payment status if OCR is successful
        if ocr_result['validation']['is_valid']:
            await mobile_money_service.update_payment_status(
                payment_id=payment_id,
                status=PaymentStatus.PROCESSING,
                validation_data=ocr_result
            )

            # Track status change
            tracking_service = get_payment_tracking_service()
            await tracking_service.track_payment_status_change(
                payment_id=payment_id,
                old_status=PaymentStatus.PENDING,
                new_status=PaymentStatus.PROCESSING,
                changed_by=current_user['user_id'],
                notes=f"Receipt uploaded and processed with OCR confidence: {ocr_result['overall_confidence']}"
            )

            return JSONResponse({
                "success": True,
                "payment_id": payment_id,
                "ocr_result": ocr_result,
                "status": "processing",
                "message": "Receipt processed successfully. Payment is now under validation."
            })
        else:
            # OCR failed validation, return errors
            return JSONResponse({
                "success": False,
                "payment_id": payment_id,
                "ocr_result": ocr_result,
                "status": "pending",
                "validation_errors": ocr_result['validation']['errors'],
                "message": "Receipt validation failed. Please check the receipt and try again."
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload payment receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process receipt"
        )

@router.get("/{payment_id}/status")
async def get_payment_status(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get payment status and details.

    Args:
        payment_id: Payment ID
        current_user: Authenticated user

    Returns:
        Dict: Payment status and details
    """
    try:
        mobile_money_service = get_mobile_money_service()
        payment = await mobile_money_service.get_payment_by_reference(payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Check access permissions
        if (payment['user_id'] != current_user['user_id'] and
            current_user['role'] not in ['super_admin', 'tresorier', 'tresorier_adjoint', 'secretaire_cure', 'secretaire_bureau']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get payment timeline
        tracking_service = get_payment_tracking_service()
        timeline = await tracking_service.get_payment_timeline(payment_id)

        # Get provider information
        provider_info = mobile_money_service.get_provider_info(PaymentProvider(payment['provider']))

        return JSONResponse({
            "success": True,
            "payment": {
                "payment_id": payment['payment_id'],
                "payment_reference": payment['payment_reference'],
                "enrollment_id": payment['enrollment_id'],
                "provider": payment['provider'],
                "provider_info": provider_info,
                "amount": float(payment['amount']),
                "currency": payment['currency'],
                "phone_number": payment['phone_number'],
                "status": payment['status'],
                "created_at": payment['created_at'],
                "updated_at": payment['updated_at'],
                "expires_at": payment['expires_at']
            },
            "timeline": timeline,
            "status_description": {
                "pending": "En attente de paiement",
                "processing": "En cours de validation",
                "validated": "Paiement validé",
                "rejected": "Paiement rejeté",
                "expired": "Paiement expiré"
            }.get(payment['status'], "Statut inconnu")
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment status"
        )

@router.get("/queue")
async def get_validation_queue(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(require_permission("payment_validation"))
):
    """
    Get treasurer validation queue.

    Args:
        status: Filter by validation status
        limit: Maximum number of items
        offset: Offset for pagination
        current_user: Authenticated treasurer

    Returns:
        Dict: Validation queue
    """
    try:
        treasurer_service = get_treasurer_validation_service()

        # Convert string status to enum if provided
        validation_status = None
        if status:
            from ...services.treasurer_validation_service import ValidationStatus
            try:
                validation_status = ValidationStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )

        queue = await treasurer_service.get_validation_queue(
            treasurer_id=current_user['user_id'],
            status=validation_status,
            limit=limit,
            offset=offset
        )

        return JSONResponse({
            "success": True,
            "queue": queue,
            "treasurer": {
                "user_id": current_user['user_id'],
                "name": f"{current_user['prenom']} {current_user['nom']}",
                "role": current_user['role']
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get validation queue"
        )

@router.post("/validations/{validation_id}/process")
async def process_payment_validation(
    validation_id: str,
    action: ValidationAction,
    notes: Optional[str] = None,
    current_user: dict = Depends(require_permission("payment_validation"))
):
    """
    Process treasurer validation action.

    Args:
        validation_id: Validation record ID
        action: Validation action
        notes: Validation notes
        current_user: Authenticated treasurer

    Returns:
        Dict: Validation processing result
    """
    try:
        treasurer_service = get_treasurer_validation_service()

        result = await treasurer_service.validate_payment(
            validation_id=validation_id,
            treasurer_id=current_user['user_id'],
            action=action,
            notes=notes
        )

        if result['success']:
            return JSONResponse({
                "success": True,
                "validation_result": result,
                "processed_by": {
                    "user_id": current_user['user_id'],
                    "name": f"{current_user['prenom']} {current_user['nom']}"
                }
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Validation processing failed')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process payment validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process validation"
        )

@router.post("/validations/{validation_id}/process-receipt")
async def process_validation_receipt(
    validation_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("payment_validation"))
):
    """
    Process receipt with OCR for validation.

    Args:
        validation_id: Validation record ID
        file: Receipt image file
        current_user: Authenticated treasurer

    Returns:
        Dict: OCR processing result
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )

        # Read file content
        file_content = await file.read()

        # Save uploaded file
        import os
        upload_dir = "uploads/validation_receipts"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = f"{upload_dir}/{validation_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Process with treasurer service
        treasurer_service = get_treasurer_validation_service()
        result = await treasurer_service.process_receipt_with_ocr(
            validation_id=validation_id,
            treasurer_id=current_user['user_id'],
            receipt_image_path=file_path
        )

        if result['success']:
            return JSONResponse({
                "success": True,
                "ocr_result": result['ocr_result'],
                "validation_id": validation_id,
                "processed_by": {
                    "user_id": current_user['user_id'],
                    "name": f"{current_user['prenom']} {current_user['nom']}"
                }
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'OCR processing failed')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process validation receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process receipt"
        )

@router.get("/validations/{validation_id}/details")
async def get_validation_details(
    validation_id: str,
    current_user: dict = Depends(require_permission("payment_validation"))
):
    """
    Get detailed validation information.

    Args:
        validation_id: Validation record ID
        current_user: Authenticated treasurer

    Returns:
        Dict: Validation details
    """
    try:
        treasurer_service = get_treasurer_validation_service()
        details = await treasurer_service.get_validation_details(
            validation_id=validation_id,
            treasurer_id=current_user['user_id']
        )

        if 'error' in details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=details['error']
            )

        return JSONResponse({
            "success": True,
            "validation_details": details
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get validation details"
        )

@router.get("/statistics")
async def get_payment_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: dict = Depends(require_permission("view_reports"))
):
    """
    Get payment statistics and analytics.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        provider: Filter by provider
        current_user: Authenticated user with reporting permissions

    Returns:
        Dict: Payment statistics
    """
    try:
        from datetime import datetime

        # Parse dates
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        end_dt = end_dt.replace(hour=23, minute=59, second=59)  # End of day

        tracking_service = get_payment_tracking_service()
        report = await tracking_service.generate_payment_report(
            start_date=start_dt,
            end_date=end_dt,
            provider=provider
        )

        if 'error' in report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=report['error']
            )

        # Calculate validation rate
        total_payments = report['summary']['total_payments']
        validated_payments = report['summary']['validated_payments']
        validation_rate = (validated_payments / total_payments * 100) if total_payments > 0 else 0
        report['summary']['validation_rate'] = round(validation_rate, 1)

        return JSONResponse({
            "success": True,
            "report": report,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "provider": provider
            },
            "generated_by": {
                "user_id": current_user['user_id'],
                "name": f"{current_user['prenom']} {current_user['nom']}",
                "role": current_user['role']
            }
        })

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment statistics"
        )

@router.get("/my-payments")
async def get_user_payments(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all payments for the current user.

    Args:
        current_user: Authenticated user

    Returns:
        Dict: User payments
    """
    try:
        mobile_money_service = get_mobile_money_service()
        payments = await mobile_money_service.get_user_payments(current_user['user_id'])

        return JSONResponse({
            "success": True,
            "payments": payments,
            "total_count": len(payments),
            "user": {
                "user_id": current_user['user_id'],
                "name": f"{current_user['prenom']} {current_user['nom']}"
            }
        })

    except Exception as e:
        logger.error(f"Failed to get user payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user payments"
        )

@router.get("/providers")
async def get_payment_providers():
    """
    Get list of available payment providers.

    Returns:
        Dict: Available providers
    """
    try:
        mobile_money_service = get_mobile_money_service()
        providers = mobile_money_service.get_available_providers()

        return JSONResponse({
            "success": True,
            "providers": providers,
            "enrollment_fee": {
                "amount": "5000.00",
                "currency": "XOF",
                "description": "Fixed enrollment fee"
            }
        })

    except Exception as e:
        logger.error(f"Failed to get payment providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment providers"
        )