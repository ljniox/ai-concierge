# MinIO Integration Guide for AI Concierge

## 📋 Overview

This guide documents the complete MinIO S3 integration for file storage in the AI Concierge WhatsApp service. The system now supports automatic file upload, storage, and management for all media attachments received through WhatsApp.

## 🏗️ Architecture

### **Components Added**

1. **MinIO Storage Service** (`src/services/minio_storage_service.py`)
   - Handles all MinIO S3 operations
   - Automatic bucket creation and policy setup
   - File upload from URLs and direct data
   - File categorization and metadata management

2. **File Management API** (`src/api/file_management.py`)
   - RESTful API endpoints for file operations
   - Upload, download, list, delete operations
   - Storage statistics and cleanup utilities

3. **Webhook Integration** (`src/api/webhook.py`)
   - Automatic file download and storage from WhatsApp media
   - Replacement of external URLs with MinIO URLs
   - Metadata preservation and tracking

4. **WAHA Service Enhancement** (`src/services/waha_service.py`)
   - Support for local file upload to MinIO
   - Automatic URL replacement for outgoing media
   - Fallback to original URLs if MinIO fails

## 🔧 Configuration

### **Environment Variables**

```bash
# MinIO Settings
MINIO_ENDPOINT=https://minio.setu.ovh:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=MinIO@JSS2024!SecurePass
MINIO_BUCKET_NAME=ai-concierge
MINIO_SECURE=true
```

### **Dependencies**

```bash
pip install minio
```

## 📁 File Organization

### **Automatic Categorization**

Files are automatically organized by type:

```
ai-concierge bucket/
├── images/          # Image files (JPG, PNG, GIF, WebP)
├── documents/       # Documents (PDF, Word, etc.)
├── audio/          # Audio files (MP3, WAV, OGG)
├── video/          # Video files (MP4, AVI, MOV)
└── other/          # Other file types
```

### **Naming Convention**

```
{timestamp}_{original_filename}
Example: 20250927_195308_test_image.png
```

## 🚀 Usage

### **1. Automatic File Storage (Webhook)**

When media files are received via WhatsApp:

```python
# Automatic process in webhook:
# 1. Detect media attachment
# 2. Download from WAHA URL
# 3. Upload to MinIO with metadata
# 4. Replace URL in message processing
# 5. Store file info in response
```

### **2. Manual File Upload**

```python
from src.services.minio_storage_service import get_minio_storage

storage = get_minio_storage()

# Upload from URL
result = storage.upload_file_from_url(
    url="https://example.com/file.pdf",
    original_filename="document.pdf",
    metadata={"source": "manual", "user_id": "123"}
)

# Upload file data
with open("local_file.jpg", "rb") as f:
    file_data = f.read()

result = storage.upload_file_data(
    file_data=file_data,
    filename="photo.jpg",
    content_type="image/jpeg"
)
```

### **3. File Management API**

#### **Upload File**
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -F "file=@document.pdf" \
  -F "category=documents" \
  -F 'metadata={"user_id": "123"}'
```

#### **Upload from URL**
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload-from-url" \
  -F "url=https://example.com/image.png" \
  -F "filename=screenshot.png" \
  -F "content_type=image/png"
```

#### **List Files**
```bash
curl "http://localhost:8000/api/v1/files/list?category=images"
```

#### **Get File Info**
```bash
curl "http://localhost:8000/api/v1/files/info/images/20250927_195308_test.png"
```

#### **Delete File**
```bash
curl -X DELETE "http://localhost:8000/api/v1/files/images/20250927_195308_test.png"
```

#### **Storage Statistics**
```bash
curl "http://localhost:8000/api/v1/files/stats"
```

## 🔍 Features

### **Automatic File Processing**

- **URL Download**: Automatic download of media from WhatsApp servers
- **Type Detection**: MIME type-based categorization
- **Metadata Preservation**: Original filename, message ID, phone number
- **Public URLs**: Generated accessible URLs for media sharing
- **Error Handling**: Graceful fallback to original URLs

### **Storage Management**

- **Bucket Policy**: Automatic public read access configuration
- **Cleanup Service**: Automatic old file cleanup (configurable)
- **Storage Stats**: Real-time storage usage statistics
- **File Listing**: Category-based file browsing

### **Security Features**

- **Access Control**: Configurable bucket policies
- **Metadata Security**: Sensitive data protection
- **URL Validation**: Secure file access patterns
- **Error Logging**: Comprehensive audit trail

## 📊 API Endpoints

### **File Management**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/files/upload` | Upload file directly |
| POST | `/api/v1/files/upload-from-url` | Upload file from URL |
| GET | `/api/v1/files/info/{object_name}` | Get file information |
| GET | `/api/v1/files/list` | List files with filters |
| DELETE | `/api/v1/files/{object_name}` | Delete file |
| GET | `/api/v1/files/stats` | Get storage statistics |
| POST | `/api/v1/files/cleanup` | Clean up old files |
| GET | `/api/v1/files/categories` | Get file categories |
| GET | `/api/v1/files/health` | Health check |

### **WhatsApp Integration**

File attachments are automatically processed through:
- **Webhook**: `/api/v1/webhook`
- **Media Storage**: Automatic MinIO upload
- **URL Replacement**: MinIO URLs in message processing

## 🔧 Monitoring

### **Health Checks**

```bash
# File management health
curl "http://localhost:8000/api/v1/files/health"

# Storage statistics
curl "http://localhost:8000/api/v1/files/stats"
```

### **Logging**

All file operations are logged with structured logging:
- File uploads with size and category
- URL generation and access
- Error conditions and fallbacks
- Storage management operations

## 🚨 Troubleshooting

### **Common Issues**

**Connection Errors**
```bash
# Check MinIO connectivity
curl "https://minio.setu.ovh:9000/minio/health/live"

# Verify credentials
python3 -c "from src.services.minio_storage_service import get_minio_storage; storage = get_minio_storage(); print('Connected')"
```

**Upload Failures**
- Check network connectivity to MinIO
- Verify bucket permissions
- Ensure file size limits
- Check available disk space

**URL Generation Issues**
- Verify bucket policy configuration
- Check DNS resolution for bucket URLs
- Ensure SSL certificate validity

### **Debug Commands**

```python
# Test connection
from src.services.minio_storage_service import get_minio_storage
storage = get_minio_storage()
print(f"Endpoint: {storage.endpoint}")
print(f"Bucket: {storage.bucket_name}")

# Test upload
result = storage.upload_file_data(
    file_data=b"test content",
    filename="test.txt",
    content_type="text/plain"
)
print(f"Upload result: {result}")

# Check files
files = storage.list_files()
print(f"Total files: {len(files)}")
```

## 📈 Performance Considerations

### **Optimizations**

- **Concurrent Uploads**: Async file processing
- **Caching**: Redis integration for frequently accessed files
- **Compression**: Automatic compression for supported formats
- **CDN Integration**: Ready for CDN deployment

### **Scalability**

- **Horizontal Scaling**: Stateless file management
- **Load Balancing**: Multiple MinIO instances support
- **Storage Tiering**: Configurable storage policies
- **Backup Integration**: Automated backup procedures

## 🔮 Future Enhancements

### **Planned Features**

1. **File Processing**
   - Image resizing and optimization
   - Document preview generation
   - Video transcoding
   - File format conversion

2. **Security Enhancements**
   - Virus scanning integration
   - Content moderation
   - Access control lists
   - Encryption at rest

3. **Integration Features**
   - Email notification system
   - Social media sharing
   - API rate limiting
   - Usage analytics

4. **Management Tools**
   - Web-based file manager
   - Bulk operations
   - Scheduled maintenance
   - Performance monitoring

---

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Verify MinIO server status
- Contact system administrator

*Last Updated: September 27, 2025*