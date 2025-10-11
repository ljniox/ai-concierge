"""
OCR Service for French Document Processing

Implements EasyOCR integration for automatic data extraction from:
- Birth certificates (FR-003)
- Baptism certificates (FR-004)
- Transfer attestations (FR-005)
- Mobile Money receipts (FR-016)

Features:
- French language support
- Confidence scoring (70% threshold)
- Automatic field extraction
- Error handling and fallback

Research Decision: research.md#1 - EasyOCR with fallback to manual entry
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import easyocr
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
import os

from ..database.sqlite_manager import get_sqlite_manager
from ..models.document import Document, ExtractionData, StatutOCR, DocumentType
from ..utils.exceptions import OCRError, DocumentError
from ..services.audit_service import log_user_action

logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR service for French document processing.

    Uses EasyOCR for deep learning-based text extraction
    with French language support and confidence scoring.
    """

    def __init__(self):
        self.reader = None
        self.confidence_threshold = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', '0.70'))
        self.manager = get_sqlite_manager()
        self._initialize_reader()

    def _initialize_reader(self):
        """Initialize EasyOCR reader with French language support."""
        try:
            # Initialize reader with French and English (fallback)
            self.reader = easyocr.Reader(['fr', 'en'], gpu=False)
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR reader: {e}")
            raise OCRError(f"OCR service initialization failed: {e}")

    async def process_document(self, document_id: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Process a document with OCR extraction.

        Args:
            document_id: Document ID to process
            force_reprocess: Force reprocessing even if already processed

        Returns:
            Dict: Processing results

        Research Decision: research.md#1 - EasyOCR with confidence scoring
        """
        try:
            # Get document from database
            document = await self._get_document(document_id)
            if not document:
                raise DocumentError(f"Document not found: {document_id}")

            # Check if already processed
            if not force_reprocess and document.ocr_completed:
                logger.info(f"Document {document_id} already processed (status: {document.statut_ocr})")
                return {
                    "document_id": document_id,
                    "statut_ocr": document.statut_ocr,
                    "donnees_extraites": document.extraction_data.dict() if document.extraction_data else None,
                    "confiance_ocr": document.confiance_ocr,
                    "message": "Document already processed"
                }

            # Update status to processing
            await self._update_document_status(document_id, StatutOCR.EN_COURS)

            # Load and preprocess image
            image = await self._load_image(document.fichier_path)

            # Perform OCR
            ocr_results = await self._extract_text(image)

            # Extract structured data based on document type
            extraction_data = await self._extract_structured_data(
                document.type_document,
                ocr_results,
                document_id
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence(ocr_results)

            # Update document with results
            await self._save_extraction_results(
                document_id,
                extraction_data,
                confidence_score,
                StatutOCR.SUCCES if confidence_score >= self.confidence_threshold else StatutOCR.MANUEL
            )

            # Log the processing
            await log_user_action(
                user_id="system-ocr",
                action_type="process_document",
                entity_type="document",
                entity_id=document_id,
                details={
                    "document_type": document.type_document,
                    "confidence_score": confidence_score,
                    "processing_time": datetime.utcnow().isoformat()
                },
                statut_action="succes"
            )

            logger.info(f"OCR processing completed for document {document_id} (confidence: {confidence_score:.2f})")

            return {
                "document_id": document_id,
                "statut_ocr": StatutOCR.SUCCES if confidence_score >= self.confidence_threshold else StatutOCR.MANUEL,
                "donnees_extraites": extraction_data.dict(),
                "confiance_ocr": confidence_score,
                "message": "OCR processing completed successfully"
            }

        except Exception as e:
            logger.error(f"OCR processing failed for document {document_id}: {e}")

            # Update document status to error
            await self._update_document_status(document_id, StatutOCR.ECHEC, str(e))

            # Log the error
            await log_user_action(
                user_id="system-ocr",
                action_type="process_document",
                entity_type="document",
                entity_id=document_id,
                details={"error": str(e)},
                statut_action="echec",
                error_message=str(e)
            )

            raise OCRError(f"OCR processing failed: {e}")

    async def _get_document(self, document_id: str) -> Optional[Document]:
        """Get document from database."""
        try:
            query = "SELECT * FROM documents WHERE id = ?"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (document_id,))
                row = await cursor.fetchone()

            if row:
                return Document.from_db_row(dict(row))
            return None

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    async def _load_image(self, file_path: str) -> np.ndarray:
        """
        Load and preprocess image for OCR.

        Args:
            file_path: Path to image file

        Returns:
            np.ndarray: Preprocessed image array
        """
        try:
            # For now, assume local file path
            # In production, this would load from MinIO

            # Load image
            image = cv2.imread(file_path)
            if image is None:
                raise OCRError(f"Failed to load image: {file_path}")

            # Preprocessing for better OCR
            image = self._preprocess_image(image)

            return image

        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            raise OCRError(f"Image loading failed: {e}")

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to improve OCR accuracy.

        Args:
            image: Input image array

        Returns:
            np.ndarray: Preprocessed image
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Apply adaptive thresholding for better text detection
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )

            # Noise reduction
            denoised = cv2.medianBlur(binary, 3)

            return denoised

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image  # Return original image if preprocessing fails

    async def _extract_text(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract text using EasyOCR.

        Args:
            image: Preprocessed image array

        Returns:
            List of OCR results with bounding boxes and confidence
        """
        try:
            # Run OCR
            results = self.reader.readtext(image)

            # Convert to standard format
            ocr_results = []
            for (bbox, text, confidence) in results:
                ocr_results.append({
                    "text": text.strip(),
                    "confidence": float(confidence),
                    "bbox": bbox,
                    "is_valid": confidence >= 0.5  # Filter low-confidence text
                })

            # Filter valid results
            valid_results = [r for r in ocr_results if r["is_valid"]]

            logger.info(f"OCR extracted {len(valid_results)} text regions from {len(ocr_results)} total")
            return valid_results

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise OCRError(f"Text extraction failed: {e}")

    async def _extract_structured_data(self, document_type: str, ocr_results: List[Dict], document_id: str) -> ExtractionData:
        """
        Extract structured data based on document type.

        Args:
            document_type: Type of document
            ocr_results: Raw OCR results
            document_id: Document ID for logging

        Returns:
            ExtractionData: Structured extraction results
        """
        try:
            # Combine all text for analysis
            full_text = " ".join([r["text"] for r in ocr_results])

            if document_type == DocumentType.EXTRAIT_NAISSANCE:
                return await self._extract_birth_certificate_data(full_text, ocr_results)
            elif document_type == DocumentType.EXTRAIT_BAPTEME:
                return await self._extract_baptism_certificate_data(full_text, ocr_results)
            elif document_type == DocumentType.ATTESTATION_TRANSFERT:
                return await self._extract_transfer_attestation_data(full_text, ocr_results)
            elif document_type == DocumentType.PREUVE_PAIEMENT:
                return await self._extract_payment_receipt_data(full_text, ocr_results)
            else:
                logger.warning(f"Unknown document type: {document_type}")
                return ExtractionData()

        except Exception as e:
            logger.error(f"Structured data extraction failed for document {document_id}: {e}")
            return ExtractionData()

    async def _extract_birth_certificate_data(self, text: str, ocr_results: List[Dict]) -> ExtractionData:
        """
        Extract data from birth certificate (FR-003).

        Args:
            text: Combined OCR text
            ocr_results: Raw OCR results

        Returns:
            ExtractionData with birth certificate fields
        """
        import re

        data = ExtractionData()
        confidence_scores = {}

        # Extract name patterns (French format)
        name_patterns = [
            r'Nom\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Né\(e\)\s+le\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Nom\s+de famille\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.nom = match.group(1).strip()
                confidence_scores['nom'] = 0.8
                break

        # Extract first name patterns
        prenom_patterns = [
            r'Prénom\(s\)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Prénom\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Né\(e\)\s+(?:à|le)\s+.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in prenom_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.prenom = match.group(1).strip()
                confidence_scores['prenom'] = 0.8
                break

        # Extract birth date patterns (French formats: DD/MM/YYYY or DD MM YYYY)
        date_patterns = [
            r'Né\(e\)\s+le\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Né\(e\)\s+le\s+(\d{1,2}\s+\w+\s+\d{4})',
            r'Date\s+de\s+naissance\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'  # General date pattern
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                data.date_naissance = match.group(1).strip()
                confidence_scores['date_naissance'] = 0.9
                break

        # Extract birth place patterns
        place_patterns = [
            r'Né\(e\)\s+(?:à|le)\s+.*?à\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Lieu\s+de\s+naissance\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'À\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in place_patterns:
            match = re.search(pattern, text)
            if match:
                data.lieu_naissance = match.group(1).strip()
                confidence_scores['lieu_naissance'] = 0.7
                break

        data.confidence_scores = confidence_scores
        return data

    async def _extract_baptism_certificate_data(self, text: str, ocr_results: List[Dict]) -> ExtractionData:
        """
        Extract data from baptism certificate (FR-004).

        Args:
            text: Combined OCR text
            ocr_results: Raw OCR results

        Returns:
            ExtractionData with baptism certificate fields
        """
        import re

        data = ExtractionData()
        confidence_scores = {}

        # Extract baptism date patterns
        date_patterns = [
            r'Baptisé\(e\)\s+le\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Date\s+du\s+baptême\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Le\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.date_bapteme = match.group(1).strip()
                confidence_scores['date_bapteme'] = 0.9
                break

        # Extract parish patterns
        parish_patterns = [
            r'Paroisse\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Église\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'A\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in parish_patterns:
            match = re.search(pattern, text)
            if match:
                data.paroisse_bapteme = match.group(1).strip()
                confidence_scores['paroisse_bapteme'] = 0.8
                break

        # Extract priest name patterns
        priest_patterns = [
            r'Célébré\s+par\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Prêtre\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Abbé\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in priest_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.nom_pretre_bapteme = match.group(1).strip()
                confidence_scores['nom_pretre_bapteme'] = 0.7
                break

        data.confidence_scores = confidence_scores
        return data

    async def _extract_transfer_attestation_data(self, text: str, ocr_results: List[Dict]) -> ExtractionData:
        """
        Extract data from transfer attestation (FR-005).

        Args:
            text: Combined OCR text
            ocr_results: Raw OCR results

        Returns:
            ExtractionData with transfer attestation fields
        """
        import re

        data = ExtractionData()
        confidence_scores = {}

        # Extract origin parish patterns
        parish_patterns = [
            r'Paroisse\s+d\'origine\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Venant\s+de\s+la\s+paroisse\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Paroisse\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in parish_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.paroisse_origine = match.group(1).strip()
                confidence_scores['paroisse_origine'] = 0.8
                break

        # Extract previous catechism year patterns
        year_patterns = [
            r'Année\s+catéchétique\s*:?\s*(\d{4}-\d{4})',
            r'Catechisme\s*:?\s*(\d{4}-\d{4})',
            r'(\d{4}-\d{4})'
        ]

        for pattern in year_patterns:
            match = re.search(pattern, text)
            if match:
                data.annee_catechisme_precedente = match.group(1).strip()
                confidence_scores['annee_catechisme_precedente'] = 0.9
                break

        data.confidence_scores = confidence_scores
        return data

    async def _extract_payment_receipt_data(self, text: str, ocr_results: List[Dict]) -> ExtractionData:
        """
        Extract data from mobile money payment receipt (FR-016).

        Args:
            text: Combined OCR text
            ocr_results: Raw OCR results

        Returns:
            ExtractionData with payment receipt fields
        """
        import re

        data = ExtractionData()
        confidence_scores = {}

        # Extract transaction reference patterns
        ref_patterns = [
            r'Référence\s*:?\s*([A-Z0-9]+)',
            r'Transaction\s+ID\s*:?\s*([A-Z0-9]+)',
            r'Ref\s*:?\s*([A-Z0-9]+)'
        ]

        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.reference_document = match.group(1).strip()
                confidence_scores['reference_document'] = 0.9
                break

        data.confidence_scores = confidence_scores
        return data

    def _calculate_confidence(self, ocr_results: List[Dict]) -> float:
        """
        Calculate overall confidence score from OCR results.

        Args:
            ocr_results: Raw OCR results with confidence scores

        Returns:
            float: Overall confidence score (0.0-1.0)
        """
        if not ocr_results:
            return 0.0

        # Calculate average confidence
        total_confidence = sum(r["confidence"] for r in ocr_results)
        average_confidence = total_confidence / len(ocr_results)

        # Adjust based on text quality
        valid_text_ratio = sum(1 for r in ocr_results if r["is_valid"]) / len(ocr_results)

        # Combined confidence score
        overall_confidence = average_confidence * valid_text_ratio

        return min(1.0, max(0.0, overall_confidence))

    async def _update_document_status(self, document_id: str, status: str, error_message: str = None):
        """Update document processing status."""
        try:
            update_fields = ["statut_ocr = ?"]
            params = [status]

            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)

            params.append(document_id)

            query = f"""
            UPDATE documents
            SET {', '.join(update_fields)}
            WHERE id = ?
            """

            async with self.manager.get_connection('catechese') as conn:
                await conn.execute(query, params)
                await conn.commit()

            logger.info(f"Updated document {document_id} status to {status}")

        except Exception as e:
            logger.error(f"Failed to update document status: {e}")

    async def _save_extraction_results(self, document_id: str, extraction_data: ExtractionData, confidence: float, status: str):
        """Save OCR extraction results to database."""
        try:
            import json

            query = """
            UPDATE documents
            SET donnees_extraites = ?,
                confiance_ocr = ?,
                statut_ocr = ?,
                error_message = NULL
            WHERE id = ?
            """

            async with self.manager.get_connection('catechese') as conn:
                await conn.execute(query, (
                    json.dumps(extraction_data.dict()),
                    confidence,
                    status,
                    document_id
                ))
                await conn.commit()

            logger.info(f"Saved extraction results for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to save extraction results: {e}")


# Global OCR service instance
_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get global OCR service instance."""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance