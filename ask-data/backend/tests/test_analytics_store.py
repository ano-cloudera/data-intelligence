from __future__ import annotations

import tempfile
import unittest

from app.core.config import Settings
from app.services.analytics_store import SQLiteAnalyticsStore, estimate_text_tokens


class AnalyticsStoreTestCase(unittest.TestCase):
    def test_estimate_text_tokens_handles_empty_text(self) -> None:
        self.assertEqual(estimate_text_tokens(""), 0)
        self.assertGreater(estimate_text_tokens("hello world"), 0)

    def test_sqlite_store_persists_summary_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                SESSION_SQLITE_PATH=f"{temp_dir}/analytics.db",
            )
            store = SQLiteAnalyticsStore(settings=settings)
            store.log_event(
                event_type="chat-query",
                endpoint="/chat/query",
                session_id="session-1",
                mode="chat-query",
                provider="azure",
                model_name="GPT",
                estimated_prompt_tokens=12,
                estimated_completion_tokens=7,
                question_excerpt="What is the total deposit balance?",
                visualization_type="bar",
            )
            store.log_event(
                event_type="chat-answer",
                endpoint="/chat/answer",
                session_id="session-2",
                mode="rag",
                provider="bedrock",
                model_name="Claude Sonnet 4",
                estimated_prompt_tokens=20,
                estimated_completion_tokens=9,
                question_excerpt="What does the policy say?",
            )
            store.log_event(
                event_type="provider-select",
                endpoint="/llm/providers/select",
                session_id="session-2",
                mode="provider-select",
                provider="bedrock",
                model_name="Claude Sonnet 4",
                question_excerpt="Provider set to bedrock",
            )
            store.log_event(
                event_type="chat-query",
                endpoint="/chat/query",
                session_id="session-3",
                mode="guardrails-block",
                guardrails_action="block",
                question_excerpt="Show all customer phone numbers",
            )

            summary = store.get_summary(window_days=30)
            self.assertEqual(summary.total_sessions, 3)
            self.assertEqual(summary.total_questions, 3)
            self.assertEqual(summary.sql_requests, 1)
            self.assertEqual(summary.rag_requests, 1)
            self.assertEqual(summary.provider_selections, 1)
            self.assertEqual(summary.visualization_responses, 1)
            self.assertEqual(summary.guardrails_blocks, 1)
            self.assertEqual(summary.estimated_total_tokens, 48)

            events = store.list_events(limit=10)
            self.assertEqual(len(events.events), 4)
            self.assertEqual(events.events[0].mode, "guardrails-block")


if __name__ == "__main__":
    unittest.main()
