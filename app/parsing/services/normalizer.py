from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import logging
from typing import Dict, Any, Tuple, Optional
import uuid
from app.financial_data.models.transaction import Transaction
from app.parsing.models.raw_transaction import RawTransaction

logger = logging.getLogger("normalizer_service")

class NormalizerService:
    def normalize_row(
        self,
        raw_row: Dict[str, Any],
        statement_id: uuid.UUID,
        default_date: date
    ) -> Tuple[Optional[Transaction], float, Optional[str]]:
        """
        Normalize a raw dictionary row extracted by a parser into a Transaction.
        Returns:
            Tuple[Transaction_instance or None, confidence_score, warning_message]
        """
        warning = None
        confidence = 1.0

        # 1. Parse Transaction Date
        raw_date_str = raw_row.get("date") or raw_row.get("transaction_date")
        tx_date = default_date
        if raw_date_str:
            tx_date, date_parsed = self._parse_date(str(raw_date_str), default_date)
            if not date_parsed:
                confidence -= 0.3
                warning = f"Could not parse date '{raw_date_str}', falling back to statement date."
        else:
            confidence -= 0.4
            warning = "Transaction date missing, defaulting to statement date."

        # 2. Parse Description
        description = str(raw_row.get("description") or raw_row.get("narrative") or "Unspecified Transaction").strip()
        if not raw_row.get("description"):
            confidence -= 0.2

        # 3. Parse Financial Amount
        # Enforce Decimal format for money accuracy
        amount = Decimal("0.00")
        tx_type = "CREDIT"
        
        raw_debit = raw_row.get("debit") or raw_row.get("withdrawal")
        raw_credit = raw_row.get("credit") or raw_row.get("deposit")
        raw_amount = raw_row.get("amount")

        try:
            if raw_debit and str(raw_debit).strip():
                debit_val = Decimal(str(raw_debit).strip().replace(",", ""))
                if debit_val > 0:
                    amount = -debit_val
                    tx_type = "DEBIT"
            elif raw_credit and str(raw_credit).strip():
                amount = Decimal(str(raw_credit).strip().replace(",", ""))
                tx_type = "CREDIT"
            elif raw_amount:
                raw_amt_str = str(raw_amount).strip().replace(",", "")
                val = Decimal(raw_amt_str)
                # If negative, it is a DEBIT
                if val < 0:
                    amount = val
                    tx_type = "DEBIT"
                else:
                    amount = val
                    tx_type = "CREDIT"
            else:
                confidence -= 0.5
                warning = "Amount fields missing. Defaulted to 0.00."
        except (InvalidOperation, ValueError):
            confidence -= 0.5
            warning = "Amount parse error. Defaulted to 0.00."

        # 4. Parse running Balance
        balance = None
        raw_bal = raw_row.get("balance")
        if raw_bal:
            try:
                balance = Decimal(str(raw_bal).strip().replace(",", ""))
            except (InvalidOperation, ValueError):
                warning = f"Running balance '{raw_bal}' could not be parsed."

        # 5. Extract Reference
        reference = raw_row.get("ref") or raw_row.get("reference") or raw_row.get("remarks")
        if reference:
            reference = str(reference).strip()

        # Clean confidence boundaries
        confidence = max(0.1, min(1.0, confidence))

        # 6. Generate Identity fingerprint for duplicate detection
        ref_hash = reference or ""
        fingerprint_source = f"{tx_date.isoformat()}:{description}:{amount}:{ref_hash}"
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

        transaction = Transaction(
            id=uuid.uuid4(),
            statement_id=statement_id,
            transaction_date=tx_date,
            description=description,
            amount=amount,
            transaction_type=tx_type,
            currency=str(raw_row.get("currency") or "NGN").strip().upper(),
            balance=balance,
            reference=reference,
            confidence=confidence,
            fingerprint=fingerprint
        )

        return transaction, confidence, warning

    def _parse_date(self, date_str: str, default_date: date) -> Tuple[date, bool]:
        date_str_clean = date_str.strip()
        formats = [
            "%Y-%m-%d",      # 2026-07-22
            "%d-%b-%Y",      # 22-Jul-2026 / 22-jul-2026
            "%d-%m-%Y",      # 22-07-2026
            "%m/%d/%Y",      # 07/22/2026
            "%d/%m/%Y",      # 22/07/2026
            "%Y/%m/%d",      # 2026/07/22
        ]
        for fmt in formats:
            try:
                parsed_dt = datetime.strptime(date_str_clean, fmt)
                return parsed_dt.date(), True
            except ValueError:
                continue

        # Try word month format case insensitively
        try:
            # E.g. "22-jul-2026"
            parsed_dt = datetime.strptime(date_str_clean.title(), "%d-%b-%Y")
            return parsed_dt.date(), True
        except ValueError:
            pass

        return default_date, False
