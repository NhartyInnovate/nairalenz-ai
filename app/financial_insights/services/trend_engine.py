from decimal import Decimal
from typing import List, Dict, Any
import uuid
from app.financial_data.models.transaction import Transaction

class TrendEngine:
    def calculate_trends(
        self,
        current_txs: List[Transaction],
        previous_txs: List[Transaction],
        categories_map: Dict[uuid.UUID, str]
    ) -> List[Dict[str, Any]]:
        """
        Compare spending in identical categories between two sets of transactions (periods).
        Returns:
            List of trend metrics dicts.
        """
        trends = []
        
        current_totals: Dict[str, Decimal] = {}
        previous_totals: Dict[str, Decimal] = {}

        for tx in current_txs:
            if tx.transaction_type == "DEBIT":
                cat = categories_map.get(tx.category_id, "Uncategorized")
                current_totals[cat] = current_totals.get(cat, Decimal("0.00")) + Decimal(abs(tx.amount))

        for tx in previous_txs:
            if tx.transaction_type == "DEBIT":
                cat = categories_map.get(tx.category_id, "Uncategorized")
                previous_totals[cat] = previous_totals.get(cat, Decimal("0.00")) + Decimal(abs(tx.amount))

        # Compare categories present in either period
        all_categories = set(current_totals.keys()) | set(previous_totals.keys())
        for cat in all_categories:
            curr_val = current_totals.get(cat, Decimal("0.00"))
            prev_val = previous_totals.get(cat, Decimal("0.00"))
            
            if prev_val == 0 and curr_val == 0:
                continue
                
            delta = curr_val - prev_val
            delta_pct = 0.0
            if prev_val > 0:
                delta_pct = float((delta / prev_val) * 100)
            elif curr_val > 0:
                delta_pct = 100.0  # Infinite growth/new category

            trends.append({
                "category": cat,
                "previous": float(prev_val),
                "current": float(curr_val),
                "delta": float(delta),
                "delta_percent": round(delta_pct, 2)
            })

        return trends
