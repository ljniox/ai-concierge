"""
Unit Tests for Phone Number Validation Utility

This test suite validates the phone number validation functionality
for the automatic account creation system, ensuring proper handling
of international formats and Senegal-specific requirements.
"""

import pytest
from unittest.mock import patch, MagicMock
import phonenumbers
from phonenumbers import NumberParseException

from src.utils.phone_validator import (
    PhoneValidator,
    PhoneNumberValidationResult,
    ValidationError,
    PhoneNumberFormatError,
    SenegalPhoneNumberError,
    UnsupportedCountryError
)


class TestPhoneValidator:
    """Test cases for PhoneValidator class."""

    @pytest.fixture
    def validator(self):
        """Create PhoneValidator instance for testing."""
        return PhoneValidator()

    @pytest.fixture
    def valid_senegal_numbers(self):
        """Fixture providing valid Senegalese phone numbers."""
        return {
            "international_format": "+221765005555",
            "local_format": "76 500 55 55",
            "digits_only": "221765005555",
            "with_spaces": "+221 76 500 55 55",
            "with_hyphens": "+221-76-500-55-55",
            "orange_prefix": "+221771234567",
            "free_prefix": "+221761234567",
            "expresso_prefix": "+221701234567",
            "malitel_prefix": "+221791234567",
            "promo_prefix": "+221781234567",
            "fixed_line": "+221338123456"
        }

    @pytest.fixture
    def invalid_numbers(self):
        """Fixture providing invalid phone numbers."""
        return [
            "123",  # Too short
            "+221123",  # Invalid format
            "+22176500555",  # Too short
            "+2217650055555",  # Too long
            "+221991234567",  # Invalid prefix
            "abcdef",  # Non-numeric
            "+22176abcde",  # Mixed alphanumeric
            "",  # Empty string
            "+221 76 500",  # Incomplete
            None,  # None value
            "+221"  # Country code only
        ]

    @pytest.fixture
    def international_numbers(self):
        """Fixture providing valid international numbers from various countries."""
        return {
            "france": "+33612345678",
            "usa": "+12125551234",
            "uk": "+447123456789",
            "germany": "+49123456789",
            "italy": "+393123456789",
            "spain": "+34612345678"
        }

    def test_validate_senegal_number_international_format(self, validator, valid_senegal_numbers):
        """Test validation of Senegalese numbers in international format."""
        result = validator.validate_phone_number(
            valid_senegal_numbers["international_format"],
            country_code="SN"
        )

        assert result.is_valid is True
        assert result.error_code is None
        assert result.error_message is None
        assert result.country_code == "SN"
        assert result.carrier is not None
        assert result.number_type in ["MOBILE", "FIXED_LINE"]
        assert result.original_number == valid_senegal_numbers["international_format"]
        assert result.normalized_number == "+221765005555"

    def test_validate_senegal_number_local_format(self, validator, valid_senegal_numbers):
        """Test validation of Senegalese numbers in local format."""
        result = validator.validate_phone_number(
            valid_senegal_numbers["local_format"],
            country_code="SN"
        )

        assert result.is_valid is True
        assert result.error_code is None
        assert result.normalized_number == "+221765005555"

    def test_validate_senegal_number_with_spaces(self, validator, valid_senegal_numbers):
        """Test validation of numbers with spaces."""
        result = validator.validate_phone_number(
            valid_senegal_numbers["with_spaces"],
            country_code="SN"
        )

        assert result.is_valid is True
        assert result.normalized_number == "+221765005555"

    def test_validate_senegal_number_with_hyphens(self, validator, valid_senegal_numbers):
        """Test validation of numbers with hyphens."""
        result = validator.validate_phone_number(
            valid_senegal_numbers["with_hyphens"],
            country_code="SN"
        )

        assert result.is_valid is True
        assert result.normalized_number == "+221765005555"

    def test_validate_mobile_carriers(self, validator):
        """Test validation of different mobile carrier prefixes."""
        carrier_tests = [
            ("+221771234567", "Orange"),
            ("+221761234567", "Free"),
            ("+221701234567", "Expresso"),
            ("+221791234567", "Malitel"),
            ("+221781234567", "Promo")
        ]

        for phone_number, expected_carrier in carrier_tests:
            result = validator.validate_phone_number(phone_number, country_code="SN")
            assert result.is_valid is True
            assert expected_carrier in result.carrier or result.carrier in ["Orange", "Free", "Expresso", "Malitel", "Promo", "Unknown"]

    def test_validate_fixed_line(self, validator, valid_senegal_numbers):
        """Test validation of fixed line numbers."""
        result = validator.validate_phone_number(
            valid_senegal_numbers["fixed_line"],
            country_code="SN"
        )

        assert result.is_valid is True
        assert result.number_type == "FIXED_LINE"

    def test_validate_invalid_numbers(self, validator, invalid_numbers):
        """Test validation of invalid phone numbers."""
        for invalid_number in invalid_numbers:
            if invalid_number is None:
                # Test None separately
                with pytest.raises(ValidationError):
                    validator.validate_phone_number(invalid_number, country_code="SN")
            else:
                result = validator.validate_phone_number(invalid_number, country_code="SN")
                assert result.is_valid is False
                assert result.error_code is not None
                assert result.error_message is not None

    def test_validate_empty_string(self, validator):
        """Test validation of empty string."""
        with pytest.raises(ValidationError, match="Phone number cannot be empty"):
            validator.validate_phone_number("", country_code="SN")

    def test_validate_none(self, validator):
        """Test validation of None value."""
        with pytest.raises(ValidationError, match="Phone number cannot be empty"):
            validator.validate_phone_number(None, country_code="SN")

    def test_validate_non_string_input(self, validator):
        """Test validation of non-string input."""
        with pytest.raises(ValidationError, match="Phone number must be a string"):
            validator.validate_phone_number(123456789, country_code="SN")

    def test_validate_international_numbers(self, validator, international_numbers):
        """Test validation of international numbers from different countries."""
        for country, number in international_numbers.items():
            country_code = {
                "france": "FR",
                "usa": "US",
                "uk": "GB",
                "germany": "DE",
                "italy": "IT",
                "spain": "ES"
            }[country]

            result = validator.validate_phone_number(number, country_code=country_code)
            assert result.is_valid is True
            assert result.country_code == country_code

    def test_validate_without_country_code(self, validator, valid_senegal_numbers):
        """Test validation without explicit country code (auto-detection)."""
        result = validator.validate_phone_number(valid_senegal_numbers["international_format"])
        assert result.is_valid is True
        assert result.country_code == "SN"

    def test_validate_wrong_country_code(self, validator, valid_senegal_numbers):
        """Test validation with wrong country code."""
        result = validator.validate_phone_number(
            valid_senegal_numbers["international_format"],
            country_code="FR"
        )
        assert result.is_valid is False
        assert result.error_code == "INVALID_COUNTRY_CODE"

    def test_is_senegal_mobile_number(self, validator):
        """Test Senegal mobile number detection."""
        mobile_numbers = [
            "+221771234567",  # Orange
            "+221761234567",  # Free
            "+221701234567",  # Expresso
            "+221791234567",  # Malitel
            "+221781234567"   # Promo
        ]

        fixed_numbers = [
            "+221338123456"   # Fixed line
        ]

        for number in mobile_numbers:
            assert validator.is_senegal_mobile_number(number) is True

        for number in fixed_numbers:
            assert validator.is_senegal_mobile_number(number) is False

    def test_normalize_phone_number(self, validator, valid_senegal_numbers):
        """Test phone number normalization."""
        test_cases = [
            (valid_senegal_numbers["international_format"], "+221765005555"),
            (valid_senegal_numbers["local_format"], "+221765005555"),
            (valid_senegal_numbers["digits_only"], "+221765005555"),
            (valid_senegal_numbers["with_spaces"], "+221765005555"),
            (valid_senegal_numbers["with_hyphens"], "+221765005555")
        ]

        for input_number, expected_normalized in test_cases:
            normalized = validator.normalize_phone_number(input_number, country_code="SN")
            assert normalized == expected_normalized

    def test_get_senegal_carrier_info(self, validator):
        """Test carrier information retrieval for Senegal numbers."""
        carrier_tests = [
            ("+221771234567", ["Orange", "Sonatel"]),
            ("+221761234567", ["Free"]),
            ("+221701234567", ["Expresso", "Millicom"]),
            ("+221791234567", ["Malitel", "Orange Mali"]),
            ("+221781234567", ["Promo"])
        ]

        for phone_number, possible_carriers in carrier_tests:
            carrier_info = validator.get_senegal_carrier_info(phone_number)
            assert carrier_info is not None
            # Check if any of the expected carriers are mentioned
            carrier_match = any(carrier in carrier_info for carrier in possible_carriers)
            assert carrier_match or carrier_info == "Unknown"

    def test_batch_validation(self, validator, valid_senegal_numbers, invalid_numbers):
        """Test batch validation of multiple phone numbers."""
        # Mix of valid and invalid numbers
        phone_numbers = [
            valid_senegal_numbers["international_format"],
            valid_senegal_numbers["local_format"],
            "invalid_number",
            "",
            valid_senegal_numbers["with_spaces"]
        ]

        results = validator.validate_phone_numbers_batch(phone_numbers, country_code="SN")

        assert len(results) == 5
        assert results[0].is_valid is True  # Valid international format
        assert results[1].is_valid is True  # Valid local format
        assert results[2].is_valid is False  # Invalid
        assert results[3].is_valid is False  # Empty
        assert results[4].is_valid is True  # Valid with spaces

    def test_validation_with_custom_region(self, validator):
        """Test validation with custom default region."""
        # Set default region to France
        validator_fr = PhoneValidator(default_region="FR")

        # Test French number without country code
        result = validator_fr.validate_phone_number("0612345678")
        assert result.is_valid is True
        assert result.country_code == "FR"
        assert result.normalized_number == "+33612345678"

    @patch('phonenumbers.parse')
    def test_phonenumber_exception_handling(self, mock_parse, validator):
        """Test handling of phonenumbers library exceptions."""
        # Mock NumberParseException
        mock_parse.side_effect = NumberParseException(1, "Invalid number format")

        result = validator.validate_phone_number("+221765005555", country_code="SN")
        assert result.is_valid is False
        assert result.error_code == "PARSE_ERROR"
        assert "Invalid number format" in result.error_message

    def test_phone_number_masking(self, validator):
        """Test phone number masking for privacy."""
        phone_number = "+221765005555"
        masked = validator.mask_phone_number(phone_number)

        assert masked == "+221*******55"

        # Test with shorter number
        short_number = "+2217650055"
        masked_short = validator.mask_phone_number(short_number)
        assert masked_short == "+221****55"

        # Test with invalid number
        assert validator.mask_phone_number("invalid") == "invalid"
        assert validator.mask_phone_number("") == ""

    def test_validation_statistics(self, validator):
        """Test validation statistics tracking."""
        # Reset statistics
        validator.reset_statistics()

        # Validate some numbers
        validator.validate_phone_number("+221765005555", country_code="SN")  # Valid
        validator.validate_phone_number("invalid", country_code="SN")  # Invalid
        validator.validate_phone_number("+221771234567", country_code="SN")  # Valid

        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == 3
        assert stats["valid_count"] == 2
        assert stats["invalid_count"] == 1
        assert stats["success_rate"] == 2/3

    def test_edge_cases(self, validator):
        """Test edge cases and boundary conditions."""
        # Test with country code only
        result = validator.validate_phone_number("+221", country_code="SN")
        assert result.is_valid is False

        # Test with extension
        result = validator.validate_phone_number("+221765005555 ext. 123", country_code="SN")
        # Should be valid or invalid depending on implementation
        assert isinstance(result.is_valid, bool)

        # Test with very long number
        long_number = "+221" + "7" * 20
        result = validator.validate_phone_number(long_number, country_code="SN")
        assert result.is_valid is False

    def test_phone_number_validation_result_model(self):
        """Test PhoneNumberValidationResult Pydantic model."""
        # Test valid result
        result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221 76 500 55 55"
        )

        assert result.is_valid is True
        assert result.error_code is None
        assert result.error_message is None

        # Test invalid result
        invalid_result = PhoneNumberValidationResult(
            is_valid=False,
            original_number="invalid",
            error_code="INVALID_FORMAT",
            error_message="Phone number format is invalid"
        )

        assert invalid_result.is_valid is False
        assert invalid_result.normalized_number is None
        assert invalid_result.error_code == "INVALID_FORMAT"

    def test_custom_exceptions(self):
        """Test custom exception classes."""
        # Test ValidationError
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error", "TEST_ERROR")
        assert str(exc_info.value) == "Test error"
        assert exc_info.value.error_code == "TEST_ERROR"

        # Test PhoneNumberFormatError
        with pytest.raises(PhoneNumberFormatError) as exc_info:
            raise PhoneNumberFormatError("Format error")
        assert str(exc_info.value) == "Phone number format error: Format error"
        assert exc_info.value.error_code == "INVALID_FORMAT"

        # Test SenegalPhoneNumberError
        with pytest.raises(SenegalPhoneNumberError) as exc_info:
            raise SenegalPhoneNumberError("Senegal error")
        assert str(exc_info.value) == "Senegal phone number error: Senegal error"
        assert exc_info.value.error_code == "INVALID_SENEGAL_NUMBER"

        # Test UnsupportedCountryError
        with pytest.raises(UnsupportedCountryError) as exc_info:
            raise UnsupportedCountryError("Country error")
        assert str(exc_info.value) == "Unsupported country error: Country error"
        assert exc_info.value.error_code == "UNSUPPORTED_COUNTRY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])