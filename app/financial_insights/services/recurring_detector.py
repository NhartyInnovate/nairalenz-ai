from datetime import date, timedelta
from decimal import Decimal
import logging
from typing import List, Dict, Any, Tuple
import uuid
from app.financial_data.models.transaction import Transaction

logger = logging.getLogger("recurring_detector")

class RecurringDetector:
    def detect_recurring(
        self,
        transactions: List[Transaction]
    ) -> List[Dict[str, Any]]:
        """
        Identify recurring payment patterns from transaction streams.
        Returns:
            List of detected recurring payments payload dictionaries.
        """
        detected = []
        if len(transactions) < 2:
            return detected

        # Group debits by merchant description
        groups: Dict[str, List[Transaction]] = {}
        for tx in transactions:
            if tx.transaction_type == "DEBIT":
                name = tx.description.strip().lower()
                if name not in groups:
                    groups[name] = []
                groups[name].append(tx)

        for name, tx_list in groups.items():
            if len(tx_list) < 2:
                continue

            # Sort chronological
            tx_list.sort(key=lambda x: x.transaction_date)
            
            # Compute intervals and amount variances
            intervals = []
            for i in range(1, len(tx_list)):
                diff = (tx_list[i].transaction_date - tx_list[i-1].transaction_date).days
                intervals.append(diff)

            avg_interval = sum(intervals) / len(intervals)
            avg_amount = sum(Decimal(abs(t.amount)) for t in tx_list) / len(tx_list)

            # Check amount consistency (all within 15% of average)
            consistent_amounts = True
            for t in tx_list:
                amt = Decimal(abs(t.amount))
                if avg_amount > 0:
                    pct_diff = abs(amt - avg_amount) / avg_amount
                    if pct_diff > 0.15:
                        consistent_amounts = False
                        break

            if not consistent_amounts:
                continue

            # Check frequency criteria
            frequency = None
            if 25 <= avg_interval <= 35:
                frequency = "MONTHLY"
            elif 5 <= avg_interval <= 9:
                frequency = "WEEKLY"

            if frequency:
                last_tx = tx_list[-1]
                next_date = last_tx.transaction_date + timedelta(days=round(avg_interval))
                
                detected.append({
                    "merchant": last_tx.description,
                    "frequency": frequency,
                    "average_amount": avg_amount,
                    "next_expected_date": next_date,
                    "confidence": 0.90,
                    "last_transaction_ids": [str(t.id) for t in tx_list[-3:]] # track last 3 transaction references
                })

        return detected
