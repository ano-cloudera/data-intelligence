import unittest

from app.core.config import Settings
from app.services.memory_store import SessionMemoryStore
from app.services.session_store import InMemorySessionStore


class MemoryStoreTestCase(unittest.TestCase):
    def test_memory_store_trims_history(self) -> None:
        settings = Settings(
            SESSION_BACKEND="memory",
            SESSION_TTL_MINUTES=30,
            MEMORY_MAX_HISTORY=2,
        )
        session_store = InMemorySessionStore(settings=settings)
        memory_store = SessionMemoryStore(
            session_store=session_store,
            settings=settings,
        )

        memory_store.append_user_message("session-1", "hello")
        memory_store.append_assistant_message("session-1", "hi")
        memory_store.append_user_message("session-1", "show deposits")

        history = memory_store.fetch_recent_history("session-1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].content, "hi")
        self.assertEqual(history[1].content, "show deposits")
