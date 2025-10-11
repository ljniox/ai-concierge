"""
Phone number validation service for the automatic account creation system.

This module provides phone number validation with Senegal-specific rules,
international formatting, and comprehensive validation logic.
"""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from src.utils.logging import get_logger
from src.utils.exceptions import ValidationError

logger = get_logger(__name__)


@dataclass
class PhoneNumberInfo:
    """Phone number information and validation result."""
    original_number: str
    normalized_number: str
    country_code: str
    is_valid: bool
    phone_type: Optional[str] = None
    carrier: Optional[str] = None
    region: Optional[str] = None
    validation_errors: List[str] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class PhoneValidationService:
    """
    Phone number validation service with Senegal-specific rules.

    Provides validation for Senegal mobile numbers and international
    phone numbers with comprehensive formatting and validation logic.
    """

    def __init__(self):
        # Senegal mobile operator prefixes
        self.senegal_mobile_prefixes = {
            '77': {'operator': 'Orange', 'type': 'mobile'},
            '76': {'operator': 'Orange', 'type': 'mobile'},
            '75': {'operator': 'Expresso', 'type': 'mobile'},
            '70': {'operator': 'Expresso', 'type': 'mobile'},
            '78': {'operator': 'Free', 'type': 'mobile'},
            '33': {'operator': 'Free', 'type': 'landline'},
            '30': {'operator': 'Sonatel', 'type': 'landline'},
        }

        # International country codes for validation
        self.country_codes = {
            'SN': {'code': '221', 'name': 'Senegal', 'phone_length': 9},
            # Other West African countries for reference
            'ML': {'code': '223', 'name': 'Mali', 'phone_length': 8},
            'BF': {'code': '226', 'name': 'Burkina Faso', 'phone_length': 8},
            'NE': {'code': '227', 'name': 'Niger', 'phone_length': 8},
            'CI': {'code': '225', 'name': 'Côte d\'Ivoire', 'phone_length': 8},
            'GN': {'code': '224', 'name': 'Guinea', 'phone_length': 8},
            'GH': {'code': '233', 'name': 'Ghana', 'phone_length': 9},
        }

        # Validation patterns
        self.patterns = {
            # Senegal mobile patterns
            'senegal_mobile': re.compile(r'^(\+221|00221)?(7[0-8]|6[0-9])[0-9]{7}$'),
            'senegal_landline': re.compile(r'^(\+221|00221)?(3[0-9])[0-9]{7}$'),

            # International patterns
            'international': re.compile(r'^\+[1-9][0-9]{6,14}$'),
            'with_zeros': re.compile(r'^00[1-9][0-9]{6,14}$'),

            # Basic validation patterns
            'numeric_only': re.compile(r'^[0-9]+$'),
            'starts_with_plus': re.compile(r'^\+'),
            'valid_chars': re.compile(r'^[0-9\+\-\(\)\s]+$'),
        }

    def validate_phone_number(self, phone_number: str, country_code: str = 'SN') -> PhoneNumberInfo:
        """
        Validate and parse a phone number.

        Args:
            phone_number: Phone number to validate
            country_code: ISO country code (default: 'SN' for Senegal)

        Returns:
            PhoneNumberInfo with validation results

        Raises:
            ValidationError: If phone number format is invalid
        """
        if not phone_number or not isinstance(phone_number, str):
            raise ValidationError("Phone number must be a non-empty string")

        # Clean and normalize the phone number
        cleaned_number = self._clean_phone_number(phone_number)

        if not cleaned_number:
            raise ValidationError("Phone number contains no valid digits")

        # Determine the country and normalize to international format
        normalized_number, detected_country = self._normalize_to_international(cleaned_number, country_code)

        # Validate according to country rules
        if detected_country == 'SN':
            validation_result = self._validate_senegal_number(normalized_number)
        else:
            validation_result = self._validate_international_number(normalized_number, detected_country)

        return validation_result

    def _clean_phone_number(self, phone_number: str) -> str:
        """
        Clean phone number by removing non-numeric characters except leading +.

        Args:
            phone_number: Raw phone number

        Returns:
            Cleaned phone number
        """
        # Remove all characters except digits and leading +
        cleaned = re.sub(r'[^\d\+]', '', phone_number)

        # Ensure + only appears at the beginning
        if '+' in cleaned[1:]:
            cleaned = '+' + re.sub(r'\+', '', cleaned[1:])

        return cleaned

    def _normalize_to_international(self, phone_number: str, default_country: str) -> Tuple[str, str]:
        """
        Normalize phone number to international format.

        Args:
            phone_number: Cleaned phone number
            default_country: Default country code

        Returns:
            Tuple of (normalized_number, detected_country)
        """
        # If already in international format with +
        if phone_number.startswith('+'):
            # Extract country code
            country_code = phone_number[1:4]  # First 3 digits after +
            if country_code == '221':
                return phone_number, 'SN'
            else:
                # Try to detect country from other codes
                for code, info in self.country_codes.items():
                    if info['code'] == country_code:
                        return phone_number, code
                return phone_number, 'UNKNOWN'

        # If starts with 00 (international dialing prefix)
        elif phone_number.startswith('00'):
            country_code = phone_number[2:5]  # First 3 digits after 00
            if country_code == '221':
                return '+' + phone_number[2:], 'SN'
            else:
                for code, info in self.country_codes.items():
                    if info['code'] == country_code:
                        return '+' + phone_number[2:], code
                return '+' + phone_number[2:], 'UNKNOWN'

        # Local number (assume Senegal for local context)
        else:
            if default_country == 'SN':
                # For Senegal local numbers
                if len(phone_number) == 9 and phone_number[0] in ['7', '3']:
                    return '+221' + phone_number, 'SN'
                elif len(phone_number) == 7:  # Short format without area code
                    # Assume mobile prefix 7x for short numbers
                    return '+2217' + phone_number, 'SN'

            # Default: add country code based on default country
            if default_country in self.country_codes:
                return f"+{self.country_codes[default_country]['code']}{phone_number}", default_country

        return phone_number, 'UNKNOWN'

    def _validate_senegal_number(self, phone_number: str) -> PhoneNumberInfo:
        """
        Validate Senegal phone number.

        Args:
            phone_number: International format phone number (+221...)

        Returns:
            PhoneNumberInfo with validation results
        """
        original_number = phone_number
        validation_errors = []
        is_valid = True
        phone_type = None
        carrier = None
        region = 'Senegal'

        # Extract local number (remove +221)
        if not phone_number.startswith('+221'):
            validation_errors.append("Invalid Senegal country code")
            is_valid = False
            local_number = phone_number
        else:
            local_number = phone_number[4:]

        # Validate local number format
        if len(local_number) != 9:
            validation_errors.append(f"Senegal phone number must have 9 digits, got {len(local_number)}")
            is_valid = False

        # Check operator prefix
        if len(local_number) >= 2:
            prefix = local_number[:2]
            if prefix in self.senegal_mobile_prefixes:
                phone_type = self.senegal_mobile_prefixes[prefix]['type']
                carrier = self.senegal_mobile_prefixes[prefix]['operator']
            else:
                validation_errors.append(f"Unknown Senegal operator prefix: {prefix}")
                is_valid = False

        # Additional validation rules
        if is_valid:
            # Check if it's a mobile number (required for account creation)
            if phone_type != 'mobile':
                validation_errors.append("Only mobile numbers are allowed for account creation")
                is_valid = False

            # Validate number ranges for mobile prefixes
            if prefix == '77':  # Orange
                if not (local_number[2] in ['0', '1', '6', '7', '8']):
                    validation_errors.append("Invalid Orange mobile number range")
                    is_valid = False
            elif prefix == '78':  # Free
                if not (local_number[2] in ['0', '1', '2', '5', '6', '7']):
                    validation_errors.append("Invalid Free mobile number range")
                    is_valid = False

        return PhoneNumberInfo(
            original_number=original_number,
            normalized_number=phone_number,
            country_code='221',
            is_valid=is_valid,
            phone_type=phone_type,
            carrier=carrier,
            region=region,
            validation_errors=validation_errors
        )

    def _validate_international_number(self, phone_number: str, country_code: str) -> PhoneNumberInfo:
        """
        Validate international phone number.

        Args:
            phone_number: International format phone number
            country_code: Detected country code

        Returns:
            PhoneNumberInfo with validation results
        """
        validation_errors = []
        is_valid = True
        phone_type = 'mobile'  # Assume mobile for international
        carrier = None
        region = self.country_codes.get(country_code, {}).get('name', 'Unknown')

        # Basic international format validation
        if not phone_number.startswith('+'):
            validation_errors.append("International number must start with +")
            is_valid = False

        # Extract country code and local number
        match = re.match(r'^\+([1-9][0-9]{0,2})([0-9]{6,15})$', phone_number)
        if not match:
            validation_errors.append("Invalid international phone number format")
            is_valid = False
        else:
            detected_country_code, local_number = match.groups()

            # Validate local number length if we have country info
            if country_code in self.country_codes:
                expected_length = self.country_codes[country_code]['phone_length']
                if len(local_number) != expected_length:
                    validation_errors.append(
                        f"Phone number length mismatch for {region}. "
                        f"Expected {expected_length} digits, got {len(local_number)}"
                    )
                    is_valid = False

        # For non-Senegal numbers, we might want to be more restrictive
        if country_code != 'SN':
            validation_errors.append("Only Senegal phone numbers are currently supported")
            is_valid = False

        return PhoneNumberInfo(
            original_number=phone_number,
            normalized_number=phone_number,
            country_code=country_code,
            is_valid=is_valid,
            phone_type=phone_type,
            carrier=carrier,
            region=region,
            validation_errors=validation_errors
        )

    def is_senegal_mobile_number(self, phone_number: str) -> bool:
        """
        Quick check if number is a valid Senegal mobile number.

        Args:
            phone_number: Phone number to check

        Returns:
            True if valid Senegal mobile number
        """
        try:
            validation_result = self.validate_phone_number(phone_number, 'SN')
            return validation_result.is_valid and validation_result.phone_type == 'mobile'
        except ValidationError:
            return False

    def get_carrier_info(self, phone_number: str) -> Optional[Dict[str, str]]:
        """
        Get carrier information for a phone number.

        Args:
            phone_number: Phone number

        Returns:
            Carrier information or None
        """
        try:
            validation_result = self.validate_phone_number(phone_number, 'SN')
            if validation_result.is_valid and validation_result.carrier:
                return {
                    'carrier': validation_result.carrier,
                    'type': validation_result.phone_type,
                    'region': validation_result.region,
                    'country_code': validation_result.country_code
                }
        except ValidationError:
            pass
        return None

    def normalize_for_storage(self, phone_number: str) -> str:
        """
        Normalize phone number for database storage.

        Args:
            phone_number: Raw phone number

        Returns:
            Normalized international format number

        Raises:
            ValidationError: If number cannot be normalized
        """
        validation_result = self.validate_phone_number(phone_number, 'SN')
        if not validation_result.is_valid:
            raise ValidationError(f"Invalid phone number: {', '.join(validation_result.validation_errors)}")
        return validation_result.normalized_number

    def format_for_display(self, phone_number: str, format_type: str = 'international') -> str:
        """
        Format phone number for display.

        Args:
            phone_number: Phone number to format
            format_type: Format type ('international', 'national', 'masked')

        Returns:
            Formatted phone number

        Raises:
            ValidationError: If number is invalid
        """
        validation_result = self.validate_phone_number(phone_number, 'SN')
        if not validation_result.is_valid:
            raise ValidationError(f"Invalid phone number: {', '.join(validation_result.validation_errors)}")

        normalized = validation_result.normalized_number

        if format_type == 'international':
            return normalized
        elif format_type == 'national':
            # Remove country code for national format
            if normalized.startswith('+221'):
                return normalized[4:]
            return normalized
        elif format_type == 'masked':
            # Mask for privacy (show first 4 and last 2 digits)
            if len(normalized) > 6:
                return normalized[:4] + '*' * (len(normalized) - 6) + normalized[-2:]
            else:
                return '*' * len(normalized)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    def validate_multiple_numbers(self, phone_numbers: List[str]) -> List[PhoneNumberInfo]:
        """
        Validate multiple phone numbers.

        Args:
            phone_numbers: List of phone numbers to validate

        Returns:
            List of PhoneNumberInfo results
        """
        results = []
        for number in phone_numbers:
            try:
                result = self.validate_phone_number(number, 'SN')
                results.append(result)
            except ValidationError as e:
                # Create invalid result for validation errors
                results.append(PhoneNumberInfo(
                    original_number=number,
                    normalized_number=number,
                    country_code='UNKNOWN',
                    is_valid=False,
                    validation_errors=[str(e)]
                ))
        return results

    def get_validation_statistics(self, phone_numbers: List[str]) -> Dict[str, any]:
        """
        Get validation statistics for a list of phone numbers.

        Args:
            phone_numbers: List of phone numbers

        Returns:
            Validation statistics
        """
        results = self.validate_multiple_numbers(phone_numbers)

        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        # Count by carrier
        carrier_counts = {}
        for result in results:
            if result.carrier:
                carrier_counts[result.carrier] = carrier_counts.get(result.carrier, 0) + 1

        # Count by phone type
        type_counts = {}
        for result in results:
            if result.phone_type:
                type_counts[result.phone_type] = type_counts.get(result.phone_type, 0) + 1

        return {
            'total_numbers': total,
            'valid_numbers': valid,
            'invalid_numbers': invalid,
            'validation_rate': round((valid / total * 100) if total > 0 else 0, 2),
            'carrier_distribution': carrier_counts,
            'type_distribution': type_counts,
            'common_errors': self._get_common_errors(results)
        }

    def _get_common_errors(self, results: List[PhoneNumberInfo]) -> List[Dict[str, any]]:
        """Get common validation errors from results."""
        error_counts = {}
        for result in results:
            for error in result.validation_errors:
                error_counts[error] = error_counts.get(error, 0) + 1

        # Sort by frequency and return top errors
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'error': error, 'count': count} for error, count in sorted_errors[:5]]


# Global phone validation service instance
_phone_validation_service: Optional[PhoneValidationService] = None


def get_phone_validation_service() -> PhoneValidationService:
    """Get the global phone validation service instance."""
    global _phone_validation_service
    if _phone_validation_service is None:
        _phone_validation_service = PhoneValidationService()
    return _phone_validation_service


def validate_phone_number(phone_number: str, country_code: str = 'SN') -> PhoneNumberInfo:
    """Validate a phone number using the global service."""
    service = get_phone_validation_service()
    return service.validate_phone_number(phone_number, country_code)


def is_valid_senegal_mobile(phone_number: str) -> bool:
    """Check if phone number is a valid Senegal mobile number."""
    service = get_phone_validation_service()
    return service.is_senegal_mobile_number(phone_number)


def normalize_phone_number(phone_number: str) -> str:
    """Normalize phone number for storage."""
    service = get_phone_validation_service()
    return service.normalize_for_storage(phone_number)


def format_phone_number(phone_number: str, format_type: str = 'international') -> str:
    """Format phone number for display."""
    service = get_phone_validation_service()
    return service.format_for_display(phone_number, format_type)


def get_carrier_information(phone_number: str) -> Optional[Dict[str, str]]:
    """Get carrier information for a phone number."""
    service = get_phone_validation_service()
    return service.get_carrier_info(phone_number)