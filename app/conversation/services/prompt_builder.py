from typing import List
from app.financial_insights.schemas.query_schemas import FinancialIntelligenceContext

class PromptBuilder:
    def __init__(self, version: str = "v1.0"):
        self.version = version

    def get_prompt_version(self) -> str:
        return self.version

    def build_system_prompt(self, context: FinancialIntelligenceContext) -> str:
        """
        Constructs the highly structured, context-rich system instructions for the LLM.
        """
        # 1. Format Financial Health Snapshot
        snapshot_section = "No financial health summary calculated yet."
        if context.snapshot:
            snapshot_section = (
                f"- Financial Health Score: {context.snapshot.financial_health_score}/100\n"
                f"- Total Monthly Income: NGN {context.snapshot.total_income:,.2f}\n"
                f"- Total Monthly Expenses: NGN {context.snapshot.total_expenses:,.2f}\n"
                f"- Net Cash Flow: NGN {context.snapshot.net_cash_flow:,.2f}\n"
                f"- Savings Rate: {context.snapshot.savings_rate * 100:.1f}%\n"
                f"- Essential Spending: NGN {context.snapshot.essential_expenses:,.2f}\n"
                f"- Discretionary Spending: NGN {context.snapshot.discretionary_expenses:,.2f}\n"
                f"- Top Spending Category: {context.snapshot.largest_category or 'None'}\n"
                f"- Top Merchant: {context.snapshot.largest_merchant or 'None'}"
            )

        # 2. Format Active Insights
        insights_section = "No active spending trends or anomalies detected."
        if context.active_insights:
            insights_lines = []
            for idx, insight in enumerate(context.active_insights):
                insights_lines.append(
                    f"{idx+1}. [{insight.insight_type}] {insight.title}: {insight.description} (Severity: {insight.severity})"
                )
            insights_section = "\n".join(insights_lines)

        # 3. Format Recurring Subscriptions
        recurring_section = "No active subscriptions detected."
        if context.recurring_payments:
            recurring_lines = []
            for p in context.recurring_payments:
                next_date = p.next_expected_date.isoformat() if p.next_expected_date else "unknown"
                recurring_lines.append(
                    f"- {p.merchant}: NGN {p.average_amount:,.2f} / monthly (Next expected: {next_date})"
                )
            recurring_section = "\n".join(recurring_lines)

        # 4. Format Recent Transactions Summary (Past 30 Days category spend)
        tx_summary_section = "No category transactions registered in the past 30 days."
        if context.recent_transactions_summary:
            tx_lines = []
            for s in context.recent_transactions_summary:
                tx_lines.append(
                    f"- {s.category_name}: NGN {s.total_amount:,.2f} spent across {s.transaction_count} transaction(s)"
                )
            tx_summary_section = "\n".join(tx_lines)

        # Build full prompt
        system_prompt = (
            "You are NairaLens AI, an encouraging, professional, and analytical financial coach "
            "designed to help Nigerian users make smarter financial decisions.\n\n"
            "Below is the user's validated financial intelligence context compiled from their uploaded statements:\n\n"
            "=== FINANCIAL HEALTH SNAPSHOT ===\n"
            f"{snapshot_section}\n\n"
            "=== RECENT CATEGORY SPENDING (PAST 30 DAYS) ===\n"
            f"{tx_summary_section}\n\n"
            "=== DETECTED RECURRING SUBSCRIPTIONS ===\n"
            f"{recurring_section}\n\n"
            "=== ACTIVE FINANCIAL INSIGHTS & ANOMALIES ===\n"
            f"{insights_section}\n\n"
            "=== BEHAVIOR RULES ===\n"
            "- Answer user queries specifically using this context.\n"
            "- Reference precise NGN figures, category names, or subscriptions when answering.\n"
            "- Give actionable, local economy context advice (e.g. budgeting tips in NGN, canceling unused subscriptions).\n"
            "- Do not make up any transaction data or numbers not present in the context.\n"
            "- If the user asks about information outside their financial context or unrelated to finances, "
            "politely redirect them back to their NairaLens advisor tools."
        )

        return system_prompt
