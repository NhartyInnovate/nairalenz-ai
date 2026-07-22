from abc import ABC, abstractmethod
from typing import Dict, Any, List

class FileValidator(ABC):
    """
    Interface for file-specific format and payload structure validation.
    """
    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """
        Expose capability metadata describing parser features.
        """
        pass

    @abstractmethod
    def validate(self, file_bytes: bytes, filename: str, content_type: str) -> None:
        """
        Perform format structural, MIME, extension, and magic signature checks.
        """
        pass

class PDFValidator(FileValidator):
    @property
    def capabilities(self) -> Dict[str, Any]:
        return {
            "supports_ocr": True,
            "supports_embedded_text": True,
            "supports_password_detection": True
        }

    def validate(self, file_bytes: bytes, filename: str, content_type: str) -> None:
        # File Size bounds checked at service level
        lower_filename = filename.lower()
        if not lower_filename.endswith(".pdf") or lower_filename.count(".") > 1:
            raise ValueError("Only standard PDF files are supported")

        if content_type.lower() != "application/pdf":
            raise ValueError("MIME type must be application/pdf")

        if not file_bytes.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF structure: magic bytes signature mismatch")

class CSVValidator(FileValidator):
    @property
    def capabilities(self) -> Dict[str, Any]:
        return {
            "supports_encoding_detection": True,
            "supports_delimiter_detection": True,
            "supports_header_validation": True
        }

    def validate(self, file_bytes: bytes, filename: str, content_type: str) -> None:
        lower_filename = filename.lower()
        if not lower_filename.endswith(".csv") or lower_filename.count(".") > 1:
            raise ValueError("Only standard CSV files are supported")

        valid_mimes = ["text/csv", "application/csv", "application/vnd.ms-excel"]
        if content_type.lower() not in valid_mimes:
            raise ValueError("MIME type must be text/csv or application/csv")

        # Verify CSV text structure (rejects binaries disguised as CSV)
        is_text = False
        try:
            file_bytes.decode("utf-8")
            is_text = True
        except UnicodeDecodeError:
            # Check if it has UTF-16 BOM before trying UTF-16 decode
            if file_bytes.startswith(b"\xff\xfe") or file_bytes.startswith(b"\xfe\xff"):
                try:
                    file_bytes.decode("utf-16")
                    is_text = True
                except UnicodeDecodeError:
                    pass
        if not is_text:
            raise ValueError("Invalid CSV encoding: file is not text-compatible")

class FileValidatorRegistry:
    """
    Registry pattern mapping file properties (extensions) to validation strategies.
    Makes it easy to plug in new formats (OFX, XLSX, etc.) without altering code.
    """
    def __init__(self):
        self._registry: Dict[str, FileValidator] = {
            ".pdf": PDFValidator(),
            ".csv": CSVValidator()
        }

    def get_validator(self, filename: str) -> FileValidator:
        lower_filename = filename.lower()
        for ext, validator in self._registry.items():
            if lower_filename.endswith(ext):
                return validator
        raise ValueError("Unsupported file format: no matching validator found")

# Global singleton validator registry
validator_registry = FileValidatorRegistry()
