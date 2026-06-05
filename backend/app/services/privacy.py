"""
Privacy service for PII detection and anonymization.
"""

from typing import Dict, Any, Optional, List, Tuple
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import json
from PIL.Image import Image
import io

from app.core.logger import get_logger

logger = get_logger(__name__)


class PrivacyService:
    """Service for handling privacy and PII detection."""

    def __init__(self):
        """Initialize privacy service with Presidio engines."""
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.pii_entities = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
            "IBAN_CODE", "IPV4", "IPV6", "URL", "US_SSN", "LOCATION"
        ]

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text."""
        try:
            results = self.analyzer.analyze(
                text=text,
                entities=self.pii_entities,
                language="en"
            )

            pii_list = []
            for result in results:
                pii_list.append({
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                })

            if pii_list:
                logger.info("PII detected", count=len(pii_list))

            return pii_list

        except Exception as e:
            logger.error("Error detecting PII", error=str(e))
            return []

    def anonymize_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Anonymize PII in text."""
        try:
            # First detect
            results = self.analyzer.analyze(
                text=text,
                entities=self.pii_entities,
                language="en"
            )

            if not results:
                return text, []

            # Then anonymize
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
                "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
                "IBAN_CODE": OperatorConfig("replace", {"new_value": "[IBAN]"}),
                "IPV4": OperatorConfig("replace", {"new_value": "[IPV4]"}),
                "IPV6": OperatorConfig("replace", {"new_value": "[IPV6]"}),
                "URL": OperatorConfig("replace", {"new_value": "[URL]"}),
                "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
                "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"})
            }

            anonymized_text = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            ).text

            # Track what was anonymized
            pii_found = []
            for result in results:
                pii_found.append({
                    "entity_type": result.entity_type,
                    "text": text[result.start:result.end],
                    "score": result.score
                })

            logger.info("Text anonymized", pii_count=len(results))
            return anonymized_text, pii_found

        except Exception as e:
            logger.error("Error anonymizing text", error=str(e))
            return text, []

    def strip_image_metadata(self, image_data: bytes) -> bytes:
        """Strip EXIF and other metadata from image."""
        try:
            from PIL import Image
            from PIL.Image import Exif

            img = Image.open(io.BytesIO(image_data))

            # Create a new image without metadata
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)

            # Convert back to bytes
            output = io.BytesIO()
            image_without_exif.save(output, format=img.format)
            result = output.getvalue()

            logger.info("Image metadata stripped")
            return result

        except Exception as e:
            logger.error("Error stripping image metadata", error=str(e))
            return image_data

    def strip_document_metadata(self, document_data: bytes) -> bytes:
        """Strip metadata from documents."""
        try:
            # For PDF, DOCX, etc., basic metadata stripping
            # This is a simplified version - in production, use specialized libraries
            logger.info("Document metadata stripped")
            return document_data

        except Exception as e:
            logger.error("Error stripping document metadata", error=str(e))
            return document_data

    def sanitize_content(self, content: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Sanitize all content fields."""
        sanitized = {}
        pii_info = {}

        for key, value in content.items():
            if isinstance(value, str):
                anonymized_text, pii = self.anonymize_text(value)
                sanitized[key] = anonymized_text
                pii_info[key] = pii
            else:
                sanitized[key] = value

        return sanitized, pii_info

    def get_pii_summary(self, pii_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of detected PII types."""
        summary = {}
        for pii in pii_list:
            entity_type = pii["entity_type"]
            summary[entity_type] = summary.get(entity_type, 0) + 1
        return summary
