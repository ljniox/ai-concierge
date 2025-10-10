"""
File Management API for AI Concierge
Handles file upload, download, and management operations with MinIO
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from src.services.minio_storage_service import get_minio_storage
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Upload file to MinIO storage

    Args:
        file: File to upload
        category: Optional category (images, documents, audio, video)
        metadata: Optional JSON metadata string

    Returns:
        Upload result with file information
    """
    try:
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            import json
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")

        # Read file data
        file_data = await file.read()

        # Get MinIO storage service
        minio_storage = get_minio_storage()

        # Upload file
        result = minio_storage.upload_file_data(
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
            metadata=parsed_metadata
        )

        logger.info("file_uploaded_api",
                   filename=file.filename,
                   size=result['file_size'],
                   category=result['category'])

        return {
            "status": "success",
            "message": "File uploaded successfully",
            "file_info": result
        }

    except Exception as e:
        logger.error("file_upload_failed", filename=file.filename if file else "unknown", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload-from-url")
async def upload_from_url(
    url: str = Form(...),
    filename: Optional[str] = Form(None),
    content_type: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Upload file from URL to MinIO storage

    Args:
        url: URL to download file from
        filename: Optional filename for the stored file
        content_type: Optional content type
        metadata: Optional JSON metadata string

    Returns:
        Upload result with file information
    """
    try:
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            import json
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")

        # Get MinIO storage service
        minio_storage = get_minio_storage()

        # Upload from URL
        result = minio_storage.upload_file_from_url(
            url=url,
            original_filename=filename,
            content_type=content_type,
            metadata=parsed_metadata
        )

        logger.info("file_uploaded_from_url_api",
                   url=url,
                   size=result['file_size'],
                   category=result['category'])

        return {
            "status": "success",
            "message": "File uploaded from URL successfully",
            "file_info": result
        }

    except Exception as e:
        logger.error("file_upload_from_url_failed", url=url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload from URL failed: {str(e)}")

@router.get("/info/{object_name}")
async def get_file_info(object_name: str) -> Dict[str, Any]:
    """
    Get file information from MinIO

    Args:
        object_name: Object name in MinIO

    Returns:
        File information
    """
    try:
        minio_storage = get_minio_storage()
        file_info = minio_storage.get_file_info(object_name)

        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "status": "success",
            "file_info": file_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("file_info_failed", object_name=object_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")

@router.get("/list")
async def list_files(
    category: Optional[str] = Query(None, description="Filter by category (images, documents, audio, video)"),
    prefix: Optional[str] = Query(None, description="Filter by prefix")
) -> Dict[str, Any]:
    """
    List files in MinIO storage

    Args:
        category: Optional category filter
        prefix: Optional prefix filter

    Returns:
        List of files
    """
    try:
        minio_storage = get_minio_storage()
        files = minio_storage.list_files(category=category, prefix=prefix)

        return {
            "status": "success",
            "files": files,
            "total_count": len(files)
        }

    except Exception as e:
        logger.error("list_files_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/{object_name}")
async def delete_file(object_name: str) -> Dict[str, Any]:
    """
    Delete file from MinIO storage

    Args:
        object_name: Object name to delete

    Returns:
        Deletion result
    """
    try:
        minio_storage = get_minio_storage()
        success = minio_storage.delete_file(object_name)

        if not success:
            raise HTTPException(status_code=404, detail="File not found or deletion failed")

        logger.info("file_deleted_api", object_name=object_name)

        return {
            "status": "success",
            "message": "File deleted successfully",
            "object_name": object_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("file_delete_failed", object_name=object_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/stats")
async def get_storage_stats() -> Dict[str, Any]:
    """
    Get storage statistics

    Returns:
        Storage statistics
    """
    try:
        minio_storage = get_minio_storage()
        stats = minio_storage.get_storage_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        logger.error("storage_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_files(
    days_old: int = Query(30, description="Delete files older than this many days")
) -> Dict[str, Any]:
    """
    Clean up old files from storage

    Args:
        days_old: Delete files older than this many days

    Returns:
        Cleanup result
    """
    try:
        minio_storage = get_minio_storage()
        deleted_count = minio_storage.cleanup_old_files(days_old=days_old)

        logger.info("cleanup_completed_api", deleted_count=deleted_count, days_old=days_old)

        return {
            "status": "success",
            "message": f"Cleanup completed",
            "deleted_count": deleted_count,
            "days_old": days_old
        }

    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/categories")
async def get_file_categories() -> Dict[str, Any]:
    """
    Get available file categories and their descriptions

    Returns:
        File categories information
    """
    try:
        categories = {
            "images": {
                "description": "Image files (JPG, PNG, GIF, etc.)",
                "mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp"],
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp"]
            },
            "documents": {
                "description": "Document files (PDF, Word, etc.)",
                "mime_types": ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                "extensions": [".pdf", ".doc", ".docx"]
            },
            "audio": {
                "description": "Audio files (MP3, WAV, etc.)",
                "mime_types": ["audio/mpeg", "audio/wav", "audio/ogg"],
                "extensions": [".mp3", ".wav", ".ogg"]
            },
            "video": {
                "description": "Video files (MP4, AVI, etc.)",
                "mime_types": ["video/mp4", "video/avi", "video/quicktime"],
                "extensions": [".mp4", ".avi", ".mov"]
            },
            "other": {
                "description": "Other file types",
                "mime_types": ["application/octet-stream"],
                "extensions": []
            }
        }

        return {
            "status": "success",
            "categories": categories
        }

    except Exception as e:
        logger.error("categories_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/health")
async def file_management_health() -> Dict[str, Any]:
    """
    Health check for file management service

    Returns:
        Health status
    """
    try:
        minio_storage = get_minio_storage()
        stats = minio_storage.get_storage_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "minio_endpoint": minio_storage.endpoint,
            "bucket_name": minio_storage.bucket_name,
            "bucket_accessible": "total_files" in stats,
            "total_files": stats.get("total_files", 0)
        }

    except Exception as e:
        logger.error("file_management_health_failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }