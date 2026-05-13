import unittest

from app.services.answer_prompt_builder import build_answer_messages


class AnswerPromptBuilderTestCase(unittest.TestCase):
    def test_answer_prompt_includes_grounding_rules(self) -> None:
        messages = build_answer_messages(
            original_question="Show top balances by city",
            executed_sql="SELECT city, SUM(balance) AS total_balance FROM deposits GROUP BY city",
            columns=["city", "total_balance"],
            rows=[{"city": "Jakarta", "total_balance": 1000000}],
            row_count=1,
            truncated=False,
            limit_applied=False,
        )

        self.assertEqual(len(messages), 2)
        self.assertIn("Use only the evidence", messages[0]["content"])
        self.assertIn("Original business question", messages[1]["content"])
