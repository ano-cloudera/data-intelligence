import unittest

from app.services.visualization_service import VisualizationService


class VisualizationServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = VisualizationService()

    def test_builds_line_chart_for_temporal_series(self) -> None:
        spec = self.service.build_visualization(
            question="Show deposit trend by month",
            columns=["month", "total_deposit_balance"],
            rows=[
                {"month": "2026-02", "total_deposit_balance": 120},
                {"month": "2026-01", "total_deposit_balance": 100},
                {"month": "2026-03", "total_deposit_balance": 150},
            ],
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.type, "line")
        self.assertEqual(spec.x_key, "month")
        self.assertEqual(spec.series[0]["month"], "2026-01")
        self.assertEqual(spec.series[-1]["month"], "2026-03")
        self.assertEqual(spec.table_columns, ["month", "total_deposit_balance"])

    def test_samples_long_temporal_series_evenly(self) -> None:
        rows = [
            {"join_date": f"2026-01-{day:02d}", "customer_count": day}
            for day in range(1, 13)
        ]

        spec = self.service.build_visualization(
            question="Show new customers by join date",
            columns=["join_date", "customer_count"],
            rows=rows,
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.type, "line")
        self.assertEqual(len(spec.series), 8)
        self.assertEqual(spec.series[0]["join_date"], "2026-01-01")
        self.assertEqual(spec.series[-1]["join_date"], "2026-01-12")

    def test_builds_bar_chart_for_category_comparison(self) -> None:
        spec = self.service.build_visualization(
            question="Compare outstanding credit by city",
            columns=["city", "total_outstanding_credit"],
            rows=[
                {"city": "Jakarta", "total_outstanding_credit": 1000},
                {"city": "Bandung", "total_outstanding_credit": 800},
            ],
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.type, "bar")
        self.assertEqual(spec.series[0]["city"], "Jakarta")
        self.assertEqual(spec.table_rows[0]["city"], "Jakarta")

    def test_honors_bar_override_for_temporal_series(self) -> None:
        spec = self.service.build_visualization(
            question="Ubah ke barchart",
            columns=["month", "total_outstanding_credit"],
            rows=[
                {"month": "2026-01", "total_outstanding_credit": 100},
                {"month": "2026-02", "total_outstanding_credit": 120},
            ],
            preferred_type="bar",
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.type, "bar")
        self.assertEqual(spec.series[0]["month"], "2026-01")

    def test_builds_pie_chart_for_small_composition(self) -> None:
        spec = self.service.build_visualization(
            question="Show customer composition by segment",
            columns=["segment", "customer_count"],
            rows=[
                {"segment": "Retail", "customer_count": 10},
                {"segment": "SME", "customer_count": 20},
                {"segment": "Corporate", "customer_count": 5},
            ],
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.type, "pie")

    def test_returns_none_for_non_chartable_shape(self) -> None:
        spec = self.service.build_visualization(
            question="Show details",
            columns=["customer_name", "city"],
            rows=[
                {"customer_name": "A", "city": "Jakarta"},
                {"customer_name": "B", "city": "Bandung"},
            ],
        )

        self.assertIsNone(spec)
