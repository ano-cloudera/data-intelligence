# Ask Data Setup Guide

This guide summarizes the practical setup flow for testing and deployment in Cloudera AI.

## Runtime model

- Local development was used only for coding and file generation.
- Runtime validation is expected to happen in Cloudera AI VS Code sessions.
- Final hosting is expected to happen through Cloudera AI Applications.
- Cloudera AI runtime environment variables are the source of truth.

## Backend setup in a CAI session

```bash
cd backend
pip install -r requirements.txt
python backend_session.py
```

Notes:

- This starts the backend on `0.0.0.0`.
- It reads `APP_PORT`, then `PORT`, then falls back to `8000`.
- It avoids `uvicorn --reload`, which can be unstable in some CAI session environments.

## Create the demo schema in Impala

From a CAI session or any terminal that already has the Impala environment variables set:

```bash
cd /Users/trianonurhikmat/Documents/Works/cloudera/cai-demo
pip install -r ask-data/backend/requirements.txt
python submit_impala_schema.py
```

Notes:

- The script reads `IMPALA_HOST`, `IMPALA_PORT`, `IMPALA_HTTP_PATH`, `CDP_USER`, `CDP_PASS`, and `DB_NAME`.
- It executes every statement in `impala_demo_ddl.sql` sequentially.
- Update the `LOCATION` paths inside `impala_demo_ddl.sql` before running if your HDFS or object-storage layout is different.

## Backend setup as a CAI Application

```bash
cd backend
pip install -r requirements.txt
python backend_entry.py
```

Notes:

- This launcher reads `CDSW_APP_PORT` first, then `PORT`, then `8080`.
- It is intended for Application hosting.
- It binds to `APP_HOST` when provided, otherwise `0.0.0.0`.

## Frontend setup in a CAI session

```bash
cd frontend
npm install
npm run dev
```

Notes:

- This binds to `0.0.0.0`.
- It prefers `CDSW_APP_PORT`, then `PORT`, then `3000`.
- `NEXT_PUBLIC_API_BASE_URL` must point to the backend URL.

## Frontend setup as a CAI Application

```bash
cd frontend
python frontend_entry.py
```

Notes:

- The launcher fails clearly if `NEXT_PUBLIC_API_BASE_URL` is missing.
- It sets `PORT` from `CDSW_APP_PORT` when available.
- It installs dependencies if needed, builds the app, and starts it on `0.0.0.0`.

## Recommended validation order

1. Start the backend in a CAI session.
2. Call `GET /health`.
3. Call `GET /health/db`.
4. Test `POST /chat/query` or `POST /chat/answer`.
5. Start the frontend and point it to the backend URL.
6. Validate the end-to-end demo flow in the browser.

## Recommended Cloudera AI Application entrypoints

Backend Application:

- working directory: `ask-data/backend`
- script: `backend_entry.py`
- install command: `pip install -r requirements.txt`

Frontend Application:

- working directory: `ask-data/frontend`
- script: `frontend_entry.py`
- install command: `npm install`

## Minimum backend Application environment variables

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

Recommended:

- `APP_ENV=production`
- `APP_HOST=0.0.0.0`
- `SQL_ALLOWED_TABLES=customers,deposits,credits,fraud_transactions`

## Minimum frontend Application environment variables

- `NEXT_PUBLIC_API_BASE_URL`
