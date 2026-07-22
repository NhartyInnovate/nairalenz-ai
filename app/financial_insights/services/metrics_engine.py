from decimal import Decimal
from typing import List, Dict, Any, Tuple
import uuid
from app.financial_data.models.transaction import Transaction

class MetricsEngine:
    def calculate_metrics(
        self,
        transactions: List[Transaction],
        categories_map: Dict[uuid.UUID, str]
    ) -> Tuple[Decimal, Decimal, Decimal, float, Decimal, Decimal, str, str]:
        """
        Calculate essential income, expenses, cash flows, and category distributions.
        Returns:
            Tuple[total_income, total_expenses, net_cash_flow, savings_rate, essential, discretionary, largest_cat, largest_merchant]
        """
        total_income = Decimal("0.00")
        total_expenses = Decimal("0.00")
        essential = Decimal("0.00")
        discretionary = Decimal("0.00")
        
        category_spending: Dict[str, Decimal] = {}
        merchant_spending: Dict[str, Decimal] = {}

        # Define Essential vs Discretionary categories
        essential_categories = {
            "Groceries", "Transport", "Fuel", "Bills & Utilities",
            "Healthcare", "Education", "Loan", "Tax", "Fees & Charges"
        }

        for tx in transactions:
            amount_abs = Decimal(abs(tx.amount))
            cat_name = categories_map.get(tx.category_id, "Uncategorized")
            
            if tx.transaction_type == "CREDIT":
                total_income += amount_abs
            else:
                total_expenses += amount_abs
                
                # Category breakdown
                category_spending[cat_name] = category_spending.get(cat_name, Decimal("0.00")) + amount_abs
                
                # Merchant breakdown
                merchant_name = tx.description.strip() # fallback
                merchant_spending[merchant_name] = merchant_spending.get(merchant_name, Decimal("0.00")) + amount_abs
                
                # Essential vs Discretionary
                if cat_name in essential_categories:
                    essential += amount_abs
                else:
                    discretionary += amount_abs

        net_cash_flow = total_income - total_expenses
        
        # Savings rate = net cash flow / total income (if positive)
        savings_rate = 0.0
        if total_income > 0 and net_cash_flow > 0:
            savings_rate = float(net_cash_flow / total_income)

        # Find largest category and merchant
        largest_cat = max(category_spending, key=category_spending.get) if category_spending else "None"
        largest_merchant = max(merchant_spending, key=merchant_spending.get) if merchant_spending else "None"

        return (
            total_income,
            total_expenses,
            net_cash_flow,
            savings_rate,
            essential,
            discretionary,
            largest_cat,
            largest_merchant
        )
