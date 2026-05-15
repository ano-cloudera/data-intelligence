import unittest

from app.core.config import Settings
from app.services.prompt_builder import build_prompt_debug_view


class PromptContextTestCase(unittest.TestCase):
    def test_prompt_includes_business_and_schema_context(self) -> None:
        settings = Settings(
            DB_NAME="cai_sdx_se_indonesia",
            SQL_ALLOWED_TABLES="customer_dormant_segment",
        )

        prompt_view = build_prompt_debug_view(
            question="Tampilkan nasabah berdasarkan segmen",
            settings=settings,
        )

        self.assertIn("cai_sdx_se_indonesia.customer_dormant_segment", prompt_view["system_prompt"])
        self.assertIn("dormant_risk_level", prompt_view["system_prompt"])
        self.assertIn("customer_segment", prompt_view["system_prompt"])
        self.assertIn("Tampilkan nasabah berdasarkan segmen", prompt_view["user_prompt"])
        self.assertIn("substr(date_column, 1, 7)", prompt_view["system_prompt"])
        self.assertIn("Do not use date_format()", prompt_view["system_prompt"])
