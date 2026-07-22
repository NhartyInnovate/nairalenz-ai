from enum import Enum
import logging

logger = logging.getLogger("bank_detector")

class BankType(str, Enum):
    GTBANK = "GTBANK"
    ZENITH = "ZENITH"
    ACCESS = "ACCESS"
    UNKNOWN = "UNKNOWN"

class BankDetector:
    def detect_bank(self, file_bytes: bytes, filename: str) -> BankType:
        """
        Evaluate headers, content, and file naming structures to detect the issuing bank.
        """
        # Convert bytes to lowercase string representation to search keywords safely
        content_lower = file_bytes.lower()
        filename_lower = filename.lower()
        
        # 1. Check GTBank keywords
        if b"guaranty trust bank" in content_lower or b"gtbank" in content_lower or "gtbank" in filename_lower:
            logger.info(f"Detected GTBank from file signature: {filename}")
            return BankType.GTBANK

        # 2. Check Zenith Bank keywords
        if b"zenith bank" in content_lower or b"zenith" in content_lower or "zenith" in filename_lower:
            logger.info(f"Detected Zenith Bank from file signature: {filename}")
            return BankType.ZENITH

        # 3. Check Access Bank keywords
        if b"access bank" in content_lower or b"access" in content_lower or "access" in filename_lower:
            logger.info(f"Detected Access Bank from file signature: {filename}")
            return BankType.ACCESS

        logger.info(f"Bank detection inconclusive for file: {filename}. Defaulting to UNKNOWN.")
        return BankType.UNKNOWN
