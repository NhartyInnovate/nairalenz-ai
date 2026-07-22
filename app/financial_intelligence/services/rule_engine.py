import logging
from typing import Tuple, Optional, List
import uuid
from app.financial_intelligence.models.rule import CategorizationRule
from app.financial_intelligence.utils.normalizer import normalize_description

logger = logging.getLogger("rule_engine")

class RuleEngine:
    def evaluate_rules(
        self,
        description: str,
        rules: List[CategorizationRule]
    ) -> Tuple[Optional[uuid.UUID], float, Optional[CategorizationRule]]:
        """
        Evaluate normalized description against prioritizing rules list.
        Returns:
            Tuple[Resolved_Category_UUID, confidence_score, matched_rule_instance]
        """
        if not description or not rules:
            return None, 0.0, None

        normalized_desc = normalize_description(description)
        if not normalized_desc:
            return None, 0.0, None

        # Rules are pre-ordered by priority desc, so first match wins!
        for rule in rules:
            pattern_clean = rule.pattern.lower().strip()
            # Direct pattern match or substring match
            if pattern_clean in normalized_desc or normalized_desc in pattern_clean:
                logger.info(f"Rule match triggered. Pattern: '{rule.pattern}' (Priority: {rule.priority})")
                return rule.category_id, rule.confidence, rule

        return None, 0.0, None
