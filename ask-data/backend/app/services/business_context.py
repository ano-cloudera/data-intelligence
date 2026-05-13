from __future__ import annotations


def build_supported_question_examples() -> str:
    return """
Supported business question patterns include:
- total deposit balance by city
- total outstanding credit by city
- top customers by balance
- top customers by outstanding credit
- customer count by segment
- balances by product type
- credit exposure by collectibility
- balances by branch
- active vs non-active deposit counts
- active vs restructured credit counts
- maturity analysis
- customer onboarding trends
- customer cross-holding between deposits and credits
- fraud rate by channel
- fraud amount by origin city
- top risky transactions by velocity_risk_score
- customers with repeated new-device fraud
- fraud distribution by transaction type or fraud reason
""".strip()


def build_ambiguity_guidance() -> str:
    return """
Interpretation guidance:
- Prefer the safest reasonable interpretation of ambiguous questions.
- Do not invent values that are not present in the schema.
- Use grouping and aggregation for summary questions.
- Use joins only when needed to answer the question.
- If a question is broad, return a practical preview query.
- If a question asks for customer-level analysis, start from customers unless deposit data is required.
- If a question asks for balance, product, maturity, branch, or account status analysis, deposits is usually required.
- If a question asks about credit, loans, outstanding balance, principal, collectibility, or interest rate, credits is usually required.
- If a question asks about fraud rate, suspicious transactions, device changes, velocity patterns, or anomaly reasons, fraud_transactions is usually required.
- If a question asks for both deposit and credit metrics in one result, consider pre-aggregating each table by customer before joining.
- If a question mixes fraud metrics with deposits or credits, pre-aggregate each child table by customer, channel, or transaction type before joining.
""".strip()


def build_business_context() -> str:
    return "\n\n".join(
        (
            "Business context: The dataset represents a banking customer, deposit, credit, and fraud analytics demo.",
            build_supported_question_examples(),
            build_ambiguity_guidance(),
        )
    )
