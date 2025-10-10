# Temporary Pages System Setup Instructions

## Database Setup

The SQL file `temporary_pages_system.sql` needs to be executed in your Supabase dashboard SQL Editor.

### Steps:
1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project: `ixzpejqzxvxpnkbznqnj`
3. Go to SQL Editor in the left sidebar
4. Click "New query"
5. Copy the contents of `temporary_pages_system.sql`
6. Paste it into the SQL Editor
7. Click "Run"

### Tables that will be created:
- `temporary_pages` - For time-sensitive shareable pages
- `receipts` - For permanent payment receipts
- `page_access_logs` - For tracking access

### Functions that will be created:
- `create_temporary_page()` - Create new temporary page
- `get_temporary_page()` - Retrieve temporary page
- `create_receipt()` - Create permanent receipt
- `get_receipt()` - Retrieve receipt
- `cleanup_expired_pages()` - Clean up expired pages
- `get_page_stats()` - Get system statistics

## API Endpoints

After setup, the following endpoints will be available:

### Temporary Pages
- `POST /api/v1/temporary-pages/create` - Create temporary page
- `GET /api/v1/temporary-pages/view/{access_code}` - Get temporary page data
- `GET /api/v1/temporary-pages/view/{access_code}/web` - View temporary page in browser
- `DELETE /api/v1/temporary-pages/{access_code}` - Deactivate page

### Receipts
- `POST /api/v1/temporary-pages/receipts/create` - Create permanent receipt
- `GET /api/v1/temporary-pages/receipt/{receipt_code}` - Get receipt data
- `GET /api/v1/temporary-pages/receipt/{receipt_code}/web` - View receipt in browser

### Management
- `POST /api/v1/temporary-pages/cleanup` - Clean up expired pages
- `GET /api/v1/temporary-pages/statistics` - Get system statistics
- `GET /api/v1/temporary-pages/logs/{page_id}` - Get access logs

## Usage Examples

### Create a Student Report
```python
from src.utils.temp_pages_utils import get_temp_pages_utils

utils = get_temp_pages_utils()
access_code = utils.create_student_report_page(
    student_id="student-uuid-here",
    report_type="complete",
    expires_in_hours=24
)

# Share this link:
link = f"http://localhost:8000/api/v1/temporary-pages/view/{access_code}/web"
```

### Create a Payment Receipt
```python
from src.utils.temp_pages_utils import get_temp_pages_utils

utils = get_temp_pages_utils()
receipt_code = utils.create_payment_receipt(
    inscription_id="inscription-uuid-here",
    amount=15000,
    payment_method="Mobile Money"
)

# Share this permanent link:
link = f"http://localhost:8000/api/v1/temporary-pages/receipt/{receipt_code}/web"
```

## Testing

Run the test script to verify functionality:
```bash
python3 test_temp_pages_system.py
```

## Features

### Temporary Pages
- ✅ UUID-based access codes
- ✅ Configurable expiration time
- ✅ Access count limits
- ✅ Read-only access
- ✅ Print functionality
- ✅ Automatic cleanup
- ✅ Access logging

### Receipts
- ✅ Permanent UUID links
- ✅ Payment proof generation
- ✅ Inscription receipts
- ✅ Access tracking
- ✅ Professional HTML templates

### Security
- ✅ No write access
- ✅ Access logging
- ✅ Automatic expiration
- ✅ UUID-based security
- ✅ IP address tracking

## Integration with Existing System

The system integrates with:
- Student data from `catechumenes` table
- Class data from `classes` table
- Inscription data from `inscriptions` table
- Grade data from `notes` table

## Automatic Cleanup

The system includes a cleanup service that:
- Runs every hour
- Removes expired temporary pages
- Logs cleanup activities
- Provides statistics

## Web Interface

Each temporary page and receipt has a clean, printable web interface with:
- Professional styling
- Print functionality
- Access information
- Expiration warnings (for temporary pages)
- Permanent receipt validation