import unittest

from app.core.config import Settings
from app.services.prompt_builder import build_text_to_sql_messages


class PromptBuilderTestCase(unittest.TestCase):
    def test_prompt_includes_expected_constraints(self) -> None:
        settings = Settings(
            DB_NAME="demo_db",
            IMPALA_HOST="impala-host",
            IMPALA_PORT=443,
            IMPALA_HTTP_PATH="cliservice",
            CDP_USER="demo-user",
            CDP_PASS="demo-pass",
        )

        messages = build_text_to_sql_messages(
            "List active deposits",
            settings=settings,
        )

        self.assertEqual(len(messages), 2)
        self.assertIn("demo_db", messages[0]["content"])
        self.assertIn("customers", messages[0]["content"])
        self.assertIn("deposits", messages[0]["content"])
        self.assertIn("credits", messages[0]["content"])
        self.assertIn("fraud_transactions", messages[0]["content"])
        self.assertIn("read-only SQL only", messages[0]["content"])
