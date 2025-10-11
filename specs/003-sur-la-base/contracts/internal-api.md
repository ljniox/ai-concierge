# Internal API Contract: Account Creation Service

**Contract Version**: 1.0 | **Date**: 2025-10-11 | **Type**: Internal REST API
**Purpose**: Define internal API contracts for automatic account creation and user management

## API Overview

**Base URL**: `http://localhost:8001/api/v1/accounts`
**Authentication**: JWT tokens (internal service communication)
**Content-Type**: `application/json`
**Documentation**: OpenAPI/Swagger available at `/docs`

## Authentication

### JWT Token Structure

```json
{
  "sub": "user_id",
  "iat": 1647895200,
  "exp": 1647898800,
  "scope": ["account:read", "account:write", "role:read"],
  "user_id": 12345,
  "username": "jamesniox",
  "roles": ["parent", "system_admin"]
}
```

### Authorization Headers

```http
Authorization: Bearer <jwt_token>
X-Service-Name: messaging-service
X-Request-ID: req_123456789
```

## Endpoints

### 1. Create Account (Internal)

**Endpoint**: `POST /accounts/create`
**Purpose**: Create new user account from phone number validation
**Authentication**: Service-to-service token

#### Request Schema

```json
{
  "phone_number": "+2214476978781",
  "country_code": "+221",
  "national_number": "4476978781",
  "source": "telegram",
  "platform_user_id": "695065578",
  "contact_name": "James Niox",
  "parent_match": {
    "found": true,
    "parent_id": 12345,
    "parent_code": "PARENT001",
    "parent_name": "James Niox"
  },
  "consent_given": true,
  "consent_date": "2025-10-11T12:34:56Z"
}
```

#### Response Schema (201 Created)

```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "account_id": 98765,
    "phone_number": "+2214476978781",
    "username": "jamesniox_2025",
    "full_name": "James Niox",
    "is_active": true,
    "created_at": "2025-10-11T12:34:56Z",
    "roles": [
      {
        "role_id": 1,
        "role_name": "parent",
        "assigned_at": "2025-10-11T12:34:56Z"
      }
    ],
    "platform_links": {
      "telegram_user_id": 695065578,
      "whatsapp_user_id": null
    }
  },
  "metadata": {
    "request_id": "req_123456789",
    "processing_time_ms": 150,
    "validation_passed": true,
    "parent_matched": true
  }
}
```

#### Error Response (400 Bad Request)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Phone number validation failed",
    "details": {
      "phone_number": "+2214476978781",
      "validation_errors": ["Invalid mobile number format"]
    }
  },
  "metadata": {
    "request_id": "req_123456789",
    "processing_time_ms": 50
  }
}
```

#### Error Response (409 Conflict)

```json
{
  "success": false,
  "error": {
    "code": "ACCOUNT_EXISTS",
    "message": "Account already exists for this phone number",
    "details": {
      "phone_number": "+2214476978781",
      "existing_account_id": 98765,
      "existing_platform_links": ["telegram:695065578"]
    }
  }
}
```

### 2. Get Account by Phone Number

**Endpoint**: `GET /accounts/phone/{phone_number}`
**Purpose**: Retrieve user account by phone number
**Authentication**: JWT token with `account:read` scope

#### Response Schema (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "account_id": 98765,
    "phone_number": "+2214476978781",
    "username": "jamesniox_2025",
    "full_name": "James Niox",
    "email": "james.niox@example.com",
    "is_active": true,
    "created_at": "2025-10-11T12:34:56Z",
    "last_login_at": "2025-10-11T13:00:00Z",
    "account_source": "automatic",
    "created_via": "telegram",
    "roles": [
      {
        "role_id": 1,
        "role_name": "parent",
        "role_display_name": "Parent",
        "assigned_at": "2025-10-11T12:34:56Z",
        "assigned_by": null
      }
    ],
    "platform_links": {
      "telegram_user_id": 695065578,
      "whatsapp_user_id": null
    },
    "parent_info": {
      "parent_id": 12345,
      "parent_code": "PARENT001",
      "parent_name": "James Niox"
    }
  }
}
```

### 3. Link Platform Account

**Endpoint**: `POST /accounts/{user_id}/link-platform`
**Purpose**: Link messaging platform account to existing user
**Authentication**: JWT token with `account:write` scope

#### Request Schema

```json
{
  "platform": "whatsapp",
  "platform_user_id": "4476978781@c.us",
  "verification_code": "123456"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "platform_links": {
      "telegram_user_id": 695065578,
      "whatsapp_user_id": "4476978781@c.us"
    },
    "linked_at": "2025-10-11T13:00:00Z"
  }
}
```

### 4. Phone Number Validation

**Endpoint**: `POST /accounts/validate-phone`
**Purpose**: Validate and normalize phone number
**Authentication**: Service-to-service token

#### Request Schema

```json
{
  "phone_number": "+2214476978781",
  "country_code": "+221"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "data": {
    "phone_number": "+2214476978781",
    "country_code": "+221",
    "national_number": "4476978781",
    "is_valid": true,
    "is_mobile": true,
    "carrier": "Orange Senegal",
    "timezone": "Africa/Dakar",
    "normalized_formats": {
      "e164": "+2214476978781",
      "international": "+221 44 769 87 81",
      "national": "44 769 87 81",
      "rfc3966": "tel:+221-44-769-87-81"
    }
  }
}
```

### 5. Role Management

**Endpoint**: `POST /accounts/{user_id}/roles`
**Purpose**: Assign role to user account
**Authentication**: JWT token with `role:write` scope

#### Request Schema

```json
{
  "role_name": "catechist",
  "assigned_by": 54321,
  "expires_at": "2026-10-11T12:34:56Z",
  "assignment_notes": "Assigned as catechist for CM1 class"
}
```

#### Response Schema (201 Created)

```json
{
  "success": true,
  "data": {
    "assignment_id": 789,
    "user_id": 12345,
    "role_id": 3,
    "role_name": "catechist",
    "assigned_at": "2025-10-11T12:34:56Z",
    "assigned_by": 54321,
    "expires_at": "2026-10-11T12:34:56Z",
    "is_active": true
  }
}
```

**Endpoint**: `GET /accounts/{user_id}/roles`
**Purpose**: Get all roles assigned to user
**Authentication**: JWT token with `role:read` scope

#### Response Schema (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "roles": [
      {
        "role_id": 1,
        "role_name": "parent",
        "role_display_name": "Parent",
        "assigned_at": "2025-10-11T12:34:56Z",
        "assigned_by": null,
        "expires_at": null,
        "is_active": true
      },
      {
        "role_id": 3,
        "role_name": "catechist",
        "role_display_name": "Catéchiste",
        "assigned_at": "2025-10-11T15:00:00Z",
        "assigned_by": 54321,
        "expires_at": "2026-10-11T12:34:56Z",
        "is_active": true
      }
    ],
    "permissions": [
      "parent:view_children",
      "parent:register_child",
      "catechist:view_class",
      "catechist:manage_students"
    ]
  }
}
```

### 6. Super Admin Operations

**Endpoint**: `POST /admin/accounts/create-manual`
**Purpose**: Manual account creation by super admin
**Authentication**: JWT token with `super_admin` scope

#### Request Schema

```json
{
  "phone_number": "+221338765432",
  "full_name": "Marie Sarr",
  "email": "marie.sarr@example.com",
  "username": "mariesarr",
  "roles": ["parent", "secretary"],
  "parent_info": {
    "parent_code": "PARENT002",
    "address": "123 Rue de la Paix, Dakar"
  },
  "consent_given": true,
  "created_by": 54321
}
```

**Endpoint**: `GET /admin/accounts/search`
**Purpose**: Search user accounts by various criteria
**Authentication**: JWT token with `super_admin` scope

#### Query Parameters

- `phone_number`: Search by phone number
- `username`: Search by username
- `full_name`: Search by full name (partial match)
- `role_name`: Filter by role
- `is_active`: Filter by active status
- `created_after`: Filter accounts created after date
- `created_before`: Filter accounts created before date
- `limit`: Number of results (default: 50, max: 100)
- `offset`: Pagination offset (default: 0)

#### Response Schema (200 OK)

```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "user_id": 12345,
        "account_id": 98765,
        "phone_number": "+2214476978781",
        "username": "jamesniox_2025",
        "full_name": "James Niox",
        "is_active": true,
        "created_at": "2025-10-11T12:34:56Z",
        "roles": ["parent"],
        "parent_info": {
          "parent_id": 12345,
          "parent_code": "PARENT001"
        }
      }
    ],
    "pagination": {
      "total": 1,
      "limit": 50,
      "offset": 0,
      "has_more": false
    }
  }
}
```

## Error Handling

### Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific error details",
      "validation_errors": []
    }
  },
  "metadata": {
    "request_id": "req_123456789",
    "timestamp": "2025-10-11T12:34:56Z",
    "processing_time_ms": 150
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `ACCOUNT_NOT_FOUND` | 404 | User account not found |
| `ACCOUNT_EXISTS` | 409 | Account already exists |
| `PHONE_INVALID` | 400 | Invalid phone number format |
| `PARENT_NOT_FOUND` | 404 | Parent not found in database |
| `ROLE_NOT_FOUND` | 404 | Role not found |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `PLATFORM_ALREADY_LINKED` | 409 | Platform account already linked |
| `QUOTA_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |

## Rate Limiting

### Per-Endpoint Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /accounts/create` | 100/minute | Per IP |
| `GET /accounts/phone/{phone_number}` | 1000/minute | Per IP |
| `POST /accounts/{user_id}/roles` | 50/minute | Per user |
| `GET /admin/accounts/search` | 200/minute | Per user |

### Response Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1647895800
X-Request-ID: req_123456789
```

## Security

### Authentication Methods

1. **Service-to-Service**: Pre-shared API tokens for internal services
2. **User Authentication**: JWT tokens for user-initiated requests
3. **Admin Authentication**: JWT tokens with `super_admin` scope

### Authorization Scopes

- `account:read`: Read account information
- `account:write`: Create and modify accounts
- `role:read`: Read role assignments
- `role:write`: Modify role assignments
- `super_admin`: Full administrative access

### Input Validation

**Phone Number Validation**:
- Must be valid E.164 format
- Must be mobile number for target country
- Length and prefix validation

**Username Validation**:
- 3-50 characters
- Alphanumeric and underscores only
- Unique within system

**Email Validation**:
- Standard email format validation
- Optional field

## Testing

### Unit Test Scenarios

1. **Account Creation**
   - Valid phone number with parent match
   - Valid phone number without parent match
   - Invalid phone number format
   - Duplicate account creation

2. **Phone Validation**
   - Valid Senegalese numbers
   - Invalid numbers
   - International formats
   - Edge cases (short codes, etc.)

3. **Role Management**
   - Assign valid role
   - Assign invalid role
   - Remove role assignment
   - Role expiration handling

### Integration Test Scenarios

1. **End-to-End Account Creation**
   - Webhook → Account Creation → Welcome Message
   - Platform linking scenarios
   - Multi-platform account access

2. **Admin Operations**
   - Manual account creation
   - Account search and filtering
   - Bulk role assignments

## Monitoring

### Key Metrics

**Performance Metrics**:
- API response times by endpoint
- Database query performance
- Account creation success rate
- Phone validation accuracy

**Business Metrics**:
- Daily active users by platform
- Role assignment distribution
- Account creation sources
- User engagement patterns

### Health Checks

**Endpoint**: `GET /health`
**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2025-10-11T12:34:56Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "messaging": "healthy"
  },
  "metrics": {
    "accounts_created_today": 15,
    "active_users_today": 234,
    "phone_validation_success_rate": 0.99
  }
}
```

---

**Contract Status**: Ready for implementation. The internal API contract provides comprehensive coverage of the account creation service requirements with proper security, validation, and error handling.