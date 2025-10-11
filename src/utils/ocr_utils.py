"""
OCR Image Preprocessing Utilities

Advanced image processing for improved OCR accuracy on French documents.
Includes contrast enhancement, rotation correction, noise reduction, and text sharpening.

Research Decision: research.md#1 - EasyOCR with preprocessing
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class OCRPreprocessor:
    """
    Advanced OCR image preprocessing toolkit.

    Improves OCR accuracy through:
    - Contrast and brightness enhancement
    - Skew and rotation correction
    - Noise reduction and sharpening
    - Text region detection and enhancement
    """

    def __init__(self):
        self.processing_stats = {}

    def preprocess_for_ocr(self, image: np.ndarray, document_type: str = "general") -> np.ndarray:
        """
        Apply comprehensive preprocessing pipeline for OCR.

        Args:
            image: Input image as numpy array
            document_type: Type of document for specialized processing

        Returns:
            np.ndarray: Preprocessed image optimized for OCR
        """
        try:
            processed = image.copy()

            # Step 1: Basic cleanup
            processed = self._basic_cleanup(processed)

            # Step 2: Skew correction
            processed = self._correct_skew(processed)

            # Step 3: Contrast enhancement
            processed = self._enhance_contrast(processed)

            # Step 4: Noise reduction
            processed = self._reduce_noise(processed)

            # Step 5: Text sharpening
            processed = self._sharpen_text(processed)

            # Step 6: Document-specific processing
            processed = self._apply_document_specific_processing(processed, document_type)

            logger.debug(f"OCR preprocessing completed for {document_type} document")
            return processed

        except Exception as e:
            logger.warning(f"OCR preprocessing failed: {e}")
            return image  # Return original image if preprocessing fails

    def _basic_cleanup(self, image: np.ndarray) -> np.ndarray:
        """
        Apply basic image cleanup operations.

        Args:
            image: Input image

        Returns:
            np.ndarray: Cleaned image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Remove minor artifacts
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            return cleaned

        except Exception as e:
            logger.warning(f"Basic cleanup failed: {e}")
            return image

    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct image skew/rotation.

        Args:
            image: Input image

        Returns:
            np.ndarray: Skew-corrected image
        """
        try:
            # Convert to PIL for easier processing
            pil_image = Image.fromarray(image)

            # Get grayscale version for skew detection
            gray = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Hough line transform to detect lines
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

            if lines is not None:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:10]:  # Use first 10 lines
                    angle = theta * 180 / np.pi
                    if angle > 45:
                        angle = 90 - angle
                    elif angle < -45:
                        angle = 90 + angle
                    angles.append(angle)

                if angles:
                    avg_angle = np.mean(angles)

                    # Rotate image to correct skew
                    if abs(avg_angle) > 0.5:  # Only correct if skew is significant
                        rotated = pil_image.rotate(avg_angle, expand=True, fillcolor='white')
                        logger.debug(f"Corrected skew by {avg_angle:.2f} degrees")
                        return np.array(rotated.convert('L'))

            return image

        except Exception as e:
            logger.warning(f"Skew correction failed: {e}")
            return image

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast for better text visibility.

        Args:
            image: Input image

        Returns:
            np.ndarray: Contrast-enhanced image
        """
        try:
            # Convert to PIL
            pil_image = Image.fromarray(image)

            # Apply contrast enhancement
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = enhancer.enhance(2.0)  # Double the contrast

            # Apply brightness adjustment
            brightness = ImageEnhance.Brightness(enhanced)
            enhanced = brightness.enhance(1.1)  # Slightly increase brightness

            return np.array(enhanced)

        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}")
            return image

    def _reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Reduce noise in the image.

        Args:
            image: Input image

        Returns:
            np.ndarray: Noise-reduced image
        """
        try:
            # Apply median filter for noise reduction
            denoised = cv2.medianBlur(image, 3)

            # Apply bilateral filter for edge-preserving smoothing
            bilateral = cv2.bilateralFilter(denoised, 9, 75, 75)

            return bilateral

        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return image

    def _sharpen_text(self, image: np.ndarray) -> np.ndarray:
        """
        Sharpen text edges for better OCR recognition.

        Args:
            image: Input image

        Returns:
            np.ndarray: Sharpened image
        """
        try:
            # Create sharpening kernel
            kernel = np.array([
                [-1, -1, -1],
                [-1, 9, -1],
                [-1, -1, -1]
            ])

            # Apply sharpening
            sharpened = cv2.filter2D(image, -1, kernel)

            # Blend with original image to avoid over-sharpening
            result = cv2.addWeighted(image, 0.7, sharpened, 0.3, 0)

            return result

        except Exception as e:
            logger.warning(f"Text sharpening failed: {e}")
            return image

    def _apply_document_specific_processing(self, image: np.ndarray, document_type: str) -> np.ndarray:
        """
        Apply specialized processing based on document type.

        Args:
            image: Input image
            document_type: Type of document

        Returns:
            np.ndarray: Specialized processed image
        """
        try:
            if document_type in ["extrait_naissance", "extrait_bapteme"]:
                # French certificates often have forms and tables
                return self._process_certificate(image)
            elif document_type == "attestation_transfert":
                # Transfer letters are mostly text
                return self._process_letter(image)
            elif document_type == "preuve_paiement":
                # Payment receipts have specific formats
                return self._process_receipt(image)
            else:
                # General processing
                return self._process_general(image)

        except Exception as e:
            logger.warning(f"Document-specific processing failed: {e}")
            return image

    def _process_certificate(self, image: np.ndarray) -> np.ndarray:
        """
        Process French official certificates (birth, baptism).

        Args:
            image: Certificate image

        Returns:
            np.ndarray: Processed certificate image
        """
        try:
            # Convert to PIL for advanced processing
            pil_image = Image.fromarray(image)

            # Enhance text clarity
            enhancer = ImageEnhance.Sharpness(pil_image)
            sharpened = enhancer.enhance(1.5)

            # Apply adaptive thresholding for form fields
            image_array = np.array(sharpened)

            # Use adaptive threshold to handle varying lighting
            binary = cv2.adaptiveThreshold(
                image_array, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                15, 10
            )

            return binary

        except Exception as e:
            logger.warning(f"Certificate processing failed: {e}")
            return image

    def _process_letter(self, image: np.ndarray) -> np.ndarray:
        """
        Process transfer attestation letters.

        Args:
            image: Letter image

        Returns:
            np.ndarray: Processed letter image
        """
        try:
            # Letters usually have good contrast, focus on text enhancement
            pil_image = Image.fromarray(image)

            # Enhance text readability
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = enhancer.enhance(1.5)

            # Apply slight sharpening
            sharpener = ImageEnhance.Sharpness(enhanced)
            sharpened = sharpener.enhance(1.2)

            return np.array(sharpened)

        except Exception as e:
            logger.warning(f"Letter processing failed: {e}")
            return image

    def _process_receipt(self, image: np.ndarray) -> np.ndarray:
        """
        Process mobile money payment receipts.

        Args:
            image: Receipt image

        Returns:
            np.ndarray: Processed receipt image
        """
        try:
            # Receipts often have low-quality phone images
            # Apply aggressive noise reduction
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)

            # Enhance contrast for digital text
            pil_image = Image.fromarray(denoised)
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = enhancer.enhance(2.0)

            return np.array(enhanced)

        except Exception as e:
            logger.warning(f"Receipt processing failed: {e}")
            return image

    def _process_general(self, image: np.ndarray) -> np.ndarray:
        """
        General document processing when type is unknown.

        Args:
            image: Input image

        Returns:
            np.ndarray: Processed image
        """
        try:
            # Apply moderate enhancement
            pil_image = Image.fromarray(image)

            # Slight contrast enhancement
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = enhancer.enhance(1.3)

            return np.array(enhanced)

        except Exception as e:
            logger.warning(f"General processing failed: {e}")
            return image

    def detect_text_regions(self, image: np.ndarray) -> list:
        """
        Detect text regions in the image for selective processing.

        Args:
            image: Input image

        Returns:
            list: Bounding boxes of text regions
        """
        try:
            # Use morphological operations to find text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
            closed = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours by size and aspect ratio
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size (remove very small or very large regions)
                if w > 50 and h > 20 and w < image.shape[1] * 0.9 and h < image.shape[0] * 0.9:
                    # Filter by aspect ratio (text regions are usually wider than tall)
                    aspect_ratio = w / h
                    if aspect_ratio > 1.5 and aspect_ratio < 20:
                        text_regions.append((x, y, w, h))

            return text_regions

        except Exception as e:
            logger.warning(f"Text region detection failed: {e}")
            return []


# Convenience functions for common preprocessing tasks
def preprocess_image_for_ocr(image_path: str, document_type: str = "general") -> np.ndarray:
    """
    Convenience function to preprocess an image file for OCR.

    Args:
        image_path: Path to image file
        document_type: Type of document

    Returns:
        np.ndarray: Preprocessed image
    """
    try:
        # Load image
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Apply preprocessing
        preprocessor = OCRPreprocessor()
        processed = preprocessor.preprocess_for_ocr(image, document_type)

        return processed

    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        raise


def enhance_image_quality(image: np.ndarray) -> np.ndarray:
    """
    General image quality enhancement.

    Args:
        image: Input image

    Returns:
        np.ndarray: Enhanced image
    """
    try:
        preprocessor = OCRPreprocessor()
        return preprocessor.preprocess_for_ocr(image)

    except Exception as e:
        logger.error(f"Image enhancement failed: {e}")
        return image


def save_processed_image(image: np.ndarray, output_path: str):
    """
    Save processed image to file.

    Args:
        image: Processed image array
        output_path: Output file path
    """
    try:
        # Convert BGR to RGB if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Save using PIL for better quality
        pil_image = Image.fromarray(image)
        pil_image.save(output_path, quality=95)

        logger.info(f"Processed image saved to: {output_path}")

    except Exception as e:
        logger.error(f"Failed to save processed image: {e}")
        raise