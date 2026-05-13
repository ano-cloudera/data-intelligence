# Ask Data Frontend

This frontend is the web UI for the general analytics assistant in the CAI demo workspace.

It is designed for local development, CAI session validation, and CAI Application hosting.

## Frontend Responsibilities

- collect user questions
- keep lightweight client session continuity
- call the backend through the frontend proxy using `BACKEND_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`
- display backend and database health state
- present the answer first, with generated SQL and result previews for transparency

## Required Environment Variables

- `BACKEND_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`
- `PORT`
- `CDSW_APP_PORT`

`CDSW_APP_PORT` should be preferred in CAI Application hosting. The app falls back to `PORT`, then `3000`.

## Install And Run

```bash
npm install
npm run dev
```

## Run As A CAI Application

Preferred launcher:

```bash
python frontend_entry.py
```

Alternative launcher:

```bash
./frontend_entry.sh
```

Both launchers validate `BACKEND_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`, use CAI port conventions, and start the app for Application hosting.

## UI Expectations

When a user submits a question through `/chat/query`, the UI should show:

- a concise business answer
- generated SQL
- executed SQL
- result preview rows

This keeps the experience demo-friendly while preserving transparency for technical audiences.
