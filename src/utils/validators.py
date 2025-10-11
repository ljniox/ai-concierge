"""
Common Validation Utilities

Provides reusable validation functions for:
- Phone numbers (E.164 format)
- Email addresses
- Document files (size, format)
- Names and personal information
- French-specific formats (codes, dates)

Constitution Principle II: Type safety and input validation
Research Decision: File size ≤10MB (FR-002)
"""

import re
import imghdr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from pathlib import Path

from .exceptions import ValidationError


class ValidationResult:
    """Container for validation results."""

    def __init__(self, is_valid: bool, message: str = None, field: str = None):
        self.is_valid = is_valid
        self.message = message
        self.field = field

    def __bool__(self):
        return self.is_valid

    def raise_if_invalid(self):
        """Raise ValidationError if validation failed."""
        if not self.is_valid:
            raise ValidationError(
                message=self.message,
                field=self.field
            )


def validate_phone_number(phone: str, country_code: str = "SN") -> ValidationResult:
    """
    Validate phone number in E.164 format.

    Args:
        phone: Phone number to validate
        country_code: Country code for format validation (default: SN for Senegal)

    Returns:
        ValidationResult: Validation result with details

    Examples:
        validate_phone_number("+221770000001")  # Valid
        validate_phone_number("770000001")      # Invalid (missing +)
        validate_phone_number("+33612345678")   # Valid (French number)
    """
    if not phone:
        return ValidationResult(False, "Phone number is required", "telephone")

    # Basic E.164 validation
    e164_pattern = r'^\+[1-9]\d{1,14}$'
    if not re.match(e164_pattern, phone):
        return ValidationResult(
            False,
            "Invalid phone number format. Use E.164 format (e.g., +221770000001)",
            "telephone"
        )

    # Country-specific validations
    if country_code == "SN":
        # Senegal numbers: +221 33, 76, 77, 78, 70
        if phone.startswith("+221"):
            senegal_pattern = r'^\+221(33|76|77|78|70)\d{7}$'
            if not re.match(senegal_pattern, phone):
                return ValidationResult(
                    False,
                    "Invalid Senegal phone number. Must start with +221 followed by 33, 76, 77, 78, or 70",
                    "telephone"
                )

    return ValidationResult(True)


def validate_email(email: str) -> ValidationResult:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        ValidationResult: Validation result with details

    Examples:
        validate_email("user@example.com")     # Valid
        validate_email("user@")                # Invalid
        validate_email("user.example.com")     # Invalid
    """
    if not email:
        return ValidationResult(False, "Email is required", "email")

    # RFC 5322 compliant email regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return ValidationResult(
            False,
            "Invalid email format. Example: user@domain.com",
            "email"
        )

    # Check for common issues
    if email.startswith('.') or email.endswith('.'):
        return ValidationResult(
            False,
            "Email cannot start or end with a dot",
            "email"
        )

    if '..' in email:
        return ValidationResult(
            False,
            "Email cannot contain consecutive dots",
            "email"
        )

    return ValidationResult(True)


def validate_name(name: str, field_name: str = "name", min_length: int = 2, max_length: int = 50) -> ValidationResult:
    """
    Validate person name (first name or last name).

    Args:
        name: Name to validate
        field_name: Name of the field for error messages
        min_length: Minimum length requirement
        max_length: Maximum length requirement

    Returns:
        ValidationResult: Validation result with details
    """
    if not name or not name.strip():
        return ValidationResult(False, f"{field_name.title()} is required", field_name)

    name = name.strip()

    if len(name) < min_length:
        return ValidationResult(
            False,
            f"{field_name.title()} must be at least {min_length} characters long",
            field_name
        )

    if len(name) > max_length:
        return ValidationResult(
            False,
            f"{field_name.title()} cannot exceed {max_length} characters",
            field_name
        )

    # Check for allowed characters (letters, hyphens, apostrophes, spaces)
    name_pattern = r"^[a-zA-Z\u00C0-\u00FF\s\-']+$"  # Includes French accented characters
    if not re.match(name_pattern, name):
        return ValidationResult(
            False,
            f"{field_name.title()} can only contain letters, spaces, hyphens, and apostrophes",
            field_name
        )

    # Check for consecutive spaces or hyphens
    if '  ' in name or '--' in name:
        return ValidationResult(
            False,
            f"{field_name.title()} cannot contain consecutive spaces or hyphens",
            field_name
        )

    return ValidationResult(True)


def validate_french_date(date_str: str, field_name: str = "date") -> ValidationResult:
    """
    Validate French date format (DD/MM/YYYY or YYYY-MM-DD).

    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages

    Returns:
        ValidationResult: Validation result with details

    Examples:
        validate_french_date("12/03/2015")    # Valid
        validate_french_date("2015-03-12")    # Valid
        validate_french_date("31/02/2025")    # Invalid (Feb 31)
    """
    if not date_str:
        return ValidationResult(False, f"{field_name.title()} is required", field_name)

    date_str = date_str.strip()

    # Try DD/MM/YYYY format (French)
    try:
        parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
        return ValidationResult(True)
    except ValueError:
        pass

    # Try YYYY-MM-DD format (ISO)
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        return ValidationResult(True)
    except ValueError:
        pass

    return ValidationResult(
        False,
        f"Invalid {field_name} format. Use DD/MM/YYYY (e.g., 12/03/2015) or YYYY-MM-DD (e.g., 2015-03-12)",
        field_name
    )


def validate_montant(montant: Union[int, float, str], min_amount: int = 100, max_amount: int = 1000000) -> ValidationResult:
    """
    Validate monetary amount.

    Args:
        montant: Amount to validate (can be int, float, or string)
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount

    Returns:
        ValidationResult: Validation result with details
    """
    if montant is None or montant == "":
        return ValidationResult(False, "Amount is required", "montant")

    # Convert to float
    try:
        amount_float = float(str(montant).replace(',', '.'))
    except (ValueError, TypeError):
        return ValidationResult(
            False,
            "Invalid amount format. Use numbers only (e.g., 15000 or 15000.50)",
            "montant"
        )

    # Check range
    if amount_float < min_amount:
        return ValidationResult(
            False,
            f"Amount must be at least {min_amount} FCFA",
            "montant"
        )

    if amount_float > max_amount:
        return ValidationResult(
            False,
            f"Amount cannot exceed {max_amount} FCFA",
            "montant"
        )

    # Check for reasonable decimal places (max 2)
    if abs(amount_float - round(amount_float, 2)) > 0.0001:
        return ValidationResult(
            False,
            "Amount can have maximum 2 decimal places",
            "montant"
        )

    return ValidationResult(True)


def validate_document_file(file_path: str, allowed_types: List[str] = None, max_size_mb: int = 10) -> ValidationResult:
    """
    Validate document file (size and format).

    Args:
        file_path: Path to the file
        allowed_types: List of allowed file extensions (default: common document types)
        max_size_mb: Maximum file size in MB (default: 10MB per FR-002)

    Returns:
        ValidationResult: Validation result with details

    Research Decision: File size ≤10MB (FR-002)
    """
    if not file_path:
        return ValidationResult(False, "File path is required", "file")

    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        return ValidationResult(False, "File does not exist", "file")

    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return ValidationResult(
            False,
            f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)",
            "file"
        )

    # Default allowed types
    if allowed_types is None:
        allowed_types = ['pdf', 'jpg', 'jpeg', 'png', 'heic', 'doc', 'docx']

    # Check file extension
    file_extension = file_path.suffix.lower().lstrip('.')
    if file_extension not in allowed_types:
        return ValidationResult(
            False,
            f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}",
            "file"
        )

    # Additional validation for image files
    if file_extension in ['jpg', 'jpeg', 'png', 'heic']:
        # Verify it's actually an image file
        if not imghdr.what(str(file_path)):
            return ValidationResult(
                False,
                "File is not a valid image file",
                "file"
            )

    return ValidationResult(True)


def validate_code_parent(code: str) -> ValidationResult:
    """
    Validate parent code format.

    Args:
        code: Parent code to validate

    Returns:
        ValidationResult: Validation result with details

    Examples:
        validate_code_parent("CAT-12345")    # Valid
        validate_code_parent("1de90")        # Valid (legacy format)
        validate_code_parent("ABC")          # Invalid (too short)
    """
    if not code:
        return ValidationResult(False, "Parent code is required", "code_parent")

    code = code.strip().upper()

    # Legacy format (alphanumeric, 5-8 chars)
    legacy_pattern = r'^[A-Z0-9]{5,8}$'
    if re.match(legacy_pattern, code):
        return ValidationResult(True)

    # New format (CAT-XXXXX)
    new_pattern = r'^CAT-\d{5}$'
    if re.match(new_pattern, code):
        return ValidationResult(True)

    return ValidationResult(
        False,
        "Invalid parent code format. Use legacy format (e.g., 1de90) or new format (e.g., CAT-12345)",
        "code_parent"
    )


def validate_annee_catechetique(annee: str) -> ValidationResult:
    """
    Validate catechism year format (YYYY-YYYY).

    Args:
        annee: Year string to validate

    Returns:
        ValidationResult: Validation result with details

    Examples:
        validate_annee_catechetique("2025-2026")    # Valid
        validate_annee_catechetique("2025-2025")    # Invalid
        validate_annee_catechetique("2025")         # Invalid
    """
    if not annee:
        return ValidationResult(False, "Catechism year is required", "annee_catechetique")

    annee = annee.strip()

    # Pattern: YYYY-YYYY+1
    pattern = r'^(\d{4})-(\d{4})$'
    match = re.match(pattern, annee)

    if not match:
        return ValidationResult(
            False,
            "Invalid catechism year format. Use YYYY-YYYY format (e.g., 2025-2026)",
            "annee_catechetique"
        )

    start_year = int(match.group(1))
    end_year = int(match.group(2))

    # Check if end year is exactly one year after start year
    if end_year != start_year + 1:
        return ValidationResult(
            False,
            "End year must be exactly one year after start year",
            "annee_catechetique"
        )

    # Check reasonable year range
    current_year = datetime.now().year
    if start_year < current_year - 5 or start_year > current_year + 5:
        return ValidationResult(
            False,
            f"Catechism year {start_year}-{end_year} is outside reasonable range",
            "annee_catechetique"
        )

    return ValidationResult(True)


def validate_niveau_catechese(niveau: str) -> ValidationResult:
    """
    Validate catechism level.

    Args:
        niveau: Catechism level to validate

    Returns:
        ValidationResult: Validation result with details
    """
    if not niveau:
        return ValidationResult(False, "Catechism level is required", "niveau")

    valid_levels = ['éveil', 'CE1', 'CE2', 'CM1', 'CM2', 'confirmation']

    niveau = niveau.strip().lower()
    if niveau not in valid_levels:
        return ValidationResult(
            False,
            f"Invalid catechism level. Valid levels: {', '.join(valid_levels)}",
            "niveau"
        )

    return ValidationResult(True)


def validate_uuid(uuid_str: str) -> ValidationResult:
    """
    Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        ValidationResult: Validation result with details
    """
    if not uuid_str:
        return ValidationResult(False, "UUID is required", "id")

    import uuid as uuid_lib

    try:
        uuid_lib.UUID(uuid_str)
        return ValidationResult(True)
    except ValueError:
        return ValidationResult(
            False,
            "Invalid UUID format",
            "id"
        )


def validate_temp_page_code(code: str) -> ValidationResult:
    """
    Validate temporary page access code (8 alphanumeric chars).

    Args:
        code: Access code to validate

    Returns:
        ValidationResult: Validation result with details
    """
    if not code:
        return ValidationResult(False, "Access code is required", "code_acces")

    # Pattern: 8 alphanumeric characters, excluding confusing characters (0, O, 1, I, L)
    pattern = r'^[A-HJ-NP-Z2-9]{8}$'  # Excludes 0, O, 1, I, L

    if not re.match(pattern, code.upper()):
        return ValidationResult(
            False,
            "Invalid access code format. Must be 8 alphanumeric characters",
            "code_acces"
        )

    return ValidationResult(True)


# Batch validation
def validate_multiple(data: Dict[str, Any], validators: Dict[str, callable]) -> List[ValidationResult]:
    """
    Validate multiple fields using provided validators.

    Args:
        data: Dictionary of data to validate
        validators: Dictionary mapping field names to validator functions

    Returns:
        List[ValidationResult]: List of validation results
    """
    results = []

    for field_name, validator in validators.items():
        field_value = data.get(field_name)
        result = validator(field_value)
        result.field = field_name
        results.append(result)

    return results


def validate_batch_results(results: List[ValidationResult]) -> ValidationResult:
    """
    Combine multiple validation results into one.

    Args:
        results: List of validation results

    Returns:
        ValidationResult: Combined result (first error if any, otherwise success)
    """
    for result in results:
        if not result.is_valid:
            return result

    return ValidationResult(True, "All validations passed")