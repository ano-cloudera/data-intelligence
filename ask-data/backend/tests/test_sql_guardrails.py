import unittest

from app.core.config import Settings
from app.services.sql_guardrails import SQLValidationError, validate_and_prepare_sql


class SQLGuardrailsTestCase(unittest.TestCase):
    def test_applies_default_limit_for_listing_query(self) -> None:
        settings = Settings(
            DB_NAME="demo_db",
            SQL_DEFAULT_LIMIT=25,
            SQL_ALLOWED_TABLES="customers,deposits,credits,fraud_transactions",
        )

        sql, limit_applied = validate_and_prepare_sql(
            "SELECT customer_id, full_name FROM customers",
            settings=settings,
        )

        self.assertTrue(limit_applied)
        self.assertEqual(sql, "SELECT customer_id, full_name FROM customers LIMIT 25")

    def test_rejects_unknown_table(self) -> None:
        settings = Settings(
            DB_NAME="demo_db",
            SQL_ALLOWED_TABLES="customers,deposits,credits,fraud_transactions",
        )

        with self.assertRaises(SQLValidationError):
            validate_and_prepare_sql("SELECT * FROM transactions", settings=settings)

    def test_rejects_date_format_function(self) -> None:
        settings = Settings(
            DB_NAME="demo_db",
            SQL_ALLOWED_TABLES="customers,deposits,credits,fraud_transactions",
        )

        with self.assertRaises(SQLValidationError):
            validate_and_prepare_sql(
                "SELECT date_format(cast(join_date as date), 'yyyy-MM') FROM customers",
                settings=settings,
            )
