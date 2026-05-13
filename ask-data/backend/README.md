# Ask Data Backend

This backend powers the general analytics assistant for the CAI demo workspace.

It is designed to run in Cloudera AI sessions and Applications, using Impala for data access and Azure OpenAI for SQL generation and answer synthesis.

## Current Runtime Expectations

- Cloudera AI environment variables are the primary source of runtime configuration
- the current shared database is `cai_sdx_se_indonesia`
- the current allowlisted tables are `customers`, `deposits`, `credits`, and `fraud_transactions`
- final runtime validation should happen in CAI because network and auth are environment-specific

## Backend Responsibilities

- FastAPI application bootstrap
- environment-driven configuration loading
- Impala connection management
- service and database health endpoints
- Azure OpenAI-backed text-to-SQL generation
- SQL validation and execution guardrails
- preview-based answer generation
- in-memory session and conversation support

## Expected Environment Variables

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `APP_DEBUG`
- `IMPALA_HOST`
- `IMPALA_PORT`
- `IMPALA_HTTP_PATH`
- `CDP_USER`
- `CDP_PASS`
- `DB_NAME`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_MODEL`
- `RAG_BASE_URL` or `AGENT_BASE_URL`
- `RAG_TIMEOUT_SECONDS`
- `GUARDRAILS_ENABLED`
- `GUARDRAILS_API_KEY`
- `GUARDRAILS_BASE_URL`
- `GUARDRAILS_FAIL_OPEN`
- `SESSION_BACKEND`
- `SESSION_TTL_MINUTES`
- `MEMORY_MAX_HISTORY`
- `SQL_DEFAULT_LIMIT`
- `SQL_MAX_PREVIEW_ROWS`
- `SQL_ALLOWED_TABLES`

Recommended current CAI values:

- `DB_NAME=cai_sdx_se_indonesia`
- `SQL_ALLOWED_TABLES=customers,deposits,credits,fraud_transactions`

## Run Locally Or In CAI Session

```bash
pip install -r requirements.txt
python backend_session.py
```

If CAI already injects runtime variables, a local `.env` file is not required.

## Run As A CAI Application

```bash
python backend_entry.py
```

The launcher reads `CDSW_APP_PORT` first, then `PORT`, then falls back to `8080`.

## API Surface

- `GET /`
- `GET /health`
- `GET /health/db`
- `GET /tables`
- `POST /sql/generate`
- `POST /sql/execute`
- `POST /chat/query`
- `POST /chat/answer`
- `GET /rag/options`
- `GET /rag/config/{session_id}`
- `POST /rag/config`

## Behavioral Notes

- only read-only `SELECT` and `WITH ... SELECT` statements are allowed
- generated SQL is validated before execution
- dangerous keywords and multi-statement SQL are blocked
- answer generation is grounded in result previews, not hidden data access
- when `GUARDRAILS_ENABLED=true`, the backend screens prompts before SQL or RAG execution
- if `GUARDRAILS_BASE_URL` is omitted, the backend runs in `local-only` guardrails mode using built-in enterprise safety rules
- if `GUARDRAILS_BASE_URL` is set, the backend attempts remote Guardrails validation and still respects `GUARDRAILS_FAIL_OPEN`
- when RAG Studio is configured and enabled per chat session, `POST /chat/answer` can route to a saved RAG session instead of the default SQL flow
- this app remains more general-purpose than `fraud-ai-assistant`
