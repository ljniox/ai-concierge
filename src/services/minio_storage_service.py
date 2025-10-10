"""
MinIO File Storage Service for AI Concierge
Handles file upload, download, and management for WhatsApp media attachments
"""

import os
import uuid
import json
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import structlog
import requests
from io import BytesIO

load_dotenv()

logger = structlog.get_logger()

class MinIOStorageService:
    """Service for managing file storage with MinIO (via S3 API)"""

    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'http://localhost:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket_name = os.getenv('MINIO_BUCKET_NAME', 'ai-concierge')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

        # Initialize S3 client with MinIO compatibility
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='us-east-1',
            config=Config(signature_version='s3v4')
        )

        # Ensure bucket exists
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            # Check if bucket exists
            response = self.client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]

            if self.bucket_name not in buckets:
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info("bucket_created", bucket=self.bucket_name)
                # Set bucket policy for public read access
                self._set_public_read_policy()
            else:
                logger.info("bucket_exists", bucket=self.bucket_name)
        except ClientError as e:
            logger.error("bucket_creation_failed", bucket=self.bucket_name, error=str(e))
            raise

    def _set_public_read_policy(self):
        """Set bucket policy for public read access"""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                }
            ]
        }
        try:
            self.client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(policy)
            )
            logger.info("public_policy_set", bucket=self.bucket_name)
        except ClientError as e:
            logger.warning("public_policy_failed", bucket=self.bucket_name, error=str(e))

    def upload_file_from_url(self, url: str, original_filename: str = None,
                           content_type: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Download file from URL and upload to MinIO"""
        try:
            # Download file from URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            file_data = response.content
            file_size = len(file_data)

            # Determine content type
            if content_type:
                mime_type = content_type
            else:
                mime_type = response.headers.get('content-type', 'application/octet-stream')

            # Generate filename
            if not original_filename:
                original_filename = f"file_{uuid.uuid4()}"

            # Clean filename and add timestamp
            clean_filename = self._sanitize_filename(original_filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"{timestamp}_{clean_filename}"

            # Determine folder structure by file type
            file_category = self._get_file_category(mime_type)
            full_object_name = f"{file_category}/{object_name}"

            # Prepare metadata
            obj_metadata = {
                'original-url': url,
                'original-filename': original_filename,
                'content-type': mime_type,
                'file-size': str(file_size),
                'upload-timestamp': datetime.now().isoformat(),
                'category': file_category
            }

            if metadata:
                obj_metadata.update(metadata)

            # Upload to MinIO/S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=full_object_name,
                Body=BytesIO(file_data),
                ContentType=mime_type,
                Metadata=obj_metadata
            )

            # Generate public URL
            public_url = self.get_public_url(full_object_name)

            result = {
                'object_name': full_object_name,
                'public_url': public_url,
                'original_filename': original_filename,
                'content_type': mime_type,
                'file_size': file_size,
                'category': file_category,
                'metadata': obj_metadata,
                'uploaded_at': datetime.now().isoformat()
            }

            logger.info("file_uploaded_from_url",
                       object_name=full_object_name,
                       size=file_size,
                       category=file_category)

            return result

        except Exception as e:
            logger.error("file_upload_from_url_failed", url=url, error=str(e))
            raise

    def upload_file_data(self, file_data: bytes, filename: str,
                        content_type: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload file data directly to MinIO"""
        try:
            file_size = len(file_data)

            # Determine content type
            if content_type:
                mime_type = content_type
            else:
                mime_type, _ = mimetypes.guess_type(filename)
                if not mime_type:
                    mime_type = 'application/octet-stream'

            # Clean filename and add timestamp
            clean_filename = self._sanitize_filename(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"{timestamp}_{clean_filename}"

            # Determine folder structure by file type
            file_category = self._get_file_category(mime_type)
            full_object_name = f"{file_category}/{object_name}"

            # Prepare metadata
            obj_metadata = {
                'original-filename': filename,
                'content-type': mime_type,
                'file-size': str(file_size),
                'upload-timestamp': datetime.now().isoformat(),
                'category': file_category
            }

            if metadata:
                obj_metadata.update(metadata)

            # Upload to MinIO/S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=full_object_name,
                Body=BytesIO(file_data),
                ContentType=mime_type,
                Metadata=obj_metadata
            )

            # Generate public URL
            public_url = self.get_public_url(full_object_name)

            result = {
                'object_name': full_object_name,
                'public_url': public_url,
                'original_filename': filename,
                'content_type': mime_type,
                'file_size': file_size,
                'category': file_category,
                'metadata': obj_metadata,
                'uploaded_at': datetime.now().isoformat()
            }

            logger.info("file_uploaded",
                       object_name=full_object_name,
                       size=file_size,
                       category=file_category)

            return result

        except Exception as e:
            logger.error("file_upload_failed", filename=filename, error=str(e))
            raise

    def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Get file information from MinIO"""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=object_name)

            return {
                'object_name': object_name,
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'].isoformat(),
                'metadata': response.get('Metadata', {}),
                'public_url': self.get_public_url(object_name)
            }
        except ClientError as e:
            logger.error("file_info_failed", object_name=object_name, error=str(e))
            return None

    def get_public_url(self, object_name: str) -> str:
        """Generate public URL for object"""
        if self.secure:
            return f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{object_name}"
        else:
            return f"http://{self.bucket_name}.{self.endpoint.replace('http://', '')}/{object_name}"

    def list_files(self, prefix: str = None, category: str = None) -> List[Dict[str, Any]]:
        """List files in bucket, optionally filtered by prefix or category"""
        try:
            if category:
                prefix = f"{category}/"

            # Build list_objects_v2 parameters, only include Prefix if not None
            list_params = {'Bucket': self.bucket_name}
            if prefix is not None:
                list_params['Prefix'] = prefix

            response = self.client.list_objects_v2(**list_params)
            files = []

            for obj in response.get('Contents', []):
                file_info = {
                    'object_name': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'],
                    'public_url': self.get_public_url(obj['Key'])
                }
                files.append(file_info)

            return files

        except ClientError as e:
            logger.error("list_files_failed", error=str(e))
            return []

    def delete_file(self, object_name: str) -> bool:
        """Delete file from MinIO"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info("file_deleted", object_name=object_name)
            return True
        except ClientError as e:
            logger.error("file_delete_failed", object_name=object_name, error=str(e))
            return False

    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0

            response = self.client.list_objects_v2(Bucket=self.bucket_name)

            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    try:
                        self.client.delete_object(Bucket=self.bucket_name, Key=obj['Key'])
                        deleted_count += 1
                        logger.info("old_file_deleted", object_name=obj['Key'], age_days=days_old)
                    except ClientError:
                        continue

            logger.info("cleanup_completed", deleted_count=deleted_count, days_old=days_old)
            return deleted_count

        except Exception as e:
            logger.error("cleanup_failed", error=str(e))
            return 0

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path traversal attempts
        filename = filename.replace('../', '').replace('..\\', '')

        # Replace problematic characters
        filename = ''.join(c for c in filename if c.isalnum() or c in '._- ')

        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:100-len(ext)] + ext

        return filename or 'file'

    def _get_file_category(self, mime_type: str) -> str:
        """Determine file category based on MIME type"""
        if mime_type.startswith('image/'):
            return 'images'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('application/pdf'):
            return 'documents'
        elif mime_type.startswith('application/') and 'document' in mime_type.lower():
            return 'documents'
        elif mime_type.startswith('text/'):
            return 'documents'
        else:
            return 'other'

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            category_stats = {}

            response = self.client.list_objects_v2(Bucket=self.bucket_name)

            for obj in response.get('Contents', []):
                total_size += obj['Size']
                file_count += 1

                # Categorize by object name prefix
                category = obj['Key'].split('/')[0]
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'size': 0}

                category_stats[category]['count'] += 1
                category_stats[category]['size'] += obj['Size']

            return {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'category_stats': category_stats,
                'bucket_name': self.bucket_name,
                'endpoint': self.endpoint
            }

        except Exception as e:
            logger.error("storage_stats_failed", error=str(e))
            return {}

# Global instance
minio_storage = MinIOStorageService()

def get_minio_storage():
    """Get MinIO storage service instance"""
    return minio_storage

if __name__ == "__main__":
    # Test the MinIO service
    print("🗄️ Testing MinIO Storage Service...")

    try:
        storage = get_minio_storage()

        # Test storage stats
        stats = storage.get_storage_stats()
        print(f"📊 Storage stats: {stats}")

        # Test file upload from URL
        test_url = "https://httpbin.org/image/png"
        result = storage.upload_file_from_url(
            url=test_url,
            original_filename="test_image.png",
            metadata={"test": "true", "source": "test_script"}
        )

        print(f"✅ File uploaded: {result['public_url']}")

        # Test file info
        file_info = storage.get_file_info(result['object_name'])
        print(f"📋 File info: {file_info}")

        # List files
        files = storage.list_files()
        print(f"📂 Total files: {len(files)}")

        print("\n✅ MinIO storage test completed!")

    except Exception as e:
        print(f"❌ MinIO test failed: {e}")