import json
from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")

    impala_host: str = Field(
        default="",
        validation_alias=AliasChoices("IMPALA_HOST"),
    )
    impala_port: int = Field(
        default=443,
        validation_alias=AliasChoices("IMPALA_PORT"),
    )
    impala_http_path: str = Field(
        default="",
        validation_alias=AliasChoices("IMPALA_HTTP_PATH"),
    )
    impala_db: str = Field(
        default="cai_sdx_se_indonesia",
        validation_alias=AliasChoices("DB_NAME", "IMPALA_DB"),
    )
    impala_user: str = Field(
        default="",
        validation_alias=AliasChoices("CDP_USER", "IMPALA_USER"),
    )
    impala_password: str = Field(
        default="",
        validation_alias=AliasChoices("CDP_PASS", "IMPALA_PASSWORD"),
    )

    azure_openai_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_ENDPOINT"),
    )
    azure_openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_API_KEY"),
    )
    azure_openai_api_version: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_API_VERSION"),
    )
    azure_openai_deployment: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_DEPLOYMENT"),
    )
    azure_openai_model: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_MODEL"),
    )
    bedrock_region: str = Field(
        default="",
        validation_alias=AliasChoices("BEDROCK_REGION", "AWS_DEFAULT_REGION"),
    )
    bedrock_model_id: str = Field(
        default="anthropic.claude-sonnet-4-20250514-v1:0",
        alias="BEDROCK_MODEL_ID",
    )
    bedrock_model_name: str = Field(
        default="",
        alias="BEDROCK_MODEL_NAME",
    )
    bedrock_discover_models: bool = Field(default=False, alias="BEDROCK_DISCOVER_MODELS")
    # Optional JSON array of {"model_id": "...", "model_name": "..."} — server-side catalog only (no AWS secrets).
    bedrock_model_catalog_json: str = Field(default="", alias="BEDROCK_MODEL_CATALOG_JSON")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    session_backend: str = Field(default="sqlite", alias="SESSION_BACKEND")
    session_sqlite_path: str = Field(
        default="data/ask_data_sessions.db",
        alias="SESSION_SQLITE_PATH",
    )
    session_ttl_minutes: int = Field(default=30, alias="SESSION_TTL_MINUTES")
    memory_max_history: int = Field(default=10, alias="MEMORY_MAX_HISTORY")
    sql_default_limit: int = Field(default=100, alias="SQL_DEFAULT_LIMIT")
    sql_max_preview_rows: int = Field(default=100, alias="SQL_MAX_PREVIEW_ROWS")
    sql_allowed_tables: str = Field(
        default="customer_dormant_segment",
        alias="SQL_ALLOWED_TABLES",
    )
    llm_provider: str = Field(default="local_qwen", alias="LLM_PROVIDER")
    qwen_base_url: str = Field(default="http://localhost:8000/v1", alias="QWEN_BASE_URL")
    qwen_model: str = Field(default="Qwen/Qwen3-8B-AWQ", alias="QWEN_MODEL")
    chroma_persist_dir: str = Field(default="./chroma_db", alias="CHROMA_PERSIST_DIR")
    chroma_enabled: bool = Field(default=False, alias="CHROMA_ENABLED")
    rag_pdf_dir: str = Field(default="./rag_pdfs", alias="RAG_PDF_DIR")
    embed_model: str = Field(default="nomic-embed-text", alias="EMBED_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    guardrails_enabled: bool = Field(default=False, alias="GUARDRAILS_ENABLED")
    guardrails_api_key: str = Field(default="", alias="GUARDRAILS_API_KEY")
    guardrails_base_url: str = Field(default="", alias="GUARDRAILS_BASE_URL")
    guardrails_fail_open: bool = Field(default=True, alias="GUARDRAILS_FAIL_OPEN")

    @property
    def is_impala_configured(self) -> bool:
        required_values = (
            self.impala_host,
            self.impala_http_path,
            self.impala_db,
            self.impala_user,
            self.impala_password,
        )
        return all(bool(value) for value in required_values)

    @property
    def is_azure_openai_configured(self) -> bool:
        required_values = (
            self.azure_openai_endpoint,
            self.azure_openai_api_key,
            self.azure_openai_api_version,
            self.azure_openai_deployment,
            self.azure_openai_model,
        )
        return all(bool(value) for value in required_values)

    @property
    def is_bedrock_configured(self) -> bool:
        required_values = (
            self.bedrock_region,
            self.bedrock_model_id,
        )
        return all(bool(value) for value in required_values)

    @property
    def bedrock_model_catalog_entries(self) -> list[tuple[str, str]]:
        """Bedrock models exposed to the UI: (model_id, display name). Falls back to BEDROCK_MODEL_ID/NAME."""
        raw = (self.bedrock_model_catalog_json or "").strip()
        if not raw:
            return [(self.bedrock_model_id, self.bedrock_model_name)]
        try:
            parsed: Any = json.loads(raw)
            if not isinstance(parsed, list):
                return [(self.bedrock_model_id, self.bedrock_model_name)]
            out: list[tuple[str, str]] = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                mid = item.get("model_id") or item.get("modelId")
                name = item.get("model_name") or item.get("modelName")
                if isinstance(mid, str) and mid.strip():
                    label = (name.strip() if isinstance(name, str) and name.strip() else mid.strip())
                    out.append((mid.strip(), label))
            return out if out else [(self.bedrock_model_id, self.bedrock_model_name)]
        except (json.JSONDecodeError, TypeError, ValueError):
            return [(self.bedrock_model_id, self.bedrock_model_name)]

    @property
    def sql_allowed_tables_list(self) -> list[str]:
        return [
            table.strip().lower()
            for table in self.sql_allowed_tables.split(",")
            if table.strip()
        ]

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ] or ["*"]

    @property
    def is_rag_configured(self) -> bool:
        if self.chroma_enabled:
            return True
        # Auto-detect: if chromadb is importable, enable RAG regardless of the flag
        try:
            import chromadb  # noqa: F401
            return True
        except ImportError:
            return False

    @property
    def is_guardrails_configured(self) -> bool:
        return self.guardrails_enabled and bool(self.guardrails_api_key.strip())

    @property
    def guardrails_mode(self) -> str:
        if not self.guardrails_enabled:
            return "disabled"
        if self.guardrails_base_url.strip():
            return "remote"
        if self.guardrails_api_key.strip():
            return "local-only"
        return "misconfigured"


@lru_cache
def get_settings() -> Settings:
    return Settings()
