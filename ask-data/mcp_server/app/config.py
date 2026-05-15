from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Impala
    impala_host: str = Field(alias="IMPALA_HOST")
    impala_port: int = Field(default=443, alias="IMPALA_PORT")
    impala_http_path: str = Field(default="cliservice", alias="IMPALA_HTTP_PATH")
    cdp_user: str = Field(alias="CDP_USER")
    cdp_pass: str = Field(alias="CDP_PASS")
    db_name: str = Field(default="cai_sdx_se_indonesia", alias="DB_NAME")

    # ChromaDB
    chroma_persist_dir: str = Field(default="./chroma_db", alias="CHROMA_PERSIST_DIR")
    chroma_collection: str = Field(default="bankjatim_docs", alias="CHROMA_COLLECTION")
    embed_model: str = Field(default="nomic-embed-text", alias="EMBED_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")


settings = Settings()  # type: ignore[call-arg]
