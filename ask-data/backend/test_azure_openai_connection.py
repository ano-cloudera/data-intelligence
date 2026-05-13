from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def load_local_env() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]

    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=False)
            print(f"Loaded env file: {candidate}")
            return

    print("No local .env file found. Using runtime environment only.")



def mask(value: str | None) -> str:
    if not value:
        
        return "<missing>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def print_env_status() -> None:
    keys = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_MODEL",
    ]
    print("Azure OpenAI env status:")
    for key in keys:
        print(f"- {key}: {mask(os.getenv(key))}")


def main() -> int:
    load_local_env()
    print_env_status()

    repo_backend = Path(__file__).resolve().parent
    if str(repo_backend) not in sys.path:
        sys.path.insert(0, str(repo_backend))

    from app.core.config import Settings
    from app.services.llm_client import AzureOpenAIClient, LLMClientError

    settings = Settings()
    print(f"is_azure_openai_configured={settings.is_azure_openai_configured}")

    if not settings.is_azure_openai_configured:
        print("Azure OpenAI settings are incomplete.")
        return 1

    try:
        client = AzureOpenAIClient(settings=settings)
        response = client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "Answer in one short sentence only.",
                },
                {
                    "role": "user",
                    "content": "Introduce yourself as a banking data assistant and confirm that the Azure OpenAI deployment is reachable.",
                },
            ],
            temperature=0.0,
        )
    except LLMClientError as exc:
        print(f"Azure OpenAI test failed: {exc}")
        return 2
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return 3

    print("Azure OpenAI test succeeded.")
    print(f"Response: {response}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
