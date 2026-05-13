# Ask Data — Project State (Latest)

## Document Purpose

This document captures the full working understanding of the Ask Data project up to the latest successful state.
It is intended as a handoff/reference so work can be resumed in a new session without re-deriving context.

This version supersedes the earlier BNI-specific state and reflects the refactored general-purpose UI.

---

## 1. Executive Summary

**Use Case:** Ask the Data / Natural Language to SQL

A general-purpose AI analytics assistant that lets users ask questions about structured data in natural language.
The backend generates SQL, executes against the database, and returns a natural language answer.

The UI was originally built for a BNI banking demo and has since been refactored to a generic Cloudera-branded design,
removing all BNI-specific references so it can be reused across different banking or enterprise customers.

**Deployment target:**
- Backend as a Cloudera AI Application
- Frontend as a Cloudera AI Application

---

## 2. Demo Flow

1. User opens the frontend (Ask the Data UI)
2. User asks a question in natural language (e.g. "What is the total deposit balance right now?")
3. Frontend calls `/chat/query` for the standard SQL flow and `/chat/answer` for RAG-backed answers
4. Backend builds a prompt, generates SQL via Azure OpenAI, executes it against Impala/CDW
5. Backend returns a natural language answer plus optional visualization metadata when the SQL result is chartable
6. Frontend renders the answer in a chat-style panel and can render a chart card from the backend visualization spec

### Optional RAG Studio Flow

1. User opens the `RAG Studio` panel from the top bar
2. User enables RAG for the current chat session
3. User selects knowledge base, model, and optional advanced settings
4. Frontend saves config via backend
5. Backend creates a backing RAG session and stores it in per-session state
6. Subsequent chat requests in that session can be routed to RAG instead of the default SQL flow

---

## 3. Architecture

| Layer | Technology |
|---|---|
| Structured data | Impala / CDW |
| LLM provider | Azure OpenAI and Amazon Bedrock |
| Backend | FastAPI + Uvicorn |
| Frontend | Next.js 15 + Tailwind CSS + TypeScript |
| Deployment | Cloudera AI Applications |

### Important note
Runtime config lives in **Cloudera AI environment variables**, not in local `.env` files.
`.env.example` is documentation only.

---

## 4. Data Model

Three core tables:
- `customers`
- `deposits`
- `credits`

All join on `customer_id`. No orphan records. Date fields in `YYYY-MM-DD` format for Impala compatibility.

**Supported queries:**
- Total deposit balance
- Outstanding credit
- Top debtors by outstanding credit
- Customers per segment
- Deposits maturing in next N days
- Total deposit balance by city
- Total outstanding credit by collectibility
- Customers with both deposit and credit

---

## 5. Backend

**Stack:** FastAPI, Uvicorn, Impyla, Pydantic, OpenAI Python SDK (Azure-configured)

**Key endpoints:**
| Endpoint | Purpose |
|---|---|
| `GET /health` | App liveness check |
| `GET /health/db` | Database connectivity check |
| `GET /llm/providers` | List available non-RAG model providers for the current session |
| `POST /llm/providers/select` | Persist the active non-RAG model provider for the current session |
| `GET /rag/options` | Load available RAG Studio KB + model options |
| `GET /rag/config/{session_id}` | Load saved RAG config for one chat session |
| `POST /rag/config` | Save RAG config and create backing RAG session |
| `POST /chat/answer` | Main answer endpoint for RAG-aware chat — returns `session_id`, `original_question`, `answer`, guardrails metadata, and optional sources |
| `POST /chat/query` | SQL answer endpoint — returns answer, SQL, rows, metadata, and optional visualization spec |
| `POST /sql/generate` | SQL-only generation for debugging |

**Session memory:** SQLite-backed by default with an in-memory fallback.
This now stores per-session chat history, last SQL/result context, visualization follow-up context, provider/model selection, and RAG configuration/session IDs.
Recommended CAI backend env values for the current deployment:
- `SESSION_BACKEND=sqlite`
- `SESSION_SQLITE_PATH=data/ask_data_sessions.db`
- `SESSION_TTL_MINUTES=30`
- `MEMORY_MAX_HISTORY=10`

**Session endpoints:**
| Endpoint | Purpose |
|---|---|
| `GET /sessions` | List recent saved sessions |
| `GET /sessions/{session_id}` | Reload one saved session and its working memory |
| `GET /analytics/summary` | Read-only usage and observability summary for the recent window |
| `GET /analytics/events` | Read-only recent application activity log |

**Validation note:**
- `GET /health` now includes `session_backend`
- expected value for the current deployment is `sqlite`
- analytics logging shares the same SQLite file by default, so no additional backend service is required for observability

**CORS:** FastAPI CORSMiddleware is removed. Cloudera Application proxy handles CORS headers.
Do not re-add middleware unless thoroughly tested — it caused duplicate CORS headers in the past.

**Deployment entry:** `backend/backend_entry.py`
- Resolves paths via `os.getcwd()` (not `__file__`, which is unavailable in JupyterWSG context)
- Launches Uvicorn via `subprocess` (not `uvicorn.run()`) to avoid running event loop conflict

### Guardrails and response safety
- Optional Guardrails config is now supported through env vars:
  - `GUARDRAILS_ENABLED`
  - `GUARDRAILS_API_KEY`
  - `GUARDRAILS_BASE_URL`
  - `GUARDRAILS_FAIL_OPEN`
- If `GUARDRAILS_BASE_URL` is not set, the backend runs in `local-only` guardrails mode
- If `GUARDRAILS_BASE_URL` is set, the backend can attempt remote Guardrails validation while still honoring `GUARDRAILS_FAIL_OPEN`
- Input-side screening can block:
  - prompt injection / jailbreak-style prompts
  - obvious out-of-scope prompts
  - requests for raw sensitive customer data
  - Indonesian PII requests such as `nomor hp`, `email nasabah`, `alamat nasabah`, and `nomor rekening`
  - abusive/toxic prompts
- Output-side protection can:
  - block sensitive result-column shapes before answer narration
  - redact email / phone / long numeric identifiers from final answer text
  - return guardrails metadata for the frontend so the UI can explain blocks or redactions
- `customer_id` is now treated as an analytics identifier rather than hard-blocked PII, so ranked per-customer portfolio exploration can still work while true contact/account PII remains blocked

### Visualization generation
- Visualization intent is now generated in the backend, not guessed in the frontend
- Backend returns a visualization spec with:
  - chart `type`
  - chart `title`
  - `x_key`
  - `y_key`
  - normalized `series`
  - optional `table_columns`
  - optional `table_rows`
  - optional `insight`
- Current supported chart modes:
  - `bar` for comparisons
  - `line` for temporal trends
  - `pie` for small composition-style result sets
  - `table` for result sets that are better shown as a tabular summary
- Temporal series are now sorted in the backend before plotting
- Longer temporal series are sampled into representative points instead of simply taking the first rows returned by SQL
- Chart-oriented follow-up prompts such as `linechart aja`, `tampilkan grafik`, and `keluarkan aja` are now routed into SQL/data flow instead of being treated as generic conversation
- Visualization-only follow-up prompts such as `ubah ke barchart`, `jadikan line chart`, and `tampilkan sebagai table` now reuse the latest SQL result instead of generating a new query, so only the presentation changes
- Non-chartable query results return no visualization spec and render as answer-only

### Multi-provider model routing
- Non-RAG LLM calls can now route through either Azure OpenAI or Amazon Bedrock
- Azure remains the safe default provider when both are configured
- Provider selection is stored per session, so each conversation can keep its own active model provider
- Bedrock model selection can now be sourced in two ways:
  - static env-based catalog through `BEDROCK_MODEL_ID`, `BEDROCK_MODEL_NAME`, or `BEDROCK_MODEL_CATALOG_JSON`
  - optional live discovery from AWS Bedrock when `BEDROCK_DISCOVER_MODELS=true` and valid AWS credentials are present in the backend runtime
- Some newer Anthropic Bedrock models require invocation through an inference profile instead of direct on-demand model ID usage
- The backend now retries automatically with a region-appropriate inference profile prefix such as `us.` when Bedrock returns the specific on-demand throughput validation error for a selected model
- Current provider selection applies to:
  - SQL generation
  - SQL answer narration
  - general conversation / non-data replies
- RAG Studio remains separate and continues to use its own model configuration flow
- General conversation and greeting flows are now explicitly framed around credit risk, outstanding exposure, portfolio quality, deposit concentration, and supporting customer analysis so the opening guidance stays aligned across Azure OpenAI and Bedrock

### Usage observability
- A lightweight application event log now records:
  - chat requests
  - provider switches
  - guardrails blocks
  - visualization follow-up usage
- The logging layer is intentionally read-only from the frontend and should not interfere with chat flow if logging fails
- Current metrics include:
  - total recent sessions
  - total question volume
  - SQL vs conversation vs RAG activity
  - guardrails block count
  - visualization response count
  - provider usage breakdown
  - estimated prompt/completion token volume
- Token values are currently **estimated** from message length so they remain stable across Azure OpenAI and Bedrock without depending on provider-specific usage payloads

---

## 6. Frontend

**Stack:** Next.js 15 (App Router), Tailwind CSS 3, TypeScript, Inter + Outfit + JetBrains Mono fonts, Recharts, @mui/icons-material

### Design system
- **Sidebar:** Dark navy (`#08004D`) with indigo nav accent (`#5c63f2`) — original Cloudera palette retained
- **Background:** Light grey (`#f3f5fa`)
- **Typography:** Inter (body/labels), Outfit (all headings h1–h6), JetBrains Mono (code/numeric values)
- **Fonts:** Loaded from Google Fonts via `layout.tsx` — no external CSS import in globals
- **Icons:** All inline SVGs replaced with `@mui/icons-material` components per-component
- **Action buttons:** Orange gradient (`#FF6B00 → #E54E00`) for primary CTAs (Ask, Save, New Conversation excluded — remains indigo)
- **Radius tokens:** `--radius-panel: 16px`, `--radius-card: 16px`, `--radius-button: 8px`
- **Sidebar width:** `18rem`
- **Icon convention:** Stat/feature icons wrapped in `.icon-box` utility (orange gradient background, 32–40px)

### Branding
- Logo: Cloudera wordmark (`/Cloudera_logo.svg.png`) — centered in sidebar, `172px` wide
- Favicon: `/pavicon.png`
- App title: **Data Intelligence — Ask the Data**

### Key components
| Component | Location | Purpose |
|---|---|---|
| `BrandLogo` | `components/brand-logo.tsx` | Cloudera logo + app title in sidebar |
| `ChatInputPanel` | `components/chat-input-panel.tsx` | Textarea + submit with indigo button |
| `AnswerCard` | `components/answer-card.tsx` | Renders assistant response |
| `StarterCard` | `components/starter-card.tsx` | Clickable prompt suggestion cards |
| `NoticePanel` | `components/notice-panel.tsx` | Error / empty state notices |
| `RagConfigModal` | `components/rag-config-modal.tsx` | Per-session RAG Studio config panel |
| `UserMessageCard` | `components/user-message-card.tsx` | Branded user bubble with avatar tile |
| `ResultChartCard` | `components/result-chart-card.tsx` | Renders backend-provided chart or table visualizations with a user-toggleable view |
| `DemoBriefingModal` | `components/demo-briefing-modal.tsx` | First-open briefing modal with color-coded sections for use case, data scope, business value, and demo flow |
| `DemoGuidePanel` | `components/demo-guide-panel.tsx` | Sidebar-driven demo guide workspace inside the main body |
| `ModelSettingsPanel` | `components/model-settings-panel.tsx` | Sidebar-driven provider and model settings workspace |
| `UsageDashboardPanel` | `components/usage-dashboard-panel.tsx` | Sidebar-driven usage dashboard workspace inside the main body |
| `AppShell` | `components/ui/shell.tsx` | Layout: sidebar + topbar + main |

### UI features
- Dark navy fixed sidebar with Cloudera logo + nav
- Topbar now intentionally stays minimal and operational: database status, `Refresh status`, `RAG Studio`, `Clear Session`, and `RAG Studio ready`
- Welcome screen with Cloudera logo + 3 starter prompt cards
- First-open demo briefing modal now explains:
  - the demo use case
  - the available data scope
  - the business value
  - the recommended demo flow for sales and self-service users
- The left sidebar now includes dedicated workspace views for:
  - `Demo Guide`
  - `AI Assistant`
  - `Usage Dashboard`
  - `Model Settings`
- The first-open demo briefing popup now uses stronger section-specific color treatment so use case, data scope, business value, and demo flow are easier to distinguish at a glance
- `Demo Guide` is now also available as a persistent body section rather than only as a modal
- `Usage Dashboard` is now rendered in the main body workspace instead of a popup
- `Model Settings` is now rendered in the main body workspace instead of the top bar
- Model selection now follows a two-step workflow in the body:
  - choose the provider connection
  - choose the available model for that provider
- The preferred model setting is stored locally in the browser and then applied to the active AI session
- The `Demo Guide` body layout no longer contains an internal sidebar. It now uses:
  - a briefing hero header
  - a horizontal section selector
  - an editorial content canvas with `What To Explain`, `Suggested Flow`, and `Prompt Ideas`
- The `Demo Guide` copy has been rewritten to sound more business-facing and sales-ready, avoiding generic AI-style phrasing
- The earlier welcome-state `Self-Service Menu` cards have been removed to keep the landing experience more focused
- Chat messages: styled user bubble with human avatar + assistant answer card (white surface)
- RAG-backed answers can render a structured source list under the answer card when source metadata is available
- Assistant answers now sanitize raw RAG citation markup before rendering
- Assistant answers can render cleaner paragraphs, lists, and simple pipe-table content instead of plain monospaced text blocks
- SQL-backed answers can render backend-selected charts for trend/comparison/composition questions
- SQL-backed answers can also expose a compact summary table as an alternate visual view
- Guardrails blocks or redactions render a stronger warning notice below the assistant answer, including a policy badge, shorter copy, and safe aggregate follow-up suggestion
- Visual insight charts are now rendered with Recharts rather than custom SVG primitives
- Line charts now render with a more standard dashboard treatment:
  - responsive container with standard axes, grid, and tooltip
  - compact number formatting for large values (for example `13.3B`, `484.8B`)
  - lighter marker styling and cleaner trend presentation
  - optional switch between `Chart` and `Table` when both views are available
- Bar charts now render as a standard chart instead of a manual progress-bar list
- Composition visuals now render as a donut chart with a compact legend
- Usage Dashboard recent activity now uses pagination so the analytics workspace stays compact as event volume grows
- Usage Dashboard summary cards now use dedicated icons and a lighter operational notes treatment
- Model Settings now uses polished provider cards, a custom-styled model selector, and a lighter guidance panel instead of the earlier dark notes box
- Loading state: animated bouncing dots
- "New Conversation" button in sidebar footer resets session
- Sidebar now shows recent saved sessions from the backend store and can reopen an earlier conversation
- The `AI Model` control no longer lives in the topbar and is now managed through the dedicated `Model Settings` workspace in the sidebar
- RAG config lives in a separate modal, not in the chat input area
- Layout has been adjusted to be more responsive on narrower screens
- RAG modal locks page scroll on open, supports `Escape`/backdrop close, uses sticky header/footer, and avoids repeated option reloads to reduce visible modal flicker/glitch
- Guardrails runtime mode remains available from `/health`, but the topbar no longer shows a persistent `Guardrails Local/Remote` badge to keep the demo UI cleaner

### Starter prompts (generic, not BNI-specific)
1. "What is the total deposit balance right now?"
2. "What is the total outstanding credit right now?"
3. "Who are the customers with the highest outstanding credit?"

### API integration
- Frontend proxies backend calls through `/api/backend`
- Proxy upstream uses `BACKEND_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`
- Typed API client in `lib/api.ts`
- Standard SQL chat now calls `POST /chat/query`
- RAG-enabled chat still uses `POST /chat/answer`
- Both response types can include guardrails metadata
- SQL query responses can include backend-generated visualization specs
- Frontend can reload persisted chat history through the backend session APIs and keep the active session in local storage
- Frontend can open a read-only usage dashboard that pulls summary metrics and recent events directly from backend analytics endpoints
- Frontend can load available LLM providers and persist the provider choice per session through backend APIs
- Also calls `GET /rag/options`, `GET /rag/config/{session_id}`, and `POST /rag/config`

**Deployment entry:** `frontend/frontend_entry.py`
- Resolves port from `CDSW_APP_PORT`
- Runs dependency install/build/start and now re-installs dependencies when required modules such as `recharts` are missing from a stale `node_modules` directory in CAI

---

## 7. Known Deployment Rules

1. **Both Applications must have "Allow Unauthenticated Access" enabled** — otherwise frontend gets 302 redirects to login when calling backend
2. **Do not use `.sh` as Application script** — Cloudera Application script picker may not list `.sh` files; use Python launchers
3. **Do not re-add FastAPI CORSMiddleware** — Cloudera proxy already sets CORS headers; middleware causes duplicate headers and browser rejection
4. **Session proxy in VS Code session ≠ Application behavior** — asset path issues in session proxy do not predict Application failure

---

## 8. Environment Variables

### Backend (set in Cloudera AI)
- Impala / CDW connection: host, port, database, auth
- Azure OpenAI: endpoint, key, deployment name, model name
- Bedrock / AWS:
  - `AWS_DEFAULT_REGION` or `BEDROCK_REGION`
  - `BEDROCK_MODEL_ID`
  - `BEDROCK_MODEL_NAME`
  - Optional `BEDROCK_DISCOVER_MODELS=true` to fetch a live Bedrock model list for the Model Settings dropdown
  - Optional `BEDROCK_MODEL_CATALOG_JSON` — JSON array of `{"model_id","model_name"}` entries shown in Model Settings (server-side only; no credential exposure)
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
- `RAG_BASE_URL` or `AGENT_BASE_URL` for RAG Studio integration
- `GUARDRAILS_ENABLED`
- `GUARDRAILS_API_KEY`
- `GUARDRAILS_BASE_URL`
- `GUARDRAILS_FAIL_OPEN`
- `SESSION_BACKEND`
- `SESSION_SQLITE_PATH`
- `SESSION_TTL_MINUTES`
- `MEMORY_MAX_HISTORY`

### Frontend (set in Cloudera AI)
- `BACKEND_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL` — full URL of the backend Application

---

## 9. Current State

### UI
- [x] Fully refactored from BNI-specific to generic Cloudera-branded design
- [x] Design system aligned with fraud-ai-assistant project (same color tokens, fonts, shell layout)
- [x] All BNI references removed from UI text and prompts
- [x] Cloudera logo + favicon in place
- [x] Database status indicator (live green/red based on `/health/db`)
- [x] Latest opened datetime shown in topbar
- [x] Dedicated RAG Studio config modal implemented
- [x] `Clear Session` implemented
- [x] Responsive shell and modal behavior improved
- [x] Modal scroll locking and deferred option loading added to reduce opening glitch
- [x] RAG modal can now close via `Escape` and backdrop click, with sticky header/footer for more stable long forms
- [x] Footer actions in RAG config modal no longer easily clip off-screen
- [x] Frontend can fall back to hardcoded RAG KB/model defaults if live `/rag/options` is still failing in a stale backend deployment
- [x] Answer card supports rendering structured RAG sources instead of raw source objects
- [x] Answer card now uses SmartToy MUI icon marker instead of bot emoji
- [x] User/assistant message alignment has been adjusted to feel more balanced in wide chat layouts
- [x] Backend now sorts temporal chart data before plotting and samples longer series more intelligently
- [x] Visual insight cards can switch between chart and table views when summary rows are available
- [x] User bubble has been upgraded to a more polished human-style card with avatar marker
- [x] Frontend now renders backend-provided visualization cards for chartable SQL answers
- [x] Frontend can explain guardrails blocks or redactions inline in the chat UI
- [x] Guardrails notice UX now looks more intentional with policy-oriented wording, badges, and safer follow-up suggestions
- [x] Guardrails warning layout has been compacted so policy notices take less vertical space in chat
- [x] Session persistence now works through SQLite by default, with recent sessions shown in the sidebar
- [x] Backend CAI configuration now includes explicit SQLite session env values (`SESSION_BACKEND`, `SESSION_SQLITE_PATH`, `SESSION_TTL_MINUTES`, `MEMORY_MAX_HISTORY`)
- [x] First-open demo briefing and reusable self-service guide are now part of the frontend experience
- [x] Non-RAG model selection can now switch between Azure OpenAI and Bedrock per session
- [x] Bedrock live model discovery can populate the model list from AWS when `BEDROCK_DISCOVER_MODELS=true`
- [x] Bedrock runtime now retries newer Anthropic models through inference-profile prefixes when direct on-demand invocation is rejected
- [x] Sensitive Indonesian PII prompts such as `nomor hp`, `email nasabah`, `alamat nasabah`, and `nomor rekening` are blocked by local guardrails
- [x] `customer_id` is now allowed for ranked analytics exploration instead of being hard-blocked like direct contact/account PII
- [x] Chart rendering now uses Recharts for a more standard enterprise dashboard look and feel
- [x] Line chart values now use compact formatting to reduce clipping on large balances
- [x] Usage Dashboard recent activity is paginated and more compact
- [x] Usage Dashboard score cards now use more purposeful iconography
- [x] Sidebar and Model Settings iconography has been cleaned up to feel less generic
- [x] Topbar guardrails mode badge was removed from the visible UI; `/health` remains the source for runtime status
- [x] RAG source cards now prefer an `Open Source PDF` action instead of implying guaranteed inline preview
- [x] Typography upgraded to Inter (body) + Outfit (headings) + JetBrains Mono (code/numeric) via Google Fonts
- [x] All inline SVG icons replaced with `@mui/icons-material` across nav, cards, dashboard, and settings panels
- [x] Primary action buttons (Ask, Save) updated to orange gradient (`#FF6B00 → #E54E00`) per design system spec
- [x] Sidebar nav colors and background retained as original Cloudera indigo/navy palette
- [x] Demo Guide content rewritten with management-first framing — Business Impact is now the first section
- [x] Demo Guide sections restructured: Business Impact → Use Case → Data Scope → Demo Flow
- [x] Demo Guide copy is now scannable and outcome-focused for management-level audiences
- [x] Analytics dashboard glitch fixed — `analyticsLoadedRef` prevents re-fetch loop on tab switch
- [x] Auto-refresh after chat now only triggers when user is actively on the Usage Dashboard tab
- [x] Analytics error state resets the load ref so manual retry via Refresh button works correctly

### Backend
- [x] Implemented and deployed
- [x] Azure OpenAI integration working
- [x] Impala/CDW query execution working
- [x] `/chat/answer` endpoint working
- [x] RAG config endpoints implemented
- [x] RAG session creation working with complete payload
- [x] `/health` now reports the active session backend so SQLite activation can be validated after deploy
- [x] `/llm/providers` and `/llm/providers/select` now expose session-scoped provider selection for Azure OpenAI and Bedrock
- [x] Human-readable validation errors added for incomplete RAG config
- [x] RAG source extraction added from chat history into a structured `sources` payload for UI rendering
- [x] RAG answer text is sanitized to strip citation anchor markup before the response is sent to the frontend
- [x] Guardrails service added for input screening, output redaction, and result-shape blocking
- [x] `/health` and `/` now expose guardrails runtime mode/status
- [x] Backend visualization service now returns explicit chart specs for SQL answers
- [x] Chat router now keeps chart-related follow-up prompts in SQL/data flow instead of misclassifying them as generic conversation
- [x] `guardrails-ai` dependency added and backend test environment verified in Python 3.11
- [x] Backend tests updated and passing locally (`28 tests`)
- [x] A standalone Azure OpenAI connection test script now exists for local/runtime credential validation

### Demo readiness
- [x] End-to-end flow working
- [x] UI polished and generic enough to reuse for any banking/enterprise customer
- [x] Frontend fallback RAG defaults added:
  - Knowledge base: `BPJS-Claim-Knowledge (291)`
  - Chat model: `meta.llama3-8b-instruct-v1:0`
- [x] Source rendering support added for RAG answers
- [x] Cleaner display support added for list/table-style answers in the main chat card
- [x] Local frontend build verified successfully with the workspace-installed Node runtime
- [x] Local frontend build verified successfully after adding Recharts
- [ ] Backend runtime env vars need to be set per customer environment
- [ ] CAI backend should be redeployed with the latest guardrails + visualization changes
- [ ] CAI frontend should be redeployed with the latest visualization + guardrails UI changes, including the Recharts dependency install fix
- [ ] Until redeployed, frontend may rely on hardcoded fallback options if live `/rag/options` still fails
- [ ] RAG source card rendering depends on the exact `chat-history` payload shape returned by the target RAG Studio instance
- [ ] `Open Source PDF` behavior still depends on upstream RAG file download headers; some documents may open inline while others may download directly
- [ ] Remote Guardrails mode still requires `GUARDRAILS_BASE_URL`; otherwise backend runs in `local-only` mode
- [ ] Frontend/CAI smoke test still needed for backend-driven visualization behavior and chart-followup routing in deployed Applications

---

## 10. Resume Instructions

When resuming in a new session, assume:
1. Use case is Ask the Data / NL-to-SQL
2. UI is a generic Cloudera-branded analytics assistant (not BNI-specific)
3. Design system is shared with `fraud-ai-assistant` — adopt changes from there for consistency
4. Backend: FastAPI, deployed as CAI Application, CORS middleware removed
5. Frontend: Next.js 15, deployed as CAI Application, indigo+navy design system
6. Runtime config lives in Cloudera AI env vars — do not touch `.env.example` for runtime
7. Guardrails and backend-driven visualization are now part of the latest state
8. Major deployment blockers already solved — focus on CAI validation, polish, or feature additions

---

End of project state.
