from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    candidates = [
        Path(__file__).parents[1] / ".env",
        Path(__file__).parents[2] / ".env",
        Path(".env"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_find_env_file(), extra="ignore")

    impala_host: str = Field(alias="IMPALA_HOST")
    impala_port: int = Field(default=443, alias="IMPALA_PORT")
    impala_http_path: str = Field(default="cliservice", alias="IMPALA_HTTP_PATH")
    cdp_user: str = Field(alias="CDP_USER")
    cdp_pass: str = Field(alias="CDP_PASS")
    db_name: str = Field(default="cai_sdx_se_indonesia", alias="DB_NAME")
    aggregation_table: str = Field(default="customer_aggregation", alias="TABLE_NAME")


settings = Settings()  # type: ignore[call-arg]
