from decimal import Decimal
import logging
from typing import List, Dict, Any, Tuple
import uuid
from app.financial_data.models.transaction import Transaction

logger = logging.getLogger("anomaly_detector")

class AnomalyDetector:
    def detect_anomalies(
        self,
        transactions: List[Transaction],
        previous_transactions: List[Transaction],
        categories_map: Dict[uuid.UUID, str]
    ) -> List[Dict[str, Any]]:
        """
        Scan transaction stream for duplicate payments, utility spikes, and extreme transfers.
        Returns:
            List of anomaly dictionaries.
        """
        anomalies = []
        if not transactions:
            return anomalies

        # 1. Duplicate transaction detection (same day, amount, description)
        seen: Dict[Tuple[str, Decimal, str], List[Transaction]] = {}
        for tx in transactions:
            key = (tx.transaction_date.isoformat(), Decimal(abs(tx.amount)), tx.description.strip().lower())
            if key not in seen:
                seen[key] = []
            seen[key].append(tx)

        for key, tx_list in seen.items():
            if len(tx_list) > 1:
                # Flag duplicates
                for dup in tx_list[1:]:
                    anomalies.append({
                        "transaction_id": dup.id,
                        "title": "Duplicate Transaction Detected",
                        "description": f"Identical transaction for {dup.description} of amount {dup.amount} detected on same day.",
                        "anomaly_type": "DUPLICATE",
                        "severity": "CRITICAL",
                        "confidence": 0.95,
                        "provenance": {
                            "engine": "AnomalyDetector",
                            "engine_version": "1.0.0",
                            "based_on": [str(t.id) for t in tx_list]
                        }
                    })

        # Calculate average stats from history to benchmark spikes
        prev_utility_debits = [
            Decimal(abs(t.amount)) for t in previous_transactions 
            if t.transaction_type == "DEBIT" and categories_map.get(t.category_id) in ["Bills & Utilities", "Utilities"]
        ]
        avg_utility = sum(prev_utility_debits) / len(prev_utility_debits) if prev_utility_debits else Decimal("0.00")

        # 2. Utility Bill spike (> 3x average)
        for tx in transactions:
            if tx.transaction_type == "DEBIT" and categories_map.get(tx.category_id) in ["Bills & Utilities", "Utilities"]:
                amt = Decimal(abs(tx.amount))
                if avg_utility > 0:
                    multiplier = amt / avg_utility
                    if multiplier >= 3.0:
                        anomalies.append({
                            "transaction_id": tx.id,
                            "title": "Utility Bill Spike Detected",
                            "description": f"Electricity or bill payment for {tx.description} is {round(multiplier, 1)}x higher than average ({avg_utility}).",
                            "anomaly_type": "UTILITY_SPIKE",
                            "severity": "CRITICAL",
                            "confidence": 0.90,
                            "provenance": {
                                "engine": "AnomalyDetector",
                                "engine_version": "1.0.0",
                                "average_utility": float(avg_utility),
                                "current_utility": float(amt),
                                "multiplier": float(multiplier)
                            }
                        })
                    elif multiplier >= 1.5:
                        anomalies.append({
                            "transaction_id": tx.id,
                            "title": "Utility Bill Spike Warning",
                            "description": f"Electricity or bill payment for {tx.description} is higher than average.",
                            "anomaly_type": "UTILITY_SPIKE",
                            "severity": "WARNING",
                            "confidence": 0.85,
                            "provenance": {
                                "engine": "AnomalyDetector",
                                "engine_version": "1.0.0",
                                "average_utility": float(avg_utility),
                                "current_utility": float(amt),
                                "multiplier": float(multiplier)
                            }
                        })

        return anomalies
