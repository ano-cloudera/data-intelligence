import unittest
from unittest.mock import Mock

from app.core.config import Settings
from app.services.llm_client import BedrockClient, LLMClientError


class BedrockClientTestCase(unittest.TestCase):
    def test_retries_with_us_inference_profile_when_on_demand_not_supported(self) -> None:
        settings = Settings(
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-6-20260219-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4.6",
            AWS_ACCESS_KEY_ID="demo-key",
            AWS_SECRET_ACCESS_KEY="demo-secret",
        )

        with unittest.mock.patch("app.services.llm_client.boto3.client") as mock_boto_client:
            mock_runtime = Mock()
            mock_runtime.converse.side_effect = [
                RuntimeError(
                    "ValidationException when calling the Converse operation: "
                    "Invocation of model ID anthropic.claude-sonnet-4-6-20260219-v1:0 "
                    "with on-demand throughput isn’t supported."
                ),
                {
                    "output": {
                        "message": {
                            "content": [{"text": "ok"}],
                        }
                    }
                },
            ]
            mock_boto_client.return_value = mock_runtime

            client = BedrockClient(settings=settings, model_id=settings.bedrock_model_id)
            result = client.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(result, "ok")
        self.assertEqual(mock_runtime.converse.call_count, 2)
        self.assertEqual(
            mock_runtime.converse.call_args_list[1].kwargs["modelId"],
            "us.anthropic.claude-sonnet-4-6-20260219-v1:0",
        )

    def test_raises_error_when_retry_with_profile_also_fails(self) -> None:
        settings = Settings(
            BEDROCK_REGION="us-east-1",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-6-20260219-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4.6",
            AWS_ACCESS_KEY_ID="demo-key",
            AWS_SECRET_ACCESS_KEY="demo-secret",
        )

        with unittest.mock.patch("app.services.llm_client.boto3.client") as mock_boto_client:
            mock_runtime = Mock()
            mock_runtime.converse.side_effect = [
                RuntimeError(
                    "ValidationException when calling the Converse operation: "
                    "Invocation of model ID anthropic.claude-sonnet-4-6-20260219-v1:0 "
                    "with on-demand throughput isn’t supported."
                ),
                RuntimeError("profile invocation failed"),
            ]
            mock_boto_client.return_value = mock_runtime

            client = BedrockClient(settings=settings, model_id=settings.bedrock_model_id)

            with self.assertRaises(LLMClientError) as ctx:
                client.chat([{"role": "user", "content": "hello"}])

        self.assertIn("profile invocation failed", str(ctx.exception))

