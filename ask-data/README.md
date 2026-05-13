# Ask Data

`ask-data` is the general-purpose analytics assistant in this workspace.

It is designed for CAI demos where a user asks business questions in natural language and the application turns them into safe read-only SQL against Impala, executes the query, and returns a concise answer plus transparent SQL and preview data.

## Current Role In This Workspace

- reusable analytics assistant for banking and fraud-adjacent analysis
- secondary project in priority compared with `fraud-ai-assistant`
- shared consumer of the common Impala demo schema
- CAI-ready app split into backend and frontend applications

## Current Shared Data Configuration

The app is aligned to the current CAI demo configuration:

- Impala database: `cai_sdx_se_indonesia`
- shared data root: `s3a://go01-demo/user/cai-demo-se-indonesia/data/`
- expected tables:
  - `customers`
  - `deposits`
  - `credits`
  - `fraud_transactions`

## What The App Does

- accepts natural language business questions
- generates safe read-only SQL with table allowlisting
- executes SQL against Impala
- summarizes preview results in natural language
- preserves lightweight session context during a conversation
- supports both banking and fraud-adjacent demo questions

## Architecture

### Backend

The backend is a FastAPI service that handles:

- runtime configuration from CAI environment variables
- Impala connectivity
- Azure OpenAI-powered SQL generation
- SQL validation and execution guardrails
- answer generation grounded in query results
- in-memory session and conversation state

Primary backend guide:

- [`backend/README.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/backend/README.md)

### Frontend

The frontend is a Next.js application that handles:

- question input and session continuity
- backend and database health display
- answer-first result presentation
- generated SQL visibility
- query result preview rendering

Primary frontend guide:

- [`frontend/README.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/frontend/README.md)

## Folder Structure

```text
ask-data/
├── backend/
├── docs/
├── frontend/
└── README.md
```

## CAI Deployment Model

This project is intended to run in Cloudera AI as two separate Applications:

- backend application via `ask-data/backend/backend_entry.py`
- frontend application via `ask-data/frontend/frontend_entry.py`

Recommended runtime assumptions:

- configuration is injected through CAI environment variables
- frontend points to the backend with `NEXT_PUBLIC_API_BASE_URL`
- the backend uses `DB_NAME=cai_sdx_se_indonesia`
- both apps are synced from GitHub and validated in CAI

## Typical Questions It Should Support

- customer balance and product mix questions
- deposit and credit summaries
- trend analysis by date or branch
- high-level fraud rate or suspicious activity exploration
- fraud distribution by channel, city, device, or segment

## Key Documentation

- project status and handoff: [`docs/project-state.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/docs/project-state.md)
- environment variables: [`docs/env.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/docs/env.md)
- setup guidance: [`docs/setup.md`](/Users/triano/Documents/Cloudera/cai-se-indo-demo/ask-data/docs/setup.md)
