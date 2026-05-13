# Ask Data Environment Reference

This document lists the main runtime environment variables expected by the project.

Important:

- Cloudera AI runtime environment variables are the primary source of configuration.
- `.env.example` and `.env.local.example` files are documentation only and optional local fallback.

## Backend environment variables

### App

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `APP_DEBUG`
- `CORS_ALLOW_ORIGINS`

### Impala / database

- `IMPALA_HOST`
- `IMPALA_PORT`
- `IMPALA_HTTP_PATH`
- `CDP_USER`
- `CDP_PASS`
- `DB_NAME`

### Azure OpenAI

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_MODEL`

### Amazon Bedrock

- `AWS_DEFAULT_REGION`
- `BEDROCK_REGION`
- `BEDROCK_MODEL_ID`
- `BEDROCK_MODEL_NAME`
- `BEDROCK_DISCOVER_MODELS`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### RAG Studio

- `RAG_BASE_URL`
- `AGENT_BASE_URL`
- `RAG_TIMEOUT_SECONDS`

### Guardrails AI

- `GUARDRAILS_ENABLED`
- `GUARDRAILS_API_KEY`
- `GUARDRAILS_BASE_URL`
- `GUARDRAILS_FAIL_OPEN`

### Session and memory

- `SESSION_BACKEND`
- `SESSION_SQLITE_PATH`
- `SESSION_TTL_MINUTES`
- `MEMORY_MAX_HISTORY`

### Usage dashboard and observability

No dedicated environment variable is required for the current usage dashboard.

- Usage events are stored in the same SQLite file configured by `SESSION_SQLITE_PATH`
- If `SESSION_BACKEND=memory`, usage analytics also becomes in-memory and will not survive app restart
- Token figures shown in the dashboard are estimated from message length for cross-provider monitoring and are not intended to replace billing-grade accounting

### SQL safety and execution

- `SQL_DEFAULT_LIMIT`
- `SQL_MAX_PREVIEW_ROWS`
- `SQL_ALLOWED_TABLES`

### CAI backend runtime

- `PORT`
- `CDSW_APP_PORT`

## Frontend environment variables

- `NEXT_PUBLIC_API_BASE_URL`
- `BACKEND_API_BASE_URL`
- `PORT`
- `CDSW_APP_PORT`

## Notes

- The frontend must point to the backend URL using `NEXT_PUBLIC_API_BASE_URL`.
- The browser client now calls the frontend's same-origin proxy at `/api/backend`. Set `BACKEND_API_BASE_URL` on the frontend Application to the backend app URL. `NEXT_PUBLIC_API_BASE_URL` can still be used as a fallback for older frontend deployments.
- For CAI Application hosting, `CDSW_APP_PORT` should be preferred when present.
- Recommended `DB_NAME` for the current CAI demo is `cai_sdx_se_indonesia`.
- Set either `RAG_BASE_URL` or `AGENT_BASE_URL` to the RAG Studio application base URL when enabling the optional knowledge-base workflow.
- Set `GUARDRAILS_ENABLED=true` to activate request screening. `GUARDRAILS_API_KEY` is required when Guardrails is enabled.
- `GUARDRAILS_BASE_URL` is optional in the current implementation. If omitted, the app still uses built-in heuristic screening for prompt injection, sensitive-data requests, and obvious off-domain prompts.
- `GUARDRAILS_FAIL_OPEN` defaults to `true`, meaning the app will continue with local heuristics if a remote Guardrails endpoint is unreachable.
- `SESSION_BACKEND` now defaults to `sqlite`. Set `SESSION_SQLITE_PATH` if you want the session database stored outside the default `data/ask_data_sessions.db` location.
- Azure OpenAI remains the default non-RAG provider. If Bedrock credentials and model env vars are set, the frontend can offer a per-session provider switch without changing the RAG Studio flow.
- Set `BEDROCK_DISCOVER_MODELS=true` if you want the backend to fetch a live list of text-capable Bedrock foundation models for the Model Settings dropdown. If omitted or `false`, the UI falls back to the static Bedrock model entries from `BEDROCK_MODEL_ID`, `BEDROCK_MODEL_NAME`, or `BEDROCK_MODEL_CATALOG_JSON`.
- Current shared external data location is `s3a://go01-demo/user/cai-demo-se-indonesia/data/`.
- Recommended `SQL_ALLOWED_TABLES` value is `customers,deposits,credits,fraud_transactions`.
- No secrets should be hardcoded into source files.
- `CORS_ALLOW_ORIGINS` defaults to `*` for the current demo so the frontend Application can call the backend across Cloudera subdomains. Set a comma-separated allowlist later if you need stricter browser access.
