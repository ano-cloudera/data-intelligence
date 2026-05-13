import unittest
from unittest.mock import patch

from app.core.config import Settings
from app.schemas.llm import LLMSelectionState
from app.schemas.session import SessionMemoryState
from app.services.llm_provider_service import LLMProviderService


class LLMProviderServiceTestCase(unittest.TestCase):
    def test_lists_both_azure_and_bedrock_when_configured(self) -> None:
        settings = Settings(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="demo-key",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_DEPLOYMENT="gpt-4-1-demo",
            AZURE_OPENAI_MODEL="gpt-4.1",
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
        )
        service = LLMProviderService(settings=settings)

        options = service.list_options().options

        self.assertEqual([option.provider for option in options], ["azure", "bedrock"])

    def test_resolve_selection_falls_back_to_default_when_invalid(self) -> None:
        settings = Settings(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="demo-key",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_DEPLOYMENT="gpt-4-1-demo",
            AZURE_OPENAI_MODEL="gpt-4.1",
        )
        service = LLMProviderService(settings=settings)
        memory = SessionMemoryState(
            session_id="session-1",
            llm_selection=LLMSelectionState(provider="bedrock"),
        )

        selection = service.resolve_selection(memory)

        self.assertEqual(selection.provider, "azure")
        self.assertEqual(selection.model_name, "gpt-4.1")

    def test_apply_selection_persists_bedrock_choice(self) -> None:
        settings = Settings(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="demo-key",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_DEPLOYMENT="gpt-4-1-demo",
            AZURE_OPENAI_MODEL="gpt-4.1",
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
        )
        service = LLMProviderService(settings=settings)
        session = SessionMemoryState(session_id="session-1")

        updated = service.apply_selection(session, "bedrock")

        self.assertEqual(updated.llm_selection.provider, "bedrock")
        self.assertEqual(
            updated.llm_selection.model_id,
            "anthropic.claude-sonnet-4-20250514-v1:0",
        )

    def test_bedrock_catalog_json_adds_multiple_bedrock_rows(self) -> None:
        catalog = (
            '[{"model_id":"anthropic.claude-3-5-sonnet-20240620-v1:0","model_name":"Claude 3.5 Sonnet"},'
            '{"model_id":"anthropic.claude-sonnet-4-20250514-v1:0","model_name":"Claude Sonnet 4"}]'
        )
        settings = Settings(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="demo-key",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_DEPLOYMENT="gpt-4-1-demo",
            AZURE_OPENAI_MODEL="gpt-4.1",
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
            BEDROCK_MODEL_CATALOG_JSON=catalog,
        )
        service = LLMProviderService(settings=settings)
        options = service.list_options().options

        self.assertEqual(len(options), 3)
        bedrock_ids = [o.model_id for o in options if o.provider == "bedrock"]
        self.assertEqual(
            bedrock_ids,
            [
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-sonnet-4-20250514-v1:0",
            ],
        )
        self.assertEqual(
            service.bedrock_catalog_ids(),
            {
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-sonnet-4-20250514-v1:0",
            },
        )

    def test_resolve_selection_uses_session_bedrock_model_id(self) -> None:
        settings = Settings(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="demo-key",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_DEPLOYMENT="gpt-4-1-demo",
            AZURE_OPENAI_MODEL="gpt-4.1",
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
            BEDROCK_MODEL_CATALOG_JSON=(
                '[{"model_id":"model-a","model_name":"Model A"},'
                '{"model_id":"model-b","model_name":"Model B"}]'
            ),
        )
        service = LLMProviderService(settings=settings)
        memory = SessionMemoryState(
            session_id="s1",
            llm_selection=LLMSelectionState(
                provider="bedrock",
                model_id="model-b",
                model_name=None,
            ),
        )
        sel = service.resolve_selection(memory)
        self.assertEqual(sel.provider, "bedrock")
        self.assertEqual(sel.model_id, "model-b")
        self.assertEqual(sel.model_name, "Model B")

    def test_apply_selection_sets_explicit_bedrock_model(self) -> None:
        settings = Settings(
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
            AZURE_OPENAI_API_KEY="demo-key",
            AZURE_OPENAI_API_VERSION="2024-12-01-preview",
            AZURE_OPENAI_DEPLOYMENT="gpt-4-1-demo",
            AZURE_OPENAI_MODEL="gpt-4.1",
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
            BEDROCK_MODEL_CATALOG_JSON='[{"model_id":"x-id","model_name":"X"}]',
        )
        service = LLMProviderService(settings=settings)
        session = SessionMemoryState(session_id="session-1")
        updated = service.apply_selection(session, "bedrock", "x-id")
        self.assertEqual(updated.llm_selection.model_id, "x-id")
        self.assertEqual(updated.llm_selection.model_name, "X")

    @patch("app.services.llm_provider_service.boto3.client")
    def test_bedrock_discovery_populates_provider_options(self, mock_boto_client) -> None:
        mock_boto_client.return_value.list_foundation_models.return_value = {
            "modelSummaries": [
                {
                    "modelId": "anthropic.claude-sonnet-4-20250514-v1:0",
                    "modelName": "Claude Sonnet 4",
                    "providerName": "Anthropic",
                    "inferenceTypesSupported": ["ON_DEMAND"],
                    "responseStreamingSupported": True,
                },
                {
                    "modelId": "meta.llama3-1-70b-instruct-v1:0",
                    "modelName": "Llama 3.1 70B Instruct",
                    "providerName": "Meta",
                    "inferenceTypesSupported": ["ON_DEMAND"],
                    "responseStreamingSupported": True,
                },
            ]
        }
        settings = Settings(
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
            BEDROCK_DISCOVER_MODELS=True,
            AWS_ACCESS_KEY_ID="demo-key",
            AWS_SECRET_ACCESS_KEY="demo-secret",
        )

        service = LLMProviderService(settings=settings)
        bedrock_options = [o for o in service.list_options().options if o.provider == "bedrock"]

        self.assertEqual(
            [o.model_id for o in bedrock_options],
            [
                "anthropic.claude-sonnet-4-20250514-v1:0",
                "meta.llama3-1-70b-instruct-v1:0",
            ],
        )

    @patch("app.services.llm_provider_service.boto3.client")
    def test_bedrock_discovery_failure_falls_back_to_env_catalog(self, mock_boto_client) -> None:
        mock_boto_client.side_effect = RuntimeError("bedrock unavailable")
        settings = Settings(
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="fallback-id",
            BEDROCK_MODEL_NAME="Fallback Model",
            BEDROCK_DISCOVER_MODELS=True,
            AWS_ACCESS_KEY_ID="demo-key",
            AWS_SECRET_ACCESS_KEY="demo-secret",
        )

        service = LLMProviderService(settings=settings)
        bedrock_options = [o for o in service.list_options().options if o.provider == "bedrock"]

        self.assertEqual(len(bedrock_options), 1)
        self.assertEqual(bedrock_options[0].model_id, "fallback-id")

    @patch("app.services.llm_provider_service.boto3.client")
    def test_bedrock_discovery_keeps_models_even_without_previous_filters(self, mock_boto_client) -> None:
        mock_boto_client.return_value.list_foundation_models.return_value = {
            "modelSummaries": [
                {
                    "modelId": "anthropic.claude-4-5-sonnet-20251001-v1:0",
                    "modelName": "Claude 4.5 Sonnet",
                    "providerName": "Anthropic",
                    "inferenceTypesSupported": ["INFERENCE_PROFILE"],
                    "responseStreamingSupported": False,
                },
                {
                    "modelId": "amazon.nova-premier-v1:0",
                    "modelName": "Nova Premier",
                    "providerName": "Amazon",
                    "inferenceTypesSupported": ["ON_DEMAND"],
                    "responseStreamingSupported": True,
                },
                {
                    "modelId": "amazon.nova-premier-v2:0",
                    "modelName": "Nova Premier",
                    "providerName": "Amazon",
                    "inferenceTypesSupported": ["ON_DEMAND"],
                    "responseStreamingSupported": True,
                },
            ]
        }
        settings = Settings(
            BEDROCK_REGION="us-west-2",
            BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-20250514-v1:0",
            BEDROCK_MODEL_NAME="Claude Sonnet 4",
            BEDROCK_DISCOVER_MODELS=True,
            AWS_ACCESS_KEY_ID="demo-key",
            AWS_SECRET_ACCESS_KEY="demo-secret",
        )

        service = LLMProviderService(settings=settings)
        bedrock_options = [o for o in service.list_options().options if o.provider == "bedrock"]

        self.assertEqual(
            [o.model_id for o in bedrock_options],
            [
                "anthropic.claude-4-5-sonnet-20251001-v1:0",
                "amazon.nova-premier-v1:0",
                "amazon.nova-premier-v2:0",
            ],
        )
        self.assertEqual(bedrock_options[0].model_name, "Claude 4.5 Sonnet")
        self.assertEqual(
            bedrock_options[1].model_name,
            "Nova Premier (amazon.nova-premier-v1:0)",
        )
        self.assertEqual(
            bedrock_options[2].model_name,
            "Nova Premier (amazon.nova-premier-v2:0)",
        )
