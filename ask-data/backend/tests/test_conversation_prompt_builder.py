import unittest

from app.services.conversation_prompt_builder import build_conversation_messages


class ConversationPromptBuilderTestCase(unittest.TestCase):
    def test_prompt_includes_persona_and_language_rules(self) -> None:
        messages = build_conversation_messages("selamat pagi")

        self.assertEqual(len(messages), 2)
        self.assertIn("You are a Data Analyst Assistant", messages[0]["content"])
        self.assertIn("credit risk", messages[0]["content"])
        self.assertIn("Respond in the same language as the user", messages[0]["content"])
        self.assertIn("Current user message: selamat pagi", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
