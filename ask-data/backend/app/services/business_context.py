from __future__ import annotations


def build_supported_question_examples() -> str:
    return """
Supported business question patterns include:
- customer count by dormant_risk_level (low / medium / high)
- customer count by customer_segment
- average dormant_probability by customer_segment
- total deposit balance by dormant_risk_level
- average savings balance by city or district
- outstanding loan balance by income_band
- customers with dormant_flag = true grouped by age_band
- days_since_last_transaction distribution by segment
- count of customers with has_mobile_banking = true vs false
- recommended_campaign distribution for high-risk dormant customers
- recommended_channel breakdown by customer_segment
- next_best_action frequency by dormant_reason_code
- product_holding_count distribution across segments
- active_months_last_6m average by dormant_risk_level
- digital_login_count_3m average by customer_type
""".strip()


def build_ambiguity_guidance() -> str:
    return """
Interpretation guidance:
- Prefer the safest reasonable interpretation of ambiguous questions.
- Do not invent values that are not present in the schema.
- Use grouping and aggregation for summary questions.
- All data is in the customer_dormant_segment table — no joins are needed.
- If a question asks for "dormant customers", filter on dormant_flag = true or dormant_risk_level = 'high'.
- If a question asks for segment distribution, GROUP BY customer_segment.
- If a question asks about balance, use avg_deposit_balance_3m, total_deposit_balance, or avg_savings_balance_3m as appropriate.
- If a question asks about campaign or reactivation, use recommended_campaign, recommended_channel, or next_best_action.
- If a question is broad, return a practical preview query with LIMIT applied.
""".strip()


def build_business_context() -> str:
    return "\n\n".join(
        (
            "Business context: The dataset is the customer_dormant_segment table — a single-table view of Bank Jawa Timur customers enriched with dormancy risk scores, segmentation labels, behavioral analytics, and campaign recommendations.",
            build_supported_question_examples(),
            build_ambiguity_guidance(),
        )
    )
