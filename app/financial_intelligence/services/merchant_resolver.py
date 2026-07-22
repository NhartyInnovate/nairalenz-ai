import logging
from typing import Tuple, Optional, List
from app.financial_intelligence.models.merchant import Merchant
from app.financial_intelligence.utils.normalizer import normalize_description

logger = logging.getLogger("merchant_resolver")

class MerchantResolver:
    def resolve_merchant(
        self,
        description: str,
        merchants: List[Merchant]
    ) -> Tuple[Optional[Merchant], float, List[str]]:
        """
        Scan a transaction description against all loaded merchants.
        Returns:
            Tuple[Resolved_Merchant, confidence_score, reasons_list]
        """
        reasons = []
        if not description or not merchants:
            return None, 0.0, ["Empty inputs"]

        normalized_desc = normalize_description(description)
        if not normalized_desc:
            return None, 0.0, ["Description normalization resulted in empty string"]

        # 1. Exact canonical matching (case-insensitive)
        for merchant in merchants:
            if normalized_desc == merchant.canonical_name.lower():
                reasons.append("exact canonical name match")
                return merchant, 0.99, reasons

        # 2. Exact Alias list matching
        for merchant in merchants:
            # aliases is a JSON list of lowercase string representations
            if normalized_desc in [alias.lower() for alias in merchant.aliases]:
                reasons.append("exact merchant alias match")
                return merchant, 0.98, reasons

        # 3. Substring / Prefix matching (checks if alias is inside description, or vice-versa)
        for merchant in merchants:
            # Try matching canonical name as substring
            canonical_lower = merchant.canonical_name.lower()
            if canonical_lower in normalized_desc or normalized_desc in canonical_lower:
                reasons.append(f"partial match on canonical name: {merchant.canonical_name}")
                return merchant, 0.82, reasons
                
            # Try matching any alias as substring
            for alias in merchant.aliases:
                alias_lower = alias.lower()
                if alias_lower in normalized_desc or normalized_desc in alias_lower:
                    reasons.append(f"partial match on merchant alias: {alias}")
                    return merchant, 0.82, reasons

        return None, 0.0, ["No matching merchant found"]
