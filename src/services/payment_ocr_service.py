"""
Payment Receipt OCR Processing Service

Handles OCR processing of mobile money payment receipts.
Extracts payment references, amounts, dates, and transaction details.

Features:
- Multiple receipt format support
- Payment reference extraction
- Amount validation
- Date extraction and validation
- Provider detection
- Confidence scoring

Constitution Principle: Automated payment receipt validation
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
import os

from .ocr_service import get_ocr_service
from .mobile_money_service import get_mobile_money_service, PaymentProvider
from ..utils.exceptions import ValidationError, OCRError

logger = logging.getLogger(__name__)

class PaymentReceiptOCR:
    """Service for OCR processing of payment receipts."""

    def __init__(self):
        self.ocr_service = get_ocr_service()
        self.mobile_money_service = get_mobile_money_service()
        self.min_confidence = float(os.getenv('PAYMENT_OCR_CONFIDENCE_THRESHOLD', '0.75'))

        # Patterns for extracting payment information
        self.patterns = {
            'payment_reference': {
                'orange': [
                    r'(?:Référence|Ref|Reference|ID)[:\s]+(OM\d{8,12})',
                    r'(OM\d{8,12})',
                    r'(?:Transaction|Trans)[:\s]+(OM\d{8,12})'
                ],
                'wave': [
                    r'(?:Référence|Ref|Reference|ID)[:\s]+(WV\d{8,15})',
                    r'(WV\d{8,15})',
                    r'(?:Transaction|Trans)[:\s]+(WV\d{8,15})'
                ],
                'free_money': [
                    r'(?:Référence|Ref|Reference|ID)[:\s]+(FM\d{8,12})',
                    r'(FM\d{8,12})',
                    r'(?:Transaction|Trans)[:\s]+(FM\d{8,12})'
                ],
                'wari': [
                    r'(?:Référence|Ref|Reference|ID)[:\s]+(WR\d{8,12})',
                    r'(WR\d{8,12})',
                    r'(?:Transaction|Trans)[:\s]+(WR\d{8,12})'
                ],
                'coris': [
                    r'(?:Référence|Ref|Reference|ID)[:\s]+(CM\d{8,12})',
                    r'(CM\d{8,12})',
                    r'(?:Transaction|Trans)[:\s]+(CM\d{8,12})'
                ],
                'general': [
                    r'(?:Référence|Ref|Reference|ID)[:\s]+([A-Z]{2}\d{8,15})',
                    r'([A-Z]{2}\d{8,15})',
                    r'(?:Transaction|Trans)[:\s]+([A-Z]{2}\d{8,15})'
                ]
            },
            'amount': [
                r'(?:Montant|Amount|Somme)[:\s]*([0-9]+(?:[.,][0-9]{1,3})?)\s*(?:FCFA|XOF|CFA)',
                r'([0-9]+(?:[.,][0-9]{1,3})?)\s*(?:FCFA|XOF|CFA)',
                r'(?:Montant|Amount|Somme)[:\s]*([0-9]+(?:[.,][0-9]{1,3})?)',
                r'(?:Payé|Paid)[:\s]*([0-9]+(?:[.,][0-9]{1,3})?)\s*(?:FCFA|XOF|CFA)'
            ],
            'date': [
                r'(?:Date|Le)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
                r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
                r'(?:Date|Le)[:\s]*([0-9]{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+[0-9]{4})',
                r'([0-9]{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+[0-9]{4})'
            ],
            'phone_number': [
                r'(?:Téléphone|Tel|Phone|Contact)[:\s]*([+]?[0-9]{9,15})',
                r'(?:De|From)[:\s]*([+]?221[0-9]{9})',
                r'([+]?221[0-9]{9})',
                r'([0-9]{9,15})'
            ],
            'provider_name': [
                r'(Orange\s+Money|Orange)',
                r'(Wave)',
                r'(Free\s+Money|Free)',
                r'(Wari)',
                r'(Coris\s+Money|Coris)',
                r'(MTN\s+Mobile\s+Money|MTN)'
            ]
        }

        # Common receipt keywords
        self.receipt_keywords = {
            'confirmation': [
                'confirmation', 'confirmé', 'validé', 'succès', 'success',
                'effectué', 'réussi', 'terminé', 'complété'
            ],
            'payment': [
                'paiement', 'payment', 'transfert', 'transfer', 'envoi',
                'envoyé', 'sent', 'reçu', 'received'
            ],
            'transaction': [
                'transaction', 'opération', 'operation', 'transfert'
            ]
        }

    async def process_payment_receipt(
        self,
        image_path: str,
        expected_amount: Optional[Decimal] = None,
        expected_provider: Optional[PaymentProvider] = None
    ) -> Dict[str, Any]:
        """
        Process a payment receipt image and extract payment information.

        Args:
            image_path: Path to receipt image
            expected_amount: Expected payment amount (for validation)
            expected_provider: Expected payment provider (for validation)

        Returns:
            Dict: Extracted payment information
        """
        try:
            # Perform OCR on the receipt
            ocr_result = await self.ocr_service.extract_text_from_image(image_path)

            if not ocr_result['text']:
                raise OCRError("No text extracted from receipt image")

            extracted_text = ocr_result['text']
            confidence = ocr_result['confidence']

            logger.info(f"OCR extracted {len(extracted_text)} characters with confidence {confidence}")

            # Extract payment information
            payment_info = await self._extract_payment_info(
                extracted_text, expected_amount, expected_provider
            )

            # Validate extracted information
            validation_result = await self._validate_extracted_info(
                payment_info, expected_amount, expected_provider
            )

            # Calculate overall confidence
            overall_confidence = min(confidence, validation_result['confidence'])

            result = {
                'success': True,
                'extracted_text': extracted_text,
                'ocr_confidence': confidence,
                'payment_info': payment_info,
                'validation': validation_result,
                'overall_confidence': overall_confidence,
                'processed_at': datetime.utcnow().isoformat()
            }

            logger.info(f"Payment receipt processed successfully with confidence {overall_confidence}")
            return result

        except Exception as e:
            logger.error(f"Failed to process payment receipt: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }

    async def _extract_payment_info(
        self,
        text: str,
        expected_amount: Optional[Decimal] = None,
        expected_provider: Optional[PaymentProvider] = None
    ) -> Dict[str, Any]:
        """Extract payment information from OCR text."""
        payment_info = {
            'payment_reference': None,
            'provider': None,
            'amount': None,
            'currency': None,
            'date': None,
            'phone_number': None,
            'provider_name': None,
            'confidence_scores': {}
        }

        text_upper = text.upper()

        # Extract payment reference
        ref_info = await self._extract_payment_reference(text_upper, expected_provider)
        if ref_info['reference']:
            payment_info['payment_reference'] = ref_info['reference']
            payment_info['provider'] = ref_info['provider']
            payment_info['confidence_scores']['reference'] = ref_info['confidence']

        # Extract amount
        amount_info = await self._extract_amount(text)
        if amount_info['amount']:
            payment_info['amount'] = amount_info['amount']
            payment_info['currency'] = amount_info['currency']
            payment_info['confidence_scores']['amount'] = amount_info['confidence']

        # Extract date
        date_info = await self._extract_date(text)
        if date_info['date']:
            payment_info['date'] = date_info['date']
            payment_info['confidence_scores']['date'] = date_info['confidence']

        # Extract phone number
        phone_info = await self._extract_phone_number(text)
        if phone_info['phone']:
            payment_info['phone_number'] = phone_info['phone']
            payment_info['confidence_scores']['phone'] = phone_info['confidence']

        # Extract provider name
        provider_name_info = await self._extract_provider_name(text)
        if provider_name_info['provider_name']:
            payment_info['provider_name'] = provider_name_info['provider_name']
            payment_info['confidence_scores']['provider_name'] = provider_name_info['confidence']

        return payment_info

    async def _extract_payment_reference(
        self,
        text: str,
        expected_provider: Optional[PaymentProvider] = None
    ) -> Dict[str, Any]:
        """Extract payment reference with provider detection."""
        best_match = {'reference': None, 'provider': None, 'confidence': 0.0}

        # Try specific provider patterns first
        if expected_provider:
            provider_key = expected_provider.value
            if provider_key in self.patterns['payment_reference']:
                patterns = self.patterns['payment_reference'][provider_key]
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        ref = match.group(1)
                        is_valid, detected_provider = self.mobile_money_service.validate_payment_reference(ref, expected_provider)
                        if is_valid:
                            confidence = self._calculate_reference_confidence(ref, text, match)
                            if confidence > best_match['confidence']:
                                best_match = {
                                    'reference': ref,
                                    'provider': detected_provider,
                                    'confidence': confidence
                                }

        # Try all patterns if no match found
        if not best_match['reference']:
            for provider_key, patterns in self.patterns['payment_reference'].items():
                if provider_key == 'general':
                    continue  # Try general patterns last

                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        ref = match.group(1)
                        is_valid, detected_provider = self.mobile_money_service.validate_payment_reference(ref)
                        if is_valid:
                            confidence = self._calculate_reference_confidence(ref, text, match)
                            if confidence > best_match['confidence']:
                                best_match = {
                                    'reference': ref,
                                    'provider': detected_provider,
                                    'confidence': confidence
                                }

        # Try general patterns as last resort
        if not best_match['reference']:
            for pattern in self.patterns['payment_reference']['general']:
                matches = re.finditer(pattern, text)
                for match in matches:
                    ref = match.group(1)
                    is_valid, detected_provider = self.mobile_money_service.validate_payment_reference(ref)
                    if is_valid:
                        confidence = self._calculate_reference_confidence(ref, text, match)
                        if confidence > best_match['confidence']:
                            best_match = {
                                'reference': ref,
                                'provider': detected_provider,
                                'confidence': confidence
                            }

        return best_match

    async def _extract_amount(self, text: str) -> Dict[str, Any]:
        """Extract payment amount."""
        best_match = {'amount': None, 'currency': None, 'confidence': 0.0}

        for pattern in self.patterns['amount']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean and parse amount
                    amount_str = match.group(1).replace(',', '.')
                    amount = Decimal(amount_str)

                    # Look for currency in the match
                    currency_match = re.search(r'(FCFA|XOF|CFA)', match.group(0), re.IGNORECASE)
                    currency = currency_match.group(1).upper() if currency_match else 'FCFA'

                    # Calculate confidence based on format and context
                    confidence = self._calculate_amount_confidence(amount, text, match)

                    if confidence > best_match['confidence']:
                        best_match = {
                            'amount': amount,
                            'currency': currency,
                            'confidence': confidence
                        }

                except (InvalidOperation, ValueError):
                    continue

        return best_match

    async def _extract_date(self, text: str) -> Dict[str, Any]:
        """Extract transaction date."""
        best_match = {'date': None, 'confidence': 0.0}

        # French month mapping
        french_months = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }

        english_months = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }

        for pattern in self.patterns['date']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = None

                try:
                    # Try different date formats
                    if re.match(r'[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}', date_str):
                        # Numeric format
                        parts = re.split(r'[/-]', date_str)
                        if len(parts) == 3:
                            day, month = parts[0], parts[1]
                            year = parts[2]
                            if len(year) == 2:
                                year = '20' + year
                            parsed_date = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", "%Y-%m-%d")

                    elif any(month in date_str.lower() for month in french_months.keys()):
                        # French month format
                        for month_name, month_num in french_months.items():
                            if month_name in date_str.lower():
                                parts = date_str.split()
                                if len(parts) >= 3:
                                    day = parts[0]
                                    year = parts[2]
                                    parsed_date = datetime.strptime(f"{year}-{month_num}-{day.zfill(2)}", "%Y-%m-%d")
                                break

                    elif any(month in date_str.lower() for month in english_months.keys()):
                        # English month format
                        for month_name, month_num in english_months.items():
                            if month_name in date_str.lower():
                                parts = date_str.split()
                                if len(parts) >= 3:
                                    day = parts[0]
                                    year = parts[2]
                                    parsed_date = datetime.strptime(f"{year}-{month_num}-{day.zfill(2)}", "%Y-%m-%d")
                                break

                    if parsed_date:
                        # Validate date is reasonable (not too old or future)
                        today = datetime.now()
                        if abs((parsed_date - today).days) <= 365:  # Within 1 year
                            confidence = self._calculate_date_confidence(parsed_date, text, match)
                            if confidence > best_match['confidence']:
                                best_match = {
                                    'date': parsed_date.isoformat(),
                                    'confidence': confidence
                                }

                except ValueError:
                    continue

        return best_match

    async def _extract_phone_number(self, text: str) -> Dict[str, Any]:
        """Extract phone number from receipt."""
        best_match = {'phone': None, 'confidence': 0.0}

        for pattern in self.patterns['phone_number']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                phone = match.group(1)

                # Clean phone number
                phone = re.sub(r'[^\d+]', '', phone)

                # Validate Senegal phone number format
                if len(phone) >= 9:
                    if not phone.startswith('+221') and len(phone) == 9:
                        phone = '+221' + phone
                    elif len(phone) > 9 and not phone.startswith('+'):
                        phone = '+' + phone

                    confidence = self._calculate_phone_confidence(phone, text, match)
                    if confidence > best_match['confidence']:
                        best_match = {
                            'phone': phone,
                            'confidence': confidence
                        }

        return best_match

    async def _extract_provider_name(self, text: str) -> Dict[str, Any]:
        """Extract provider name from receipt."""
        best_match = {'provider_name': None, 'confidence': 0.0}

        for pattern in self.patterns['provider_name']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                provider_name = match.group(1).strip()
                confidence = self._calculate_provider_confidence(provider_name, text, match)

                if confidence > best_match['confidence']:
                    best_match = {
                        'provider_name': provider_name,
                        'confidence': confidence
                    }

        return best_match

    async def _validate_extracted_info(
        self,
        payment_info: Dict[str, Any],
        expected_amount: Optional[Decimal] = None,
        expected_provider: Optional[PaymentProvider] = None
    ) -> Dict[str, Any]:
        """Validate extracted payment information."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'confidence': 1.0,
            'validations': {}
        }

        # Validate payment reference
        if payment_info['payment_reference']:
            ref_valid, detected_provider = self.mobile_money_service.validate_payment_reference(
                payment_info['payment_reference'], expected_provider
            )
            validation_result['validations']['reference'] = {
                'valid': ref_valid,
                'detected_provider': detected_provider.value if detected_provider else None
            }
            if not ref_valid:
                validation_result['errors'].append("Invalid payment reference format")
                validation_result['is_valid'] = False
        else:
            validation_result['errors'].append("No payment reference found")
            validation_result['is_valid'] = False

        # Validate amount
        if payment_info['amount']:
            if expected_amount:
                if payment_info['amount'] == expected_amount:
                    validation_result['validations']['amount'] = {'valid': True, 'match': True}
                else:
                    validation_result['validations']['amount'] = {
                        'valid': False,
                        'expected': float(expected_amount),
                        'found': float(payment_info['amount'])
                    }
                    validation_result['errors'].append(f"Amount mismatch: expected {expected_amount}, found {payment_info['amount']}")
                    validation_result['is_valid'] = False
            else:
                validation_result['validations']['amount'] = {'valid': True, 'match': None}
        else:
            validation_result['errors'].append("No amount found")
            validation_result['is_valid'] = False

        # Validate provider consistency
        if payment_info['provider'] and expected_provider:
            if payment_info['provider'] == expected_provider:
                validation_result['validations']['provider'] = {'valid': True, 'match': True}
            else:
                validation_result['validations']['provider'] = {
                    'valid': False,
                    'expected': expected_provider.value,
                    'found': payment_info['provider'].value
                }
                validation_result['warnings'].append(f"Provider mismatch: expected {expected_provider.value}, found {payment_info['provider'].value}")

        # Validate date recency
        if payment_info['date']:
            try:
                receipt_date = datetime.fromisoformat(payment_info['date'].replace('Z', '+00:00'))
                days_old = (datetime.utcnow() - receipt_date.replace(tzinfo=None)).days

                if days_old > 30:
                    validation_result['warnings'].append(f"Receipt is {days_old} days old")
                elif days_old < 0:
                    validation_result['errors'].append("Receipt date is in the future")
                    validation_result['is_valid'] = False

                validation_result['validations']['date'] = {
                    'valid': True,
                    'days_old': days_old
                }
            except ValueError:
                validation_result['errors'].append("Invalid date format")
                validation_result['is_valid'] = False
        else:
            validation_result['warnings'].append("No date found")

        # Calculate overall validation confidence
        if payment_info['confidence_scores']:
            avg_confidence = sum(payment_info['confidence_scores'].values()) / len(payment_info['confidence_scores'])
            validation_result['confidence'] = avg_confidence

        return validation_result

    def _calculate_reference_confidence(self, reference: str, text: str, match) -> float:
        """Calculate confidence score for payment reference extraction."""
        base_confidence = 0.8

        # Higher confidence for exact format matches
        if re.match(r'^[A-Z]{2}\d{8,15}$', reference):
            base_confidence += 0.1

        # Check for reference keywords nearby
        context = text[max(0, match.start()-50):match.end()+50]
        if any(keyword in context.lower() for keyword in ['référence', 'ref', 'reference', 'id', 'transaction']):
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _calculate_amount_confidence(self, amount: Decimal, text: str, match) -> float:
        """Calculate confidence score for amount extraction."""
        base_confidence = 0.7

        # Check for amount keywords nearby
        context = text[max(0, match.start()-30):match.end()+30]
        if any(keyword in context.lower() for keyword in ['montant', 'amount', 'somme', 'payé', 'paid']):
            base_confidence += 0.15

        # Check for currency indicator
        if 'fcfa' in context.lower() or 'xof' in context.lower():
            base_confidence += 0.15

        return min(base_confidence, 1.0)

    def _calculate_date_confidence(self, date: datetime, text: str, match) -> float:
        """Calculate confidence score for date extraction."""
        base_confidence = 0.7

        # Check for date keywords nearby
        context = text[max(0, match.start()-20):match.end()+20]
        if any(keyword in context.lower() for keyword in ['date', 'le', 'the']):
            base_confidence += 0.2

        # Higher confidence for recent dates
        days_old = abs((datetime.utcnow() - date).days)
        if days_old <= 7:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _calculate_phone_confidence(self, phone: str, text: str, match) -> float:
        """Calculate confidence score for phone number extraction."""
        base_confidence = 0.6

        # Check for phone keywords nearby
        context = text[max(0, match.start()-20):match.end()+20]
        if any(keyword in context.lower() for keyword in ['téléphone', 'tel', 'phone', 'contact', 'de', 'from']):
            base_confidence += 0.2

        # Higher confidence for proper Senegal format
        if phone.startswith('+221') and len(phone) == 13:
            base_confidence += 0.2

        return min(base_confidence, 1.0)

    def _calculate_provider_confidence(self, provider_name: str, text: str, match) -> float:
        """Calculate confidence score for provider name extraction."""
        base_confidence = 0.8

        # Higher confidence for exact provider names
        known_providers = ['orange money', 'wave', 'free money', 'wari', 'coris money']
        if provider_name.lower() in known_providers:
            base_confidence += 0.2

        return min(base_confidence, 1.0)

# Global service instance
_payment_ocr_service = None

def get_payment_ocr_service() -> PaymentReceiptOCR:
    """Get the payment OCR service instance."""
    global _payment_ocr_service
    if _payment_ocr_service is None:
        _payment_ocr_service = PaymentReceiptOCR()
    return _payment_ocr_service