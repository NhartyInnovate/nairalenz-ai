from decimal import Decimal
from typing import Dict, Tuple

class HealthScorer:
    def calculate_health_score(
        self,
        total_income: Decimal,
        total_expenses: Decimal,
        savings_rate: float,
        essential: Decimal,
        discretionary: Decimal
    ) -> Tuple[int, Dict[str, int]]:
        """
        Compute a transparent score (0-100) and its component factors.
        Returns:
            Tuple[overall_score, component_scores_dict]
        """
        # 1. Savings Rate component (40% weight)
        # Optimal savings rate is 20% or more -> score 100.
        savings_score = min(int((savings_rate / 0.20) * 100), 100) if savings_rate > 0 else 0
        
        # 2. Expense concentration & consistency (30% weight)
        # Ratio of discretionary to essential
        discretionary_score = 100
        if essential > 0:
            ratio = discretionary / essential
            if ratio > 2.0:
                discretionary_score = 0
            elif ratio > 1.0:
                discretionary_score = 50
            else:
                discretionary_score = 100
        elif discretionary > 0:
            discretionary_score = 0

        # 3. Income stability (30% weight)
        stability_score = 0
        if total_income > 0:
            if total_income >= total_expenses:
                stability_score = 100
            else:
                ratio = total_income / total_expenses
                stability_score = int(ratio * 100)

        # Weighted score
        overall_score = int(
            (savings_score * 0.40) +
            (discretionary_score * 0.30) +
            (stability_score * 0.30)
        )

        component_scores = {
            "savings_rate_score": savings_score,
            "discretionary_spend_score": discretionary_score,
            "income_stability_score": stability_score
        }

        return overall_score, component_scores
