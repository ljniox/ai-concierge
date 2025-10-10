"""
API endpoints for temporary pages and receipts management
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import uuid
from datetime import datetime

from src.services.temporary_pages_service import TemporaryPagesService, get_temp_pages_service
from src.utils.config import get_settings

router = APIRouter(prefix="/api/v1/temporary-pages", tags=["temporary-pages"])

# Pydantic models for request/response
class CreateTemporaryPageRequest(BaseModel):
    title: str
    content: Dict[str, Any]
    content_type: str = "report"
    created_by: str = "system"
    expires_in_hours: int = 24
    max_access_count: Optional[int] = None
    allowed_actions: List[str] = ["read", "print"]

class CreateReceiptRequest(BaseModel):
    title: str
    content: Dict[str, Any]
    receipt_type: str = "payment"
    reference_id: Optional[str] = None
    amount: float = 0.0
    created_by: str = "system"

class PageResponse(BaseModel):
    success: bool
    message: str
    access_code: Optional[str] = None
    receipt_code: Optional[str] = None
    shareable_link: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# Initialize service
service = get_temp_pages_service()

@router.post("/create", response_model=PageResponse)
async def create_temporary_page(request: CreateTemporaryPageRequest):
    """Create a new temporary page with UUID access code"""
    try:
        access_code = service.create_temporary_page(
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            created_by=request.created_by,
            expires_in_hours=request.expires_in_hours,
            max_access_count=request.max_access_count,
            allowed_actions=request.allowed_actions
        )

        if not access_code:
            raise HTTPException(status_code=500, detail="Failed to create temporary page")

        settings = get_settings()
        shareable_link = f"{settings.external_base_url}/view/{access_code}"

        return PageResponse(
            success=True,
            message="Temporary page created successfully",
            access_code=access_code,
            shareable_link=shareable_link
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating temporary page: {str(e)}")

@router.post("/receipts/create", response_model=PageResponse)
async def create_receipt(request: CreateReceiptRequest):
    """Create a new permanent receipt with UUID code"""
    try:
        receipt_code = service.create_receipt(
            title=request.title,
            content=request.content,
            receipt_type=request.receipt_type,
            reference_id=request.reference_id,
            amount=request.amount,
            created_by=request.created_by
        )

        if not receipt_code:
            raise HTTPException(status_code=500, detail="Failed to create receipt")

        settings = get_settings()
        shareable_link = f"{settings.external_base_url}/receipt/{receipt_code}"

        return PageResponse(
            success=True,
            message="Receipt created successfully",
            receipt_code=receipt_code,
            shareable_link=shareable_link
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating receipt: {str(e)}")

@router.get("/view/{access_code}", response_model=PageResponse)
async def get_temporary_page(access_code: str, request: Request):
    """Get temporary page by access code"""
    try:
        # Validate UUID format
        try:
            uuid.UUID(str(access_code))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid access code format")

        page = service.get_temporary_page(access_code)

        if not page:
            raise HTTPException(status_code=404, detail="Page not found, expired, or access limit reached")

        # Log access with IP address
        client_ip = request.client.host if request.client else None
        service._log_access(page["id"], "temporary", access_code, "view")

        return PageResponse(
            success=True,
            message="Page retrieved successfully",
            data={
                "title": page["title"],
                "content": page["content"],
                "content_type": page["content_type"],
                "created_by": page["created_by"],
                "created_at": page["created_at"],
                "expires_at": page["expires_at"],
                "access_count": page["access_count"],
                "max_access_count": page["max_access_count"],
                "allowed_actions": page["allowed_actions"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving page: {str(e)}")

@router.get("/receipt/{receipt_code}", response_model=PageResponse)
async def get_receipt(receipt_code: str, request: Request):
    """Get receipt by code"""
    try:
        # Validate UUID format
        try:
            uuid.UUID(str(receipt_code))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid receipt code format")

        receipt = service.get_receipt(receipt_code)

        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        # Log access with IP address
        client_ip = request.client.host if request.client else None
        service._log_access(receipt["id"], "receipt", receipt_code, "view")

        return PageResponse(
            success=True,
            message="Receipt retrieved successfully",
            data={
                "title": receipt["title"],
                "content": receipt["content"],
                "receipt_type": receipt["receipt_type"],
                "reference_id": receipt["reference_id"],
                "amount": receipt["amount"],
                "created_by": receipt["created_by"],
                "created_at": receipt["created_at"],
                "access_count": receipt["access_count"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving receipt: {str(e)}")

@router.delete("/{access_code}")
async def deactivate_temporary_page(access_code: str):
    """Deactivate a temporary page"""
    try:
        success = service.deactivate_page(access_code)

        if not success:
            raise HTTPException(status_code=404, detail="Page not found")

        return {"success": True, "message": "Page deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating page: {str(e)}")

@router.post("/cleanup")
async def cleanup_expired_pages():
    """Clean up expired temporary pages"""
    try:
        deleted_count = service.cleanup_expired_pages()

        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} expired pages",
            "deleted_count": deleted_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up pages: {str(e)}")

@router.get("/statistics")
async def get_statistics():
    """Get system statistics"""
    try:
        stats = service.get_statistics()

        return {
            "success": True,
            "statistics": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.get("/logs/{page_id}")
async def get_page_access_logs(page_id: str):
    """Get access logs for a specific page"""
    try:
        # Validate UUID format
        try:
            uuid.UUID(str(page_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid page ID format")

        logs = service.get_page_access_logs(page_id)

        return {
            "success": True,
            "logs": logs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting access logs: {str(e)}")

# Web interface endpoints
@router.get("/view/{access_code}/web", response_class=HTMLResponse)
async def view_temporary_page_web(access_code: str, request: Request):
    """Web interface for viewing temporary pages"""
    try:
        page = service.get_temporary_page(access_code)

        if not page:
            return HTMLResponse(
                content="""
                <html>
                    <head><title>Page Not Found</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1>Page Not Found</h1>
                        <p>This page may have expired, reached its access limit, or never existed.</p>
                    </body>
                </html>
                """,
                status_code=404
            )

        # Generate HTML content based on content type
        html_content = generate_page_html(page)

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>Error Loading Page</h1>
                    <p>An error occurred while loading this page.</p>
                </body>
            </html>
            """,
            status_code=500
        )

@router.get("/receipt/{receipt_code}/web", response_class=HTMLResponse)
async def view_receipt_web(receipt_code: str, request: Request):
    """Web interface for viewing receipts"""
    try:
        receipt = service.get_receipt(receipt_code)

        if not receipt:
            return HTMLResponse(
                content="""
                <html>
                    <head><title>Receipt Not Found</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1>Receipt Not Found</h1>
                        <p>This receipt may not exist or may have been deactivated.</p>
                    </body>
                </html>
                """,
                status_code=404
            )

        # Generate HTML content for receipt
        html_content = generate_receipt_html(receipt)

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>Error Loading Receipt</h1>
                    <p>An error occurred while loading this receipt.</p>
                </body>
            </html>
            """,
            status_code=500
        )

def generate_page_html(page: Dict[str, Any]) -> str:
    """Generate HTML content for a temporary page"""
    content = page["content"]
    content_type = page.get("content_type", "report")

    if content_type == "student_report":
        return generate_student_report_html(content, page)
    elif content_type == "general":
        return generate_general_report_html(content, page)
    else:
        return generate_general_report_html(content, page)

def generate_student_report_html(content: Dict[str, Any], page: Dict[str, Any]) -> str:
    """Generate HTML for student report"""
    return f"""
    <html>
        <head>
            <title>{page['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{page['title']}</h1>
                <p>Generated: {datetime.fromisoformat(page['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Expires: {datetime.fromisoformat(page['expires_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="content">
                <h2>Student Information</h2>
                <p><strong>Name:</strong> {content.get('student_name', 'N/A')}</p>
                <p><strong>Class:</strong> {content.get('class', 'N/A')}</p>

                <h3>Grades</h3>
                <table>
                    <tr><th>Subject</th><th>Grade</th></tr>
                    {''.join([f'<tr><td>Term {i+1}</td><td>{grade}</td></tr>' for i, grade in enumerate(content.get('grades', []))])}
                </table>

                {f'<p><strong>Comments:</strong> {content.get("comments", "")}</p>' if content.get('comments') else ''}
            </div>

            <div class="footer">
                <p>This is a temporary page for viewing purposes only.</p>
                <p>Access count: {page['access_count']}</p>
                <p>UUID: {page['access_code']}</p>
            </div>

            <script>
                // Print functionality
                function printPage() {{
                    window.print();
                }}
            </script>

            <div style="margin-top: 20px;">
                <button onclick="printPage()" style="padding: 10px 20px; background-color: #007cba; color: white; border: none; border-radius: 5px; cursor: pointer;">Print</button>
            </div>
        </body>
    </html>
    """

def generate_general_report_html(content: Dict[str, Any], page: Dict[str, Any]) -> str:
    """Generate HTML for general reports"""
    return f"""
    <html>
        <head>
            <title>{page['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
                pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{page['title']}</h1>
                <p>Generated: {datetime.fromisoformat(page['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Expires: {datetime.fromisoformat(page['expires_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="content">
                <pre>{json.dumps(content, indent=2, ensure_ascii=False)}</pre>
            </div>

            <div class="footer">
                <p>This is a temporary page for viewing purposes only.</p>
                <p>Access count: {page['access_count']}</p>
                <p>UUID: {page['access_code']}</p>
            </div>

            <script>
                function printPage() {{
                    window.print();
                }}
            </script>

            <div style="margin-top: 20px;">
                <button onclick="printPage()" style="padding: 10px 20px; background-color: #007cba; color: white; border: none; border-radius: 5px; cursor: pointer;">Print</button>
            </div>
        </body>
    </html>
    """

def generate_receipt_html(receipt: Dict[str, Any]) -> str:
    """Generate HTML for receipts"""
    content = receipt["content"]

    return f"""
    <html>
        <head>
            <title>{receipt['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
                .receipt-info {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .amount {{ font-size: 18px; font-weight: bold; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{receipt['title']}</h1>
                <p>Receipt Code: {receipt['receipt_code']}</p>
                <p>Generated: {datetime.fromisoformat(receipt['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="content">
                <div class="receipt-info">
                    <h2>Payment Details</h2>
                    <p><strong>Student:</strong> {content.get('student_name', 'N/A')}</p>
                    <p><strong>Reference ID:</strong> {receipt.get('reference_id', 'N/A')}</p>
                    <p><strong>Payment Method:</strong> {content.get('payment_method', 'N/A')}</p>
                    <p><strong>Payment Date:</strong> {content.get('payment_date', 'N/A')}</p>
                    <p class="amount">Amount: {receipt['amount']:,} FCFA</p>
                </div>

                {f'<p><strong>Additional Information:</strong> {content.get("additional_info", "")}</p>' if content.get('additional_info') else ''}
            </div>

            <div class="footer">
                <p>This is an official receipt. Please keep for your records.</p>
                <p>Access count: {receipt['access_count']}</p>
                <p>Receipt Code: {receipt['receipt_code']}</p>
            </div>

            <script>
                function printPage() {{
                    window.print();
                }}
            </script>

            <div style="margin-top: 20px;">
                <button onclick="printPage()" style="padding: 10px 20px; background-color: #2e7d32; color: white; border: none; border-radius: 5px; cursor: pointer;">Print Receipt</button>
            </div>
        </body>
    </html>
    """

# Create a separate router for view endpoints without API prefix
view_router = APIRouter(prefix="", tags=["temporary-pages-views"])

@view_router.get("/view/{access_code}", response_class=HTMLResponse)
async def view_temporary_page_public(access_code: str, request: Request):
    """Public web interface for viewing temporary pages"""
    return await view_temporary_page_web(access_code, request)

@view_router.get("/receipt/{receipt_code}", response_class=HTMLResponse)
async def view_receipt_public(receipt_code: str, request: Request):
    """Public web interface for viewing receipts"""
    return await view_receipt_web(receipt_code, request)