import tempfile
import unittest
from pathlib import Path

from app.core.config import Settings
from app.schemas.session import ChatMessage, SessionMemoryState
from app.services.session_store import SQLiteSessionStore


class SQLiteSessionStoreTestCase(unittest.TestCase):
    def test_persists_session_payload_between_store_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "sessions.db"
            settings = Settings(
                SESSION_BACKEND="sqlite",
                SESSION_SQLITE_PATH=str(db_path),
                SESSION_TTL_MINUTES=30,
            )
            first_store = SQLiteSessionStore(settings=settings)
            session = first_store.create_session_if_not_exists("session-1")
            session.messages.append(ChatMessage(role="user", content="show top deposit customers"))
            session.last_answer = "Here is the latest ranking."
            first_store.update_session(session)

            second_store = SQLiteSessionStore(settings=settings)
            restored = second_store.get_session("session-1")

            self.assertIsNotNone(restored)
            assert restored is not None
            self.assertEqual(len(restored.messages), 1)
            self.assertEqual(restored.messages[0].content, "show top deposit customers")
            self.assertEqual(restored.last_answer, "Here is the latest ranking.")

    def test_lists_recent_sessions_in_descending_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "sessions.db"
            settings = Settings(
                SESSION_BACKEND="sqlite",
                SESSION_SQLITE_PATH=str(db_path),
                SESSION_TTL_MINUTES=30,
            )
            store = SQLiteSessionStore(settings=settings)

            first = SessionMemoryState(session_id="session-1")
            first.messages.append(ChatMessage(role="user", content="show deposits"))
            store.update_session(first)

            second = SessionMemoryState(session_id="session-2")
            second.messages.append(ChatMessage(role="user", content="show credits"))
            store.update_session(second)

            summaries = store.list_sessions(limit=10)

            self.assertEqual([item.session_id for item in summaries], ["session-2", "session-1"])
            self.assertEqual(summaries[0].title, "show credits")
