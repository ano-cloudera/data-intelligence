from __future__ import annotations

import os
from pathlib import Path

from impala.dbapi import connect


DDL_PATH = Path(__file__).resolve().parent / "impala_demo_ddl.sql"


def require_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_statements(path: Path) -> list[str]:
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(raw_line)

    content = "\n".join(lines)
    statements = [statement.strip() for statement in content.split(";") if statement.strip()]
    return statements


def main() -> None:
    impala_host = require_env("IMPALA_HOST")
    impala_port = int(require_env("IMPALA_PORT", "443"))
    impala_http_path = require_env("IMPALA_HTTP_PATH")
    impala_db = require_env("DB_NAME", "default")
    cdp_user = require_env("CDP_USER")
    cdp_pass = require_env("CDP_PASS")

    statements = load_statements(DDL_PATH)
    if not statements:
        raise RuntimeError(f"No SQL statements found in {DDL_PATH}")

    print(f"Connecting to Impala host={impala_host} db={impala_db}")
    connection = connect(
        host=impala_host,
        port=impala_port,
        database=impala_db,
        user=cdp_user,
        password=cdp_pass,
        use_ssl=True,
        auth_mechanism="PLAIN",
        http_path=impala_http_path,
        use_http_transport=True,
    )

    try:
        with connection.cursor() as cursor:
            for index, statement in enumerate(statements, start=1):
                preview = " ".join(statement.split())[:120]
                print(f"[{index}/{len(statements)}] Executing: {preview}")
                cursor.execute(statement)

                if cursor.description:
                    rows = cursor.fetchall()
                    print(f"  Returned {len(rows)} row(s)")
                    for row in rows[:5]:
                        print(f"  {row}")
    finally:
        connection.close()

    print("Schema submission completed.")


if __name__ == "__main__":
    main()
