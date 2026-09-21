export interface HealthResponse {
  status: string;
  service?: string;
  environment?: string;
  debug?: boolean;
  database?: string;
  session_backend?: string;
  llm_providers?: string[];
  result?: number | null;
  guardrails?: {
    enabled?: boolean;
    configured?: boolean;
    mode?: string;
    remote_endpoint_configured?: boolean;
    fail_open?: boolean;
  };
}

export interface SQLGenerateResponse {
  session_id: string | null;
  original_question: string;
  raw_generated_sql: string;
  cleaned_generated_sql: string;
  provider?: string | null;
  model: string;
  deployment: string;
}

export interface SQLExecuteResponse {
  executed_sql: string;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  truncated: boolean;
  limit_applied: boolean;
}

export interface VisualizationSpec {
  type?: "bar" | "line" | "pie" | "table" | "map" | null;
  title?: string | null;
  x_key?: string | null;
  y_key?: string | null;
  series: Array<Record<string, unknown>>;
  table_columns?: string[];
  table_rows?: Array<Record<string, unknown>>;
  insight?: string | null;
  // map fields
  metric?: string | null;
  features?: Array<Record<string, unknown>>;
}

export interface ChatQueryResponse {
  session_id: string | null;
  original_question: string;
  answer: string;
  reasoning?: string | null;
  generated_sql: string;
  executed_sql: string;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  truncated: boolean;
  limit_applied: boolean;
  metadata: Record<string, unknown>;
  visualization?: VisualizationSpec | null;
}

export interface ChatAnswerResponse {
  session_id: string | null;
  original_question: string;
  answer: string;
  reasoning?: string | null;
  mode?: string | null;
  sources?: AnswerSource[];
  metadata?: Record<string, unknown>;
  visualization?: VisualizationSpec | null;
  columns?: string[];
  rows?: Array<Record<string, unknown>>;
  row_count?: number;
  truncated?: boolean;
  limit_applied?: boolean;
}

export type ChatResponsePayload =
  | ({ kind: "answer" } & ChatAnswerResponse)
  | ({ kind: "query" } & ChatQueryResponse);

export interface AnswerSource {
  title: string;
  document_id?: string | null;
  node_id?: string | null;
  score?: number | null;
  preview_url?: string | null;
  download_url?: string | null;
  excerpt?: string | null;
}

export interface RagCollectionOption {
  name: string;
  document_count: number;
}

export interface RagOptionsResponse {
  enabled: boolean;
  collections: RagCollectionOption[];
}

export interface RagSessionConfig {
  session_id: string;
  enabled: boolean;
  collection_name: string | null;
  top_k: number;
}

export interface TableLockConfig {
  session_id: string;
  locked_table: string | null;
}

export interface TablePreviewResponse {
  status: string;
  table: string;
  columns: string[];
  rows: Array<Record<string, unknown>>;
}

export interface TablesListResponse {
  status: string;
  database: string;
  count: number;
  tables: string[];
}

export interface SessionMessage {
  role: "system" | "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ResultPreviewContext {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  truncated: boolean;
  captured_at: string;
}

export interface SessionStatePayload {
  session_id: string;
  messages: SessionMessage[];
  last_generated_sql?: string | null;
  last_answer?: string | null;
  last_result_preview?: ResultPreviewContext | null;
  last_intent?: string | null;
  llm_selection?: LLMSelectionState | null;
  rag_config?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  message_count: number;
  last_user_message?: string | null;
  last_assistant_message?: string | null;
  last_intent?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
}

export interface SessionDetailResponse {
  session: SessionStatePayload;
}

export interface LLMSelectionState {
  provider: string;
  model_id?: string | null;
  model_name?: string | null;
}

export interface LLMProviderOption {
  provider: string;
  label: string;
  model_id: string;
  model_name: string;
  available: boolean;
  description?: string | null;
}

export interface LLMProviderOptionsResponse {
  session_id?: string | null;
  active_provider: string;
  active_model_id?: string | null;
  active_model_name?: string | null;
  options: LLMProviderOption[];
  // Read-only runtime state mirroring the CAI Application env var
  // VLLM_ENABLE_THINKING. Not settable from this API.
  thinking_enabled?: boolean;
}

export interface LLMProviderSelectionResponse {
  session_id: string;
  active_provider: string;
  active_model_id?: string | null;
  active_model_name?: string | null;
}

export interface AnalyticsModeMetric {
  mode: string;
  count: number;
}

export interface AnalyticsProviderMetric {
  provider: string;
  count: number;
}

export interface AnalyticsSummaryResponse {
  window_days: number;
  total_events: number;
  total_sessions: number;
  total_questions: number;
  sql_requests: number;
  rag_requests: number;
  conversation_requests: number;
  visualization_followups: number;
  visualization_responses: number;
  guardrails_blocks: number;
  provider_selections: number;
  estimated_prompt_tokens: number;
  estimated_completion_tokens: number;
  estimated_total_tokens: number;
  mode_breakdown: AnalyticsModeMetric[];
  provider_breakdown: AnalyticsProviderMetric[];
  latest_event_at?: string | null;
}

export interface AnalyticsEventRecord {
  event_id: number;
  created_at: string;
  event_type: string;
  endpoint: string;
  session_id?: string | null;
  mode?: string | null;
  provider?: string | null;
  model_name?: string | null;
  success: boolean;
  guardrails_action?: string | null;
  visualization_type?: string | null;
  estimated_prompt_tokens: number;
  estimated_completion_tokens: number;
  estimated_total_tokens: number;
  question_excerpt?: string | null;
  metadata: Record<string, unknown>;
}

export interface AnalyticsEventsResponse {
  events: AnalyticsEventRecord[];
}

function getApiBaseUrl(): string {
  return "/api/backend";
}

function formatErrorDetail(detail: unknown): string | null {
  if (!detail) return null;
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const record = item as { loc?: unknown[]; msg?: string };
          const location = Array.isArray(record.loc) ? record.loc.join(" > ") : null;
          if (record.msg && location) return `${location}: ${record.msg}`;
          if (record.msg) return record.msg;
        }
        return null;
      })
      .filter((item): item is string => Boolean(item));

    if (messages.length > 0) return messages.join(" ");
  }

  if (typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "Request failed.";
    }
  }

  return String(detail);
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: unknown };
      const formatted = formatErrorDetail(data.detail);
      if (formatted) {
        message = formatted;
      }
    } catch {
      // Keep the default message when the backend response is not JSON.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

/**
 * Consumes the backend's SSE stream at /chat/answer/stream, dispatching
 * `event: reasoning` and `event: content` payloads to separate callbacks
 * so a caller never has to split combined text itself — the backend
 * already sends reasoning and the final answer as distinct events.
 */
async function streamChatAnswer(
  payload: { question: string; session_id?: string; mcp_server_urls?: string[] },
  handlers: {
    onReasoning?: (content: string) => void;
    onContent?: (data: ChatAnswerResponse) => void;
    onDone?: () => void;
    onError?: (error: Error) => void;
  },
): Promise<void> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/chat/answer/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!response.ok || !response.body) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line.
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const rawFrame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        let eventName = "message";
        let dataLine = "";
        for (const line of rawFrame.split("\n")) {
          if (line.startsWith("event:")) {
            eventName = line.slice("event:".length).trim();
          } else if (line.startsWith("data:")) {
            dataLine += line.slice("data:".length).trim();
          }
        }

        if (dataLine) {
          let parsed: Record<string, unknown> = {};
          try {
            parsed = JSON.parse(dataLine) as Record<string, unknown>;
          } catch {
            parsed = {};
          }

          if (eventName === "reasoning" && typeof parsed.content === "string") {
            handlers.onReasoning?.(parsed.content);
          } else if (eventName === "content") {
            handlers.onContent?.({
              session_id: (parsed.session_id as string | null) ?? null,
              original_question: payload.question,
              answer: (parsed.content as string) ?? "",
              mode: (parsed.mode as string | null) ?? undefined,
              sources: (parsed.sources as AnswerSource[]) ?? [],
              metadata: (parsed.metadata as Record<string, unknown>) ?? {},
              visualization: (parsed.visualization as VisualizationSpec | null) ?? null,
              columns: (parsed.columns as string[]) ?? [],
              rows: (parsed.rows as Array<Record<string, unknown>>) ?? [],
              row_count: (parsed.row_count as number) ?? 0,
              truncated: (parsed.truncated as boolean) ?? false,
              limit_applied: (parsed.limit_applied as boolean) ?? false,
            });
          } else if (eventName === "done") {
            handlers.onDone?.();
          }
        }

        boundary = buffer.indexOf("\n\n");
      }
    }
  } catch (error) {
    const normalized = error instanceof Error ? error : new Error(String(error));
    handlers.onError?.(normalized);
    // Always propagate to the caller too — onError is a side-channel for
    // callers that want to react inline, not a substitute for the
    // rejected promise callers already await.
    throw normalized;
  }
}

export const apiClient = {
  health: () => request<HealthResponse>("/health"),
  healthDb: () => request<HealthResponse>("/health/db"),
  generateSql: (payload: { question: string; session_id?: string }) =>
    request<SQLGenerateResponse>("/sql/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  executeSql: (payload: { sql: string; session_id?: string }) =>
    request<SQLExecuteResponse>("/sql/execute", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  chatQuery: (payload: { question: string; session_id?: string }) =>
    request<ChatQueryResponse>("/chat/query", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  chatAnswerStream: (
    payload: { question: string; session_id?: string; mcp_server_urls?: string[] },
    handlers: {
      onReasoning?: (content: string) => void;
      onContent?: (data: ChatAnswerResponse) => void;
      onDone?: () => void;
      onError?: (error: Error) => void;
    },
  ) => streamChatAnswer(payload, handlers),
  chatAnswer: (payload: { question: string; session_id?: string; mcp_server_urls?: string[] }) =>
    request<ChatAnswerResponse>("/chat/answer", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  ragOptions: () => request<RagOptionsResponse>("/rag/options"),
  getRagConfig: (sessionId: string) =>
    request<RagSessionConfig>(`/rag/config/${sessionId}`),
  saveRagConfig: (payload: RagSessionConfig) =>
    request<RagSessionConfig>("/rag/config", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  ragIngest: (payload: { collection_name: string; pdf_path: string }) =>
    request<{ status: string; chunks: number }>("/rag/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listSessions: (limit = 20) =>
    request<SessionListResponse>(`/sessions?limit=${limit}`),
  getSession: (sessionId: string) =>
    request<SessionDetailResponse>(`/sessions/${sessionId}`),
  deleteSession: (sessionId: string) =>
    request<{ status: string; session_id: string }>(`/sessions/${encodeURIComponent(sessionId)}`, {
      method: "DELETE",
    }),
  getAnalyticsSummary: (windowDays = 30) =>
    request<AnalyticsSummaryResponse>(`/analytics/summary?window_days=${windowDays}`),
  getAnalyticsEvents: (limit = 20) =>
    request<AnalyticsEventsResponse>(`/analytics/events?limit=${limit}`),
  getLlmProviders: (sessionId?: string) =>
    request<LLMProviderOptionsResponse>(
      `/llm/providers${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""}`,
    ),
  selectLlmProvider: (payload: {
    session_id: string;
    provider: string;
    model_id?: string | null;
  }) =>
    request<LLMProviderSelectionResponse>("/llm/providers/select", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTables: () => request<TablesListResponse>("/tables"),
  getTablePreview: (tableName: string) =>
    request<TablePreviewResponse>(`/tables/${encodeURIComponent(tableName)}/preview`),
  getTableLock: (sessionId: string) =>
    request<TableLockConfig>(`/table-lock/${encodeURIComponent(sessionId)}`),
  saveTableLock: (payload: TableLockConfig) =>
    request<TableLockConfig>("/table-lock", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getBaseUrl: getApiBaseUrl,
  getRiskNetwork: (customerId: string, hopDepth = 2) =>
    request<unknown>(`/graph/network?customer_id=${encodeURIComponent(customerId)}&hop_depth=${hopDepth}`),
};
