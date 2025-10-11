"""
Phone Number Validation Utilities

This module provides comprehensive phone number validation and normalization
functionality for the automatic account creation system.
"""

import phonenumbers
import re
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum
from datetime import datetime
import logging


class PhoneNumberType(str, Enum):
    """Phone number types."""
    MOBILE = "mobile"
    LANDLINE = "landline"
    VOIP = "voip"
    TOLL_FREE = "toll_free"
    PREMIUM = "premium"
    UNKNOWN = "unknown"


class ValidationErrorCode(str, Enum):
    """Phone number validation error codes."""
    INVALID_FORMAT = "invalid_format"
    INVALID_COUNTRY = "invalid_country"
    NOT_MOBILE = "not_mobile"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    INVALID_CHARACTERS = "invalid_characters"
    UNSUPPORTED_REGION = "unsupported_region"


class ValidationError(Exception):
    """Base validation error."""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class PhoneNumberFormatError(ValidationError):
    """Phone number format error."""

    def __init__(self, message: str):
        super().__init__(f"Phone number format error: {message}", "INVALID_FORMAT")


class SenegalPhoneNumberError(ValidationError):
    """Senegal phone number error."""

    def __init__(self, message: str):
        super().__init__(f"Senegal phone number error: {message}", "INVALID_SENEGAL_NUMBER")


class UnsupportedCountryError(ValidationError):
    """Unsupported country error."""

    def __init__(self, message: str):
        super().__init__(f"Unsupported country error: {message}", "UNSUPPORTED_COUNTRY")


class PhoneNumberValidationResult:
    """Result of phone number validation matching test expectations."""

    def __init__(
        self,
        is_valid: bool = True,
        normalized_number: Optional[str] = None,
        country_code: Optional[str] = None,
        carrier: Optional[str] = None,
        number_type: Optional[str] = None,
        original_number: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.normalized_number = normalized_number
        self.country_code = country_code
        self.carrier = carrier
        self.number_type = number_type
        self.original_number = original_number
        self.error_code = error_code
        self.error_message = error_message


class PhoneValidationResult:
    """Result of phone number validation."""

    def __init__(
        self,
        is_valid: bool,
        phone_number: str,
        country_code: str = "SN",
        error_code: Optional[ValidationErrorCode] = None,
        error_message: Optional[str] = None,
        normalized_number: Optional[str] = None,
        phone_type: PhoneNumberType = PhoneNumberType.UNKNOWN,
        carrier: Optional[str] = None,
        region: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.phone_number = phone_number
        self.country_code = country_code
        self.error_code = error_code
        self.error_message = error_message
        self.normalized_number = normalized_number
        self.phone_type = phone_type
        self.carrier = carrier
        self.region = region
        self.validation_timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "phone_number": self.phone_number,
            "country_code": self.country_code,
            "error_code": self.error_code.value if self.error_code else None,
            "error_message": self.error_message,
            "normalized_number": self.normalized_number,
            "phone_type": self.phone_type.value,
            "carrier": self.carrier,
            "region": self.region,
            "validation_timestamp": self.validation_timestamp.isoformat()
        }


class PhoneValidator:
    """Phone number validation utility class."""

    # Supported country codes for Senegal and neighboring countries
    SUPPORTED_COUNTRY_CODES = {
        "SN": "Senegal",
        "ML": "Mali",
        "GN": "Guinea",
        "BF": "Burkina Faso",
        "NE": "Niger",
        "CI": "Ivory Coast",
        "TG": "Togo",
        "BJ": "Benin",
        "MR": "Mauritania"
    }

    # Mobile number prefixes for Senegal
    SENEGAL_MOBILE_PREFIXES = [
        "70", "71", "72", "73", "76", "77", "78", "79"
    ]

    # Known carriers in Senegal
    SENEGAL_CARRIERS = {
        "70": "Expresso",
        "71": "Expresso",
        "72": "Orange",
        "73": "Orange",
        "76": "Orange",
        "77": "Orange",
        "78": "Free",
        "79": "Free"
    }

    def __init__(self, default_country_code: str = "SN"):
        """
        Initialize phone validator.

        Args:
            default_country_code: Default country code for parsing
        """
        self.default_country_code = default_country_code
        self.logger = logging.getLogger(__name__)
        self._validation_stats = {
            "total_validations": 0,
            "valid_count": 0,
            "invalid_count": 0
        }

    async def validate_phone_number(
        self,
        phone_number: str,
        country_code: Optional[str] = None
    ) -> PhoneNumberValidationResult:
        """
        Async validate phone number - matches test expectations.

        Args:
            phone_number: Phone number to validate
            country_code: Country code (uses default if not provided)

        Returns:
            PhoneNumberValidationResult with validation details
        """
        try:
            # Input validation
            if phone_number is None:
                raise ValidationError("Phone number cannot be empty", "EMPTY_PHONE")

            if not isinstance(phone_number, str):
                raise ValidationError("Phone number must be a string", "INVALID_TYPE")

            if not phone_number.strip():
                raise ValidationError("Phone number cannot be empty", "EMPTY_PHONE")

            # Update stats
            self._validation_stats["total_validations"] += 1

            # Use provided country code or default
            code = country_code or self.default_country_code

            # Pre-process phone number
            cleaned_number = self._preprocess_phone_number(phone_number)
            original_number = phone_number

            # Parse phone number
            parsed_number = phonenumbers.parse(cleaned_number, code)

            # Check if valid
            if not phonenumbers.is_valid_number(parsed_number):
                self._validation_stats["invalid_count"] += 1
                return PhoneNumberValidationResult(
                    is_valid=False,
                    original_number=original_number,
                    error_code="INVALID_FORMAT",
                    error_message=f"Invalid phone number format for {code}"
                )

            # Determine phone type
            number_type = phonenumbers.number_type(parsed_number)
            mapped_type = self._map_phone_type(number_type)
            number_type_str = mapped_type.value

            # Get additional details
            carrier = phonenumbers.carrier.name_for_number(parsed_number, "en")
            region = phonenumbers.geocoder.description_for_number(parsed_number, "en")

            # Normalize to E.164 format
            normalized = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

            # Additional validation for Senegal numbers
            if parsed_number.country_code == 221:  # Senegal
                if not self._is_valid_senegal_mobile(normalized):
                    self._validation_stats["invalid_count"] += 1
                    return PhoneNumberValidationResult(
                        is_valid=False,
                        original_number=original_number,
                        error_code="INVALID_SENEGAL_NUMBER",
                        error_message="Invalid Senegal mobile number prefix"
                    )

            # Check if supported region
            if not self.is_supported_region(code):
                self._validation_stats["invalid_count"] += 1
                return PhoneNumberValidationResult(
                    is_valid=False,
                    original_number=original_number,
                    error_code="UNSUPPORTED_COUNTRY",
                    error_message=f"Unsupported country code: {code}"
                )

            # Update valid count
            self._validation_stats["valid_count"] += 1

            return PhoneNumberValidationResult(
                is_valid=True,
                normalized_number=normalized,
                country_code=code,
                carrier=carrier,
                number_type=number_type_str,
                original_number=original_number
            )

        except phonenumbers.NumberParseException as e:
            self._validation_stats["invalid_count"] += 1
            error_type = self._map_parse_exception_to_string(e)
            return PhoneNumberValidationResult(
                is_valid=False,
                original_number=phone_number,
                error_code=error_type,
                error_message=f"Phone number parsing error: {str(e)}"
            )
        except ValidationError as e:
            self._validation_stats["invalid_count"] += 1
            return PhoneNumberValidationResult(
                is_valid=False,
                original_number=phone_number,
                error_code=e.error_code,
                error_message=e.message
            )
        except Exception as e:
            self._validation_stats["invalid_count"] += 1
            return PhoneNumberValidationResult(
                is_valid=False,
                original_number=phone_number,
                error_code="PARSE_ERROR",
                error_message=f"Unexpected error: {str(e)}"
            )

    def validate_and_normalize(
        self,
        phone_number: str,
        country_code: Optional[str] = None,
        require_mobile: bool = True
    ) -> PhoneValidationResult:
        """
        Validate and normalize a phone number.

        Args:
            phone_number: Phone number to validate
            country_code: Country code (uses default if not provided)
            require_mobile: Whether to require mobile number

        Returns:
            PhoneValidationResult with validation details
        """
        try:
            # Use provided country code or default
            code = country_code or self.default_country_code

            # Pre-process phone number
            cleaned_number = self._preprocess_phone_number(phone_number)

            # Parse phone number
            parsed_number = phonenumbers.parse(cleaned_number, code)

            # Check if valid
            if not phonenumbers.is_valid_number(parsed_number):
                return self._create_invalid_result(
                    phone_number,
                    ValidationErrorCode.INVALID_FORMAT,
                    f"Invalid phone number format for {code}"
                )

            # Determine phone type
            number_type = phonenumbers.number_type(parsed_number)
            phone_type = self._map_phone_type(number_type)

            # Check if mobile is required
            if require_mobile and phone_type != PhoneNumberType.MOBILE:
                return self._create_invalid_result(
                    phone_number,
                    ValidationErrorCode.NOT_MOBILE,
                    "Mobile phone number required"
                )

            # Get additional details
            carrier = phonenumbers.carrier.name_for_number(parsed_number, "en")
            region = phonenumbers.geocoder.description_for_number(parsed_number, "en")

            # Normalize to E.164 format
            normalized = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

            # Additional validation for Senegal numbers
            if parsed_number.country_code == 221:  # Senegal
                if not self._is_valid_senegal_mobile(normalized):
                    return self._create_invalid_result(
                        phone_number,
                        ValidationErrorCode.NOT_MOBILE,
                        "Invalid Senegal mobile number prefix"
                    )

            return PhoneValidationResult(
                is_valid=True,
                phone_number=phone_number,
                country_code=code,
                normalized_number=normalized,
                phone_type=phone_type,
                carrier=carrier,
                region=region
            )

        except phonenumbers.NumberParseException as e:
            error_type = self._map_parse_exception(e)
            return self._create_invalid_result(
                phone_number,
                error_type,
                f"Phone number parsing error: {str(e)}"
            )
        except Exception as e:
            return self._create_invalid_result(
                phone_number,
                ValidationErrorCode.INVALID_FORMAT,
                f"Unexpected error: {str(e)}"
            )

    def _preprocess_phone_number(self, phone_number: str) -> str:
        """
        Pre-process phone number for parsing.

        Args:
            phone_number: Raw phone number

        Returns:
            Cleaned phone number
        """
        # Remove common separators and extra characters
        cleaned = re.sub(r'[.\-\s\(\)]', '', phone_number)

        # Handle international prefixes
        if cleaned.startswith('00'):
            cleaned = '+' + cleaned[2:]
        elif cleaned.startswith('+'):
            cleaned = cleaned  # Already has +
        elif cleaned.startswith('221') and len(cleaned) >= 9:  # Senegal without +
            cleaned = '+' + cleaned

        return cleaned

    def _map_phone_type(self, phonenumbers_type: phonenumbers.PhoneNumberType) -> PhoneNumberType:
        """Map phonenumbers type to our PhoneNumberType enum."""
        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: PhoneNumberType.MOBILE,
            phonenumbers.PhoneNumberType.FIXED_LINE: PhoneNumberType.LANDLINE,
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: PhoneNumberType.MOBILE,
            phonenumbers.PhoneNumberType.VOIP: PhoneNumberType.VOIP,
            phonenumbers.PhoneNumberType.TOLL_FREE: PhoneNumberType.TOLL_FREE,
            phonenumbers.PhoneNumberType.PREMIUM_RATE: PhoneNumberType.PREMIUM,
            phonenumbers.PhoneNumberType.SHARED_COST: PhoneNumberType.VOIP,
            phonenumbers.PhoneNumberType.VOICEMAIL: PhoneNumberType.VOIP,
            phonenumbers.PhoneNumberType.PAGER: PhoneNumberType.UNKNOWN,
            phonenumbers.PhoneNumberType.UAN: PhoneNumberType.UNKNOWN,
            phonenumbers.PhoneNumberType.UNKNOWN: PhoneNumberType.UNKNOWN,
        }
        return type_mapping.get(phonenumbers_type, PhoneNumberType.UNKNOWN)

    def _map_parse_exception_to_string(self, exception: phonenumbers.NumberParseException) -> str:
        """Map phonenumbers exception to string error code."""
        error_type = str(exception.error_type)

        if error_type == "INVALID_COUNTRY_CODE":
            return "INVALID_COUNTRY_CODE"
        elif error_type == "NOT_A_NUMBER":
            return "PARSE_ERROR"
        elif error_type == "TOO_SHORT_NSN":
            return "TOO_SHORT"
        elif error_type == "TOO_LONG_NSN":
            return "TOO_LONG"
        else:
            return "PARSE_ERROR"

    def _map_parse_exception(self, exception: phonenumbers.NumberParseException) -> ValidationErrorCode:
        """Map phonenumbers exception to validation error code."""
        error_type = str(exception.error_type)

        if error_type == "INVALID_COUNTRY_CODE":
            return ValidationErrorCode.INVALID_COUNTRY
        elif error_type == "NOT_A_NUMBER":
            return ValidationErrorCode.INVALID_FORMAT
        elif error_type == "TOO_SHORT_NSN":
            return ValidationErrorCode.TOO_SHORT
        elif error_type == "TOO_LONG_NSN":
            return ValidationErrorCode.TOO_LONG
        else:
            return ValidationErrorCode.INVALID_FORMAT

    def _is_valid_senegal_mobile(self, phone_number: str) -> bool:
        """
        Check if phone number is a valid Senegal mobile number.

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            True if valid Senegal mobile number
        """
        # Extract national number (remove +221)
        if not phone_number.startswith("+221"):
            return False

        national_number = phone_number[4:]  # Remove +221

        # Check length (should be 9 digits)
        if len(national_number) != 9:
            return False

        # Check prefix
        prefix = national_number[:2]
        return prefix in self.SENEGAL_MOBILE_PREFIXES

    def _create_invalid_result(
        self,
        phone_number: str,
        error_code: ValidationErrorCode,
        error_message: str
    ) -> PhoneValidationResult:
        """Create an invalid validation result."""
        return PhoneValidationResult(
            is_valid=False,
            phone_number=phone_number,
            country_code=self.default_country_code,
            error_code=error_code,
            error_message=error_message
        )

    def get_senegal_carrier(self, phone_number: str) -> Optional[str]:
        """
        Get carrier for Senegal phone number.

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            Carrier name if known, None otherwise
        """
        if not phone_number.startswith("+221"):
            return None

        national_number = phone_number[4:]
        if len(national_number) >= 2:
            prefix = national_number[:2]
            return self.SENEGAL_CARRIERS.get(prefix)

        return None

    def normalize_for_database_lookup(self, phone_number: str) -> List[str]:
        """
        Generate normalized versions of phone number for database lookup.

        Args:
            phone_number: Original phone number

        Returns:
            List of normalized phone numbers to try
        """
        normalized_variants = []

        # Validate and get the main normalized form
        result = self.validate_and_normalize(phone_number)

        if result.is_valid and result.normalized_number:
            normalized_variants.append(result.normalized_number)

            # Add additional variants for database matching
            e164 = result.normalized_number

            # Remove country code
            if e164.startswith("+221"):
                national = e164[4:]  # Remove +221
                normalized_variants.append(national)

                # Add with 00221 prefix
                normalized_variants.append("00221" + national)

            # Remove separators and spaces
            clean = re.sub(r'[^\d+]', '', phone_number)
            if clean not in normalized_variants:
                normalized_variants.append(clean)

        return list(set(normalized_variants))  # Remove duplicates

    async def validate_phone_numbers_batch(
        self,
        phone_numbers: List[str],
        country_code: Optional[str] = None
    ) -> List[PhoneNumberValidationResult]:
        """
        Async batch validate phone numbers.

        Args:
            phone_numbers: List of phone numbers to validate
            country_code: Country code (uses default if not provided)

        Returns:
            List of PhoneNumberValidationResults
        """
        results = []
        for phone_number in phone_numbers:
            result = await self.validate_phone_number(phone_number, country_code)
            results.append(result)
        return results

    def batch_validate(self, phone_numbers: List[str]) -> List[PhoneValidationResult]:
        """
        Validate multiple phone numbers.

        Args:
            phone_numbers: List of phone numbers to validate

        Returns:
            List of validation results
        """
        results = []
        for phone_number in phone_numbers:
            result = self.validate_and_normalize(phone_number)
            results.append(result)

        return results

    def get_supported_regions(self) -> Dict[str, str]:
        """Get supported country codes and regions."""
        return self.SUPPORTED_COUNTRY_CODES.copy()

    def is_supported_region(self, country_code: str) -> bool:
        """Check if country code is supported."""
        return country_code.upper() in self.SUPPORTED_COUNTRY_CODES

    def is_senegal_mobile_number(self, phone_number: str) -> bool:
        """
        Check if phone number is a Senegal mobile number.

        Args:
            phone_number: Phone number to check

        Returns:
            True if Senegal mobile number
        """
        try:
            # Parse the number first
            parsed_number = phonenumbers.parse(phone_number, "SN")

            # Check if it's Senegal and valid
            if parsed_number.country_code != 221:
                return False

            if not phonenumbers.is_valid_number(parsed_number):
                return False

            # Normalize to E.164 format
            normalized = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

            return self._is_valid_senegal_mobile(normalized)
        except:
            return False

    def normalize_phone_number(self, phone_number: str, country_code: Optional[str] = None) -> Optional[str]:
        """
        Normalize phone number to E.164 format.

        Args:
            phone_number: Phone number to normalize
            country_code: Country code (uses default if not provided)

        Returns:
            Normalized phone number or None if invalid
        """
        try:
            result = self.validate_and_normalize(phone_number, country_code)
            if result.is_valid:
                return result.normalized_number
            return None
        except:
            return None

    def get_senegal_carrier_info(self, phone_number: str) -> str:
        """
        Get detailed carrier information for Senegal phone number.

        Args:
            phone_number: Phone number in any format

        Returns:
            Carrier information string
        """
        carrier = self.get_senegal_carrier(phone_number)
        if carrier:
            return carrier

        # Try to get more detailed info using phonenumbers
        try:
            parsed_number = phonenumbers.parse(phone_number, "SN")
            if parsed_number.country_code == 221:
                carrier = phonenumbers.carrier.name_for_number(parsed_number, "en")
                return carrier or "Unknown"
        except:
            pass

        return "Unknown"

    def mask_phone_number(self, phone_number: str) -> str:
        """
        Mask phone number for privacy.

        Args:
            phone_number: Phone number to mask

        Returns:
            Masked phone number
        """
        if not phone_number or len(phone_number) < 4:
            return phone_number

        # Keep last 2 digits visible, mask the rest
        if phone_number.startswith("+"):
            if len(phone_number) <= 6:  # +221XX
                return phone_number[:4] + "*" * (len(phone_number) - 6) + phone_number[-2:]
            else:
                return phone_number[:4] + "*" * (len(phone_number) - 6) + phone_number[-2:]
        else:
            if len(phone_number) <= 4:
                return phone_number[:2] + "*" * (len(phone_number) - 4) + phone_number[-2:]
            else:
                return phone_number[:2] + "*" * (len(phone_number) - 4) + phone_number[-2:]

    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.

        Returns:
            Dictionary with validation stats
        """
        total = self._validation_stats["total_validations"]
        valid = self._validation_stats["valid_count"]

        return {
            **self._validation_stats,
            "success_rate": valid / total if total > 0 else 0.0
        }

    def reset_statistics(self) -> None:
        """Reset validation statistics."""
        self._validation_stats = {
            "total_validations": 0,
            "valid_count": 0,
            "invalid_count": 0
        }


# Global validator instance
phone_validator = PhoneValidator()


# Convenience functions
def validate_phone_number(
    phone_number: str,
    country_code: Optional[str] = None,
    require_mobile: bool = True
) -> PhoneValidationResult:
    """
    Validate and normalize a phone number.

    Args:
        phone_number: Phone number to validate
        country_code: Country code (uses default if not provided)
        require_mobile: Whether to require mobile number

    Returns:
        PhoneValidationResult with validation details
    """
    return phone_validator.validate_and_normalize(phone_number, country_code, require_mobile)


def normalize_for_lookup(phone_number: str) -> List[str]:
    """
    Generate normalized versions of phone number for database lookup.

    Args:
        phone_number: Original phone number

    Returns:
        List of normalized phone numbers to try
    """
    return phone_validator.normalize_for_database_lookup(phone_number)


def get_senegal_carrier(phone_number: str) -> Optional[str]:
    """
    Get carrier for Senegal phone number.

    Args:
        phone_number: Phone number in E.164 format

    Returns:
        Carrier name if known, None otherwise
    """
    return phone_validator.get_senegal_carrier(phone_number)