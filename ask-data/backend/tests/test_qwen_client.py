import unittest
from unittest.mock import MagicMock, patch

from llm.qwen_client import LLMChatResult, QwenClient


def _fake_openai_response(content: str, reasoning_content: str | None = None):
    message = MagicMock()
    message.content = content
    message.reasoning_content = reasoning_content
    message.reasoning = None
    choice = MagicMock(message=message)
    return MagicMock(choices=[choice])


class QwenClientThinkingTestCase(unittest.TestCase):
    def test_thinking_off_sends_enable_thinking_false_and_returns_content_only(self) -> None:
        """VLLM_ENABLE_THINKING unset (or false) -> request asks vLLM for
        enable_thinking=False, and the result carries no reasoning."""
        with patch.dict("os.environ", {"VLLM_ENABLE_THINKING": "false"}, clear=False):
            client = QwenClient()
            with patch.object(
                client.client.chat.completions,
                "create",
                return_value=_fake_openai_response("Selamat pagi! Ada yang bisa saya bantu?"),
            ) as mock_create:
                result = client.chat([{"role": "user", "content": "hallo"}])

        self.assertIsInstance(result, LLMChatResult)
        self.assertEqual(result.content, "Selamat pagi! Ada yang bisa saya bantu?")
        self.assertIsNone(result.reasoning)
        sent_extra_body = mock_create.call_args.kwargs["extra_body"]
        self.assertEqual(sent_extra_body["chat_template_kwargs"], {"enable_thinking": False})
        # Content must never contain a leaked reasoning block.
        self.assertNotIn("<think>", result.content)

    def test_thinking_on_sends_enable_thinking_true_and_separates_reasoning(self) -> None:
        """VLLM_ENABLE_THINKING=true -> request asks vLLM for
        enable_thinking=True, and reasoning is returned as a field
        separate from content — never concatenated into one string."""
        with patch.dict("os.environ", {"VLLM_ENABLE_THINKING": "true"}, clear=False):
            client = QwenClient()
            with patch.object(
                client.client.chat.completions,
                "create",
                return_value=_fake_openai_response(
                    "Selamat pagi! Ada yang bisa saya bantu?",
                    reasoning_content="Analyzing the user's greeting in Indonesian...",
                ),
            ) as mock_create:
                result = client.chat([{"role": "user", "content": "hallo"}])

        self.assertEqual(result.content, "Selamat pagi! Ada yang bisa saya bantu?")
        self.assertEqual(result.reasoning, "Analyzing the user's greeting in Indonesian...")
        sent_extra_body = mock_create.call_args.kwargs["extra_body"]
        self.assertEqual(sent_extra_body["chat_template_kwargs"], {"enable_thinking": True})
        # Reasoning must never be concatenated into the visible answer.
        self.assertNotIn("Analyzing", result.content)

    def test_inline_think_block_is_split_structurally_not_regex_stripped(self) -> None:
        """Compatibility path: some servers inline <think>...</think> into
        message.content instead of a dedicated field. Must still split
        into (content, reasoning), not silently discard the reasoning."""
        with patch.dict("os.environ", {"VLLM_ENABLE_THINKING": "true"}, clear=False):
            client = QwenClient()
            raw = "<think>step 1, step 2</think>\nJawaban akhir yang bersih."
            with patch.object(
                client.client.chat.completions,
                "create",
                return_value=_fake_openai_response(raw),
            ):
                result = client.chat([{"role": "user", "content": "hallo"}])

        self.assertEqual(result.content, "Jawaban akhir yang bersih.")
        self.assertEqual(result.reasoning, "step 1, step 2")

    def test_missing_reasoning_field_does_not_crash_when_thinking_enabled(self) -> None:
        """If thinking is enabled but the endpoint doesn't return a
        reasoning field at all, the client must not crash — just return
        content normally (graceful compatibility)."""
        with patch.dict("os.environ", {"VLLM_ENABLE_THINKING": "true"}, clear=False):
            client = QwenClient()
            with patch.object(
                client.client.chat.completions,
                "create",
                return_value=_fake_openai_response("Jawaban tanpa reasoning field."),
            ):
                result = client.chat([{"role": "user", "content": "hallo"}])

        self.assertEqual(result.content, "Jawaban tanpa reasoning field.")
        self.assertIsNone(result.reasoning)


if __name__ == "__main__":
    unittest.main()
