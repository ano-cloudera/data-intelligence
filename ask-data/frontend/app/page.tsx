"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import AutoStoriesIcon from "@mui/icons-material/AutoStories";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import BarChartIcon from "@mui/icons-material/BarChart";
import TuneIcon from "@mui/icons-material/Tune";
import PersonIcon from "@mui/icons-material/Person";

import { AnswerCard } from "@/components/answer-card";
import { BrandLogo } from "@/components/brand-logo";
import { ChatInputPanel } from "@/components/chat-input-panel";
import { DemoGuidePanel } from "@/components/demo-guide-panel";
import { DemoBriefingModal } from "@/components/demo-briefing-modal";
import { ModelSettingsPanel } from "@/components/model-settings-panel";
import { NoticePanel } from "@/components/notice-panel";
import { RagConfigModal } from "@/components/rag-config-modal";
import { ResultChartCard } from "@/components/result-chart-card";
import { StarterCard } from "@/components/starter-card";
import { UsageDashboardPanel } from "@/components/usage-dashboard-panel";
import { UserMessageCard } from "@/components/user-message-card";
import {
  AppShell,
  AppSidebar,
  AppTopHeader,
  PageCanvas,
} from "@/components/ui/shell";
import {
  apiClient,
  type AnswerSource,
  type ChatResponsePayload,
  type HealthResponse,
  type AnalyticsEventRecord,
  type AnalyticsSummaryResponse,
  type LLMProviderOption,
  type LLMProviderSelectionResponse,
  type RagOptionsResponse,
  type RagSessionConfig,
  type SessionStatePayload,
  type SessionSummary,
  type VisualizationSpec,
} from "@/lib/api";
import {
  createNewSessionId,
  getCurrentSessionId,
  getOrCreateSessionId,
  setCurrentSessionId,
} from "@/lib/session";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: AnswerSource[];
  metadata?: Record<string, unknown>;
  visualization?: VisualizationSpec | null;
}

interface ChatState {
  sessionId: string;
  question: string;
  messages: ChatMessage[];
  loading: boolean;
  error: string;
}

interface HealthState {
  loading: boolean;
  app: HealthResponse | null;
  db: HealthResponse | null;
  error: string;
}

interface SessionsState {
  loading: boolean;
  items: SessionSummary[];
  error: string;
}

interface LLMProvidersState {
  loading: boolean;
  options: LLMProviderOption[];
  activeProvider: string;
  activeModelName: string;
  error: string;
}

interface AnalyticsState {
  loading: boolean;
  summary: AnalyticsSummaryResponse | null;
  events: AnalyticsEventRecord[];
  error: string;
}

type AppView = "assistant" | "settings" | "usage" | "guide";

const DEMO_BRIEFING_STORAGE_KEY = "ask-data-demo-briefing-seen";
const LLM_PROVIDER_STORAGE_KEY = "ask-data-llm-provider";
const LLM_MODEL_STORAGE_KEY = "ask-data-llm-model";

const defaultRagConfig = (sessionId: string): RagSessionConfig => ({
  session_id: sessionId,
  enabled: false,
  session_name: "ask-data-rag-session",
  project_id: 1,
  knowledge_base_id: 291,
  knowledge_base_name: null,
  rag_session_id: null,
  inference_model_id: "",
  inference_model_name: null,
  rerank_model_id: null,
  rerank_model_name: null,
  response_chunks: 10,
  query_configuration: {
    enable_hyde: false,
    enable_summary_filter: true,
    enable_tool_calling: false,
    disable_streaming: false,
    selected_tools: [],
  },
});

const starterPrompts = [
  {
    title: "Total deposit balance",
    description: "View the current total deposit balance for a portfolio overview.",
    prompt: "What is the total deposit balance right now?",
  },
  {
    title: "Outstanding credit",
    description: "Summarize total outstanding credit to see current financing exposure.",
    prompt: "What is the total outstanding credit right now?",
  },
  {
    title: "Top debtors",
    description: "Find customers with the highest outstanding credit in current data.",
    prompt: "Who are the customers with the highest outstanding credit?",
  },
];

const fallbackRagOptions: RagOptionsResponse = {
  enabled: true,
  model_source: "fallback",
  chat_models: [
    {
      model_id: "meta.llama3-8b-instruct-v1:0",
      name: "Llama 3 8B Instruct",
      available: true,
      replica_count: 1,
      tool_calling_supported: false,
    },
  ],
  rerank_models: [],
  knowledge_bases: [
    {
      id: 291,
      name: "BPJS-Claim-Knowledge",
      description: "Fallback knowledge base option loaded locally while RAG options are unavailable.",
      document_count: 0,
      embedding_model: null,
      summarization_model: null,
      metadata: {
        source: "fallback",
      },
    },
  ],
};

function withFallbackRagOptions(options: RagOptionsResponse): RagOptionsResponse {
  return {
    enabled: options.enabled,
    model_source: options.model_source ?? fallbackRagOptions.model_source,
    chat_models:
      options.chat_models.length > 0 ? options.chat_models : fallbackRagOptions.chat_models,
    rerank_models:
      options.rerank_models.length > 0 ? options.rerank_models : fallbackRagOptions.rerank_models,
    knowledge_bases:
      options.knowledge_bases.length > 0
        ? options.knowledge_bases
        : fallbackRagOptions.knowledge_bases,
  };
}

function getGuardrailsNotice(metadata: Record<string, unknown> | undefined) {
  const action = typeof metadata?.guardrails_action === "string" ? metadata.guardrails_action : null;
  if (!action) return null;

  if (action === "block") {
    return {
      title: "Sensitive Data Blocked",
      message: "PII request blocked. No sensitive customer data was retrieved or shown.",
      badgeLabel: "Guardrails",
      suggestion: "Try aggregate insights by city, segment, product, or region.",
      tone: "warning" as const,
    };
  }

  if (action === "redact") {
    return {
      title: "Response Sanitized",
      message: "Sensitive values were masked before display.",
      badgeLabel: "PII Protected",
      suggestion: "Continue with aggregate or trend questions.",
      tone: "warning" as const,
    };
  }

  return null;
}

function mapStoredSessionToMessages(session: SessionStatePayload): ChatMessage[] {
  return session.messages
    .filter(
      (
        message,
      ): message is SessionStatePayload["messages"][number] & { role: "user" | "assistant" } =>
        message.role === "user" || message.role === "assistant",
    )
    .map((message, index) => ({
      id: `${message.role}-${session.session_id}-${index}-${message.timestamp}`,
      role: message.role,
      content: message.content,
    }));
}

const initialChatState: ChatState = {
  sessionId: "",
  question: "",
  messages: [],
  loading: false,
  error: "",
};

const initialSessionsState: SessionsState = {
  loading: true,
  items: [],
  error: "",
};

const initialLlmProvidersState: LLMProvidersState = {
  loading: true,
  options: [],
  activeProvider: "azure",
  activeModelName: "",
  error: "",
};

const initialAnalyticsState: AnalyticsState = {
  loading: false,
  summary: null,
  events: [],
  error: "",
};

const navItems = [
  {
    key: "guide",
    label: "Demo Guide",
    icon: <AutoStoriesIcon sx={{ fontSize: 22 }} />,
  },
  {
    key: "assistant",
    label: "AI Assistant",
    icon: <SmartToyIcon sx={{ fontSize: 22 }} />,
  },
  {
    key: "usage",
    label: "Usage Dashboard",
    icon: <BarChartIcon sx={{ fontSize: 22 }} />,
  },
  {
    key: "settings",
    label: "Model Settings",
    icon: <TuneIcon sx={{ fontSize: 22 }} />,
  },
];

const demoBriefingSections = [
  {
    id: "business-impact",
    label: "Business Impact",
    title: "Measurable Impact for Decision Makers",
    body:
      "Ask the Data compresses the time between a business question and a management-ready answer — from days to seconds. For leadership teams, that means faster decisions, fewer reporting bottlenecks, and full visibility into portfolio performance at any moment.",
    bullets: [
      "Reduce time-to-insight from days to seconds — no more waiting for the next reporting cycle to answer a board-level question.",
      "Enable live hypothesis testing during management meetings without interrupting the conversation to request a new report.",
      "Lower operational risk with governed, auditable SQL generation — every answer is traceable and defensible.",
      "Expand self-service analytics safely across business, risk, and relationship teams without exposing raw customer data.",
    ],
  },
  {
    id: "use-case",
    label: "Use Case",
    title: "Built for Portfolio & Relationship Teams",
    body:
      "This solution is designed for the moments that matter most — portfolio reviews, credit monitoring, and relationship planning. It allows business users to ask questions in plain language and receive structured, chart-ready answers instantly.",
    bullets: [
      "Portfolio review meetings — answer live follow-up questions on deposit concentration, credit exposure, and segment performance without leaving the room.",
      "Credit risk monitoring — surface outstanding credit trends, top debtors, and segment-level exposure in real time.",
      "Relationship planning — identify high-value customers by deposit balance or credit utilization across cities and segments.",
      "Compliance & governance — sensitive data requests are automatically blocked or redacted, keeping every session policy-safe.",
    ],
  },
  {
    id: "data-scope",
    label: "Data Scope",
    title: "Three Connected Data Domains",
    body:
      "The demo is anchored on three core domains — Customer, Deposit, and Credit — linked through customer relationships. This allows the audience to move seamlessly from portfolio-level questions down to segment or customer-level analysis.",
    bullets: [
      "Customer — identity, segment, city, and lifecycle attributes that provide the relationship context behind every portfolio number.",
      "Deposit — balance totals, concentration by segment and geography, maturity profile, and distribution trends.",
      "Credit — outstanding exposure, top debtor analysis, financing trend, and portfolio quality indicators.",
      "Cross-domain — questions can span all three domains in a single conversation without switching tools or context.",
    ],
  },
  {
    id: "how-to-demo",
    label: "Demo Flow",
    title: "Recommended Flow for a 15-Minute Demo",
    body:
      "Start with a number the audience already cares about, build confidence with one visual follow-up, then demonstrate governance. Keep the narrative tight — three questions are enough to show the full value of the platform.",
    bullets: [
      "Open with one aggregate question (total balance, total credit, customer count) — give the audience an immediate anchor they can validate.",
      "Follow with a trend or breakdown question to show chart generation and cross-domain continuity in the same conversation.",
      "Trigger the guardrails intentionally — ask for individual customer PII to show the system blocks it, then pivot to a safe aggregate alternative.",
      "Introduce RAG Studio only if the discussion shifts to policy or SOP questions — present it as a natural extension, not an extra feature.",
    ],
  },
] as const;

export default function HomePage() {
  const submitInFlightRef = useRef(false);
  const [state, setState] = useState<ChatState>(initialChatState);
  const [sessions, setSessions] = useState<SessionsState>(initialSessionsState);
  const [llmProviders, setLlmProviders] = useState<LLMProvidersState>(initialLlmProvidersState);
  const [analytics, setAnalytics] = useState<AnalyticsState>(initialAnalyticsState);
  const [activeView, setActiveView] = useState<AppView>("guide");
  const [draftProvider, setDraftProvider] = useState("azure");
  const [draftModelId, setDraftModelId] = useState("");
  const [savingModelSettings, setSavingModelSettings] = useState(false);
  const [demoBriefingOpen, setDemoBriefingOpen] = useState(false);
  const [activeBriefingSection, setActiveBriefingSection] = useState<string>("business-impact");
  const [health, setHealth] = useState<HealthState>({
    loading: true,
    app: null,
    db: null,
    error: "",
  });
  const [ragOptions, setRagOptions] = useState<RagOptionsResponse | null>(null);
  const [ragOptionsLoading, setRagOptionsLoading] = useState(false);
  const [ragConfig, setRagConfig] = useState<RagSessionConfig>(defaultRagConfig(""));
  const [ragPanelOpen, setRagPanelOpen] = useState(false);
  const [ragSaving, setRagSaving] = useState(false);
  const [ragConfigDirty, setRagConfigDirty] = useState(false);
  const [ragPanelPreparing, setRagPanelPreparing] = useState(false);

  useEffect(() => {
    const sessionId = getCurrentSessionId() || getOrCreateSessionId();
    setCurrentSessionId(sessionId);
    setState((cur) => ({ ...cur, sessionId }));
    setRagConfig(defaultRagConfig(sessionId));
    void loadSessionHistory(sessionId);

    const seenBriefing = window.localStorage.getItem(DEMO_BRIEFING_STORAGE_KEY);
    if (!seenBriefing) {
      setDemoBriefingOpen(true);
    }
  }, []);

  useEffect(() => {
    void refreshHealth();
  }, []);

  useEffect(() => {
    void refreshSessions();
  }, []);

  useEffect(() => {
    void ensureRagOptionsLoaded();
  }, []);

  useEffect(() => {
    if (!state.sessionId) return;
    void loadSavedRagConfig(state.sessionId);
    void loadLlmProviders(state.sessionId);
  }, [state.sessionId]);

  const analyticsLoadedRef = useRef(false);

  useEffect(() => {
    if (activeView === "usage" && !analyticsLoadedRef.current && !analytics.loading) {
      analyticsLoadedRef.current = true;
      void refreshAnalytics();
    }
  }, [activeView]);

  async function refreshHealth() {
    setHealth((cur) => ({ ...cur, loading: true, error: "" }));
    try {
      const [appHealth, dbHealth] = await Promise.all([
        apiClient.health(),
        apiClient.healthDb(),
      ]);
      setHealth({ loading: false, app: appHealth, db: dbHealth, error: "" });
    } catch (error) {
      setHealth({
        loading: false,
        app: null,
        db: null,
        error: error instanceof Error ? error.message : "Unable to reach the backend.",
      });
    }
  }

  async function refreshSessions() {
    setSessions((cur) => ({ ...cur, loading: true, error: "" }));
    try {
      const response = await apiClient.listSessions(20);
      setSessions({
        loading: false,
        items: response.sessions,
        error: "",
      });
    } catch (error) {
      setSessions({
        loading: false,
        items: [],
        error: error instanceof Error ? error.message : "Unable to load saved sessions.",
      });
    }
  }

  async function refreshAnalytics() {
    setAnalytics((cur) => ({ ...cur, loading: true, error: "" }));
    try {
      const [summary, events] = await Promise.all([
        apiClient.getAnalyticsSummary(30),
        apiClient.getAnalyticsEvents(20),
      ]);
      setAnalytics({
        loading: false,
        summary,
        events: events.events,
        error: "",
      });
    } catch (error) {
      analyticsLoadedRef.current = false;
      setAnalytics({
        loading: false,
        summary: null,
        events: [],
        error: error instanceof Error ? error.message : "Unable to load usage analytics.",
      });
    }
  }

  async function loadLlmProviders(sessionId: string) {
    setLlmProviders((cur) => ({ ...cur, loading: true, error: "" }));
    try {
      let response = await apiClient.getLlmProviders(sessionId);
      const storedProvider =
        typeof window !== "undefined" ? window.localStorage.getItem(LLM_PROVIDER_STORAGE_KEY) : null;
      const storedModelId =
        typeof window !== "undefined" ? window.localStorage.getItem(LLM_MODEL_STORAGE_KEY) : null;

      if (
        storedProvider &&
        storedProvider !== response.active_provider &&
        response.options.some((option) => option.provider === storedProvider)
      ) {
        const selected = await apiClient.selectLlmProvider({
          session_id: sessionId,
          provider: storedProvider,
          model_id:
            storedProvider === "bedrock" && storedModelId ? storedModelId : undefined,
        });
        response = {
          ...response,
          active_provider: selected.active_provider,
          active_model_id: selected.active_model_id,
          active_model_name: selected.active_model_name,
        };
      }

      const preferredProvider =
        storedProvider && response.options.some((option) => option.provider === storedProvider)
          ? storedProvider
          : response.active_provider;
      const preferredModels = response.options.filter((option) => option.provider === preferredProvider);
      const preferredModelId =
        storedModelId && preferredModels.some((option) => option.model_id === storedModelId)
          ? storedModelId
          : preferredModels[0]?.model_id || "";

      const needsBedrockModelSync =
        preferredProvider === "bedrock" &&
        Boolean(preferredModelId) &&
        response.active_model_id !== preferredModelId &&
        preferredModels.some((option) => option.model_id === preferredModelId);

      if (needsBedrockModelSync) {
        const selected = await apiClient.selectLlmProvider({
          session_id: sessionId,
          provider: "bedrock",
          model_id: preferredModelId,
        });
        response = {
          ...response,
          active_provider: selected.active_provider,
          active_model_id: selected.active_model_id,
          active_model_name: selected.active_model_name,
        };
      }

      setLlmProviders({
        loading: false,
        options: response.options,
        activeProvider: response.active_provider,
        activeModelName: response.active_model_name || "",
        error: "",
      });
      setDraftProvider(preferredProvider);
      setDraftModelId(preferredModelId);
    } catch (error) {
      setLlmProviders({
        loading: false,
        options: [],
        activeProvider: "azure",
        activeModelName: "",
        error: error instanceof Error ? error.message : "Unable to load model providers.",
      });
      setDraftProvider("azure");
      setDraftModelId("");
    }
  }

  async function handleLlmProviderChange(nextProvider: string, modelId?: string | null) {
    const sessionId = state.sessionId || getOrCreateSessionId();
    setLlmProviders((cur) => ({ ...cur, loading: true, error: "" }));
    try {
      const response: LLMProviderSelectionResponse = await apiClient.selectLlmProvider({
        session_id: sessionId,
        provider: nextProvider,
        model_id:
          nextProvider === "bedrock" && modelId ? modelId : undefined,
      });
      setLlmProviders((cur) => ({
        ...cur,
        loading: false,
        activeProvider: response.active_provider,
        activeModelName: response.active_model_name || "",
      }));
      await refreshSessions();
      if (activeView === "usage" || analytics.summary) {
        void refreshAnalytics();
      }
      return true;
    } catch (error) {
      setLlmProviders((cur) => ({
        ...cur,
        loading: false,
        error: error instanceof Error ? error.message : "Unable to switch model provider.",
      }));
      setState((cur) => ({
        ...cur,
        error: error instanceof Error ? toFriendlyErrorMessage(error.message) : "Unable to switch model provider.",
      }));
      return false;
    }
  }

  async function saveModelSettings() {
    if (!draftProvider) return;

    setSavingModelSettings(true);
    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(LLM_PROVIDER_STORAGE_KEY, draftProvider);
        if (draftModelId) {
          window.localStorage.setItem(LLM_MODEL_STORAGE_KEY, draftModelId);
        }
      }
      const saved = await handleLlmProviderChange(draftProvider, draftModelId);
      if (saved) {
        setActiveView("assistant");
      }
    } finally {
      setSavingModelSettings(false);
    }
  }

  async function loadSessionHistory(sessionId: string) {
    try {
      const response = await apiClient.getSession(sessionId);
      const restoredMessages = mapStoredSessionToMessages(response.session);
      setState((cur) => ({
        ...cur,
        sessionId,
        messages: restoredMessages,
        error: "",
      }));
    } catch {
      setState((cur) => ({ ...cur, sessionId, messages: [] }));
    }
  }

  async function handleSelectSession(sessionId: string) {
    if (!sessionId || sessionId === state.sessionId) return;
    setCurrentSessionId(sessionId);
    setActiveView("assistant");
    setState((cur) => ({
      ...cur,
      sessionId,
      question: "",
      loading: false,
      error: "",
      messages: [],
    }));
    setRagPanelOpen(false);
    setRagConfig(defaultRagConfig(sessionId));
    setRagConfigDirty(false);
    await loadSessionHistory(sessionId);
    await loadSavedRagConfig(sessionId);
  }

  async function loadRagOptions() {
    setRagOptionsLoading(true);
    try {
      const options = withFallbackRagOptions(await apiClient.ragOptions());
      setRagOptions(options);

      const preferredModel =
        options.chat_models.find((model) => model.name === "Llama 3 8B Instruct") ??
        options.chat_models[0];
      const preferredKb =
        options.knowledge_bases.find((item) => item.id === 291) ??
        options.knowledge_bases[0];

      setRagConfig((cur) => ({
        ...cur,
        knowledge_base_id: cur.knowledge_base_id ?? preferredKb?.id ?? null,
        knowledge_base_name: cur.knowledge_base_name ?? preferredKb?.name ?? null,
        inference_model_id: cur.inference_model_id || preferredModel?.model_id || "",
        inference_model_name: cur.inference_model_name ?? preferredModel?.name ?? null,
      }));
    } catch {
      setRagOptions(fallbackRagOptions);
      setRagConfig((cur) => ({
        ...cur,
        project_id: cur.project_id ?? 1,
        knowledge_base_id: cur.knowledge_base_id ?? 291,
        knowledge_base_name: cur.knowledge_base_name ?? "BPJS-Claim-Knowledge",
        inference_model_id: cur.inference_model_id || "meta.llama3-8b-instruct-v1:0",
        inference_model_name: cur.inference_model_name ?? "Llama 3 8B Instruct",
      }));
    } finally {
      setRagOptionsLoading(false);
    }
  }

  async function ensureRagOptionsLoaded() {
    if (ragOptionsLoading) return;
    if (ragOptions && ragOptions.chat_models.length > 0 && ragOptions.knowledge_bases.length > 0) {
      return;
    }
    await loadRagOptions();
  }

  async function openRagPanel() {
    if (ragPanelPreparing) return;

    const hasOptions =
      Boolean(ragOptions) &&
      (ragOptions?.chat_models.length ?? 0) > 0 &&
      (ragOptions?.knowledge_bases.length ?? 0) > 0;

    if (hasOptions) {
      setRagPanelOpen(true);
      return;
    }

    setRagPanelPreparing(true);
    try {
      await ensureRagOptionsLoaded();
      setRagPanelOpen(true);
    } finally {
      setRagPanelPreparing(false);
    }
  }

  function openGuideView(sectionId?: string) {
    if (sectionId) {
      setActiveBriefingSection(sectionId);
    }
    setActiveView("guide");
  }

  function closeDemoBriefing() {
    window.localStorage.setItem(DEMO_BRIEFING_STORAGE_KEY, "true");
    setDemoBriefingOpen(false);
  }

  async function loadSavedRagConfig(sessionId: string) {
    try {
      const saved = await apiClient.getRagConfig(sessionId);
      setRagConfig((cur) => ({
        ...cur,
        session_id: sessionId,
        enabled: saved.enabled,
        session_name: saved.session_name || cur.session_name,
        project_id: saved.project_id ?? cur.project_id ?? 1,
        knowledge_base_id: saved.knowledge_base_id ?? cur.knowledge_base_id,
        knowledge_base_name: saved.knowledge_base_name ?? cur.knowledge_base_name,
        rag_session_id: saved.rag_session_id,
        inference_model_id: saved.inference_model_id ?? cur.inference_model_id,
        inference_model_name: saved.inference_model_name ?? cur.inference_model_name,
        rerank_model_id: saved.rerank_model_id ?? cur.rerank_model_id,
        rerank_model_name: saved.rerank_model_name ?? cur.rerank_model_name,
        response_chunks: saved.response_chunks || cur.response_chunks,
        query_configuration: saved.query_configuration ?? cur.query_configuration,
      }));
      setRagConfigDirty(false);
    } catch {
      setRagConfig((cur) => ({ ...cur, session_id: sessionId }));
      setRagConfigDirty(false);
    }
  }

  function toFriendlyErrorMessage(message: string) {
    const lowered = message.toLowerCase();
    if (lowered.includes("only select queries are allowed")) {
      return "That message couldn't be processed as a data question. Try asking about deposits, outstanding credit, or customer data.";
    }
    if (lowered.includes("table access is not allowed")) {
      return "That question references data outside this demo's scope. Try focusing on deposit and credit data.";
    }
    if (lowered.includes("request failed with status 500")) {
      return "The request couldn't be processed right now. Please try again with a more specific question.";
    }
    return message;
  }

  async function submitQuestion(input: string) {
    const trimmed = input.trim();
    const sessionId = state.sessionId || getOrCreateSessionId();
    if (submitInFlightRef.current) return;
    if (!trimmed) {
      setState((cur) => ({ ...cur, error: "Please enter a question first." }));
      return;
    }
    if (ragConfig.enabled && (!ragConfig.rag_session_id || ragConfigDirty)) {
      setState((cur) => ({
        ...cur,
        error: "Save the RAG Studio configuration first before sending a knowledge-base question.",
      }));
      return;
    }

    const userMessage: ChatMessage = { id: `user-${Date.now()}`, role: "user", content: trimmed };
    submitInFlightRef.current = true;
    setState((cur) => ({
      ...cur,
      sessionId,
      question: "",
      loading: true,
      error: "",
      messages: [...cur.messages, userMessage],
    }));

    try {
      const response: ChatResponsePayload = ragConfig.enabled && ragConfig.rag_session_id
        ? { kind: "answer", ...(await apiClient.chatAnswer({ question: trimmed, session_id: sessionId })) }
        : { kind: "query", ...(await apiClient.chatQuery({ question: trimmed, session_id: sessionId })) };

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        sources: response.kind === "answer" ? response.sources ?? [] : [],
        metadata: response.metadata ?? {},
        visualization: response.visualization ?? null,
      };
      setState((cur) => ({
        ...cur,
        loading: false,
        sessionId,
        messages: [...cur.messages, assistantMessage],
      }));
    } catch (error) {
      setState((cur) => ({
        ...cur,
        loading: false,
        error: error instanceof Error ? toFriendlyErrorMessage(error.message) : "Request could not be processed right now.",
      }));
    } finally {
      submitInFlightRef.current = false;
      void refreshSessions();
      if (activeView === "usage") {
        void refreshAnalytics();
      }
    }
  }

  async function saveRagConfig() {
    if (!state.sessionId) return;

    setRagSaving(true);
    try {
      const saved = await apiClient.saveRagConfig({
        ...ragConfig,
        session_id: state.sessionId,
      });
      setRagConfig(saved);
      setRagConfigDirty(false);
      setRagPanelOpen(false);
    } catch (error) {
      setState((cur) => ({
        ...cur,
        error: error instanceof Error ? toFriendlyErrorMessage(error.message) : "Unable to save RAG configuration.",
      }));
    } finally {
      setRagSaving(false);
    }
  }

  async function handleToggleRag(enabled: boolean) {
    await ensureRagOptionsLoaded();

    const nextConfig: RagSessionConfig = {
      ...ragConfig,
      enabled,
      session_id: state.sessionId,
    };

    setRagConfig(nextConfig);
    setRagConfigDirty(enabled || ragConfigDirty);

    if (enabled) {
      void openRagPanel();
      return;
    }

    if (ragConfig.rag_session_id) {
      setRagSaving(true);
      try {
        const saved = await apiClient.saveRagConfig({
          ...nextConfig,
          rag_session_id: null,
        });
        setRagConfig(saved);
        setRagConfigDirty(false);
      } catch (error) {
        setState((cur) => ({
          ...cur,
          error: error instanceof Error ? error.message : "Unable to disable RAG configuration.",
        }));
      } finally {
        setRagSaving(false);
      }
    }
  }

  function handleNewChat() {
    const sessionId = createNewSessionId();
    setCurrentSessionId(sessionId);
    setActiveView("assistant");
    setState({ ...initialChatState, sessionId });
    setLlmProviders(initialLlmProvidersState);
    setRagConfig(defaultRagConfig(sessionId));
    setRagPanelOpen(false);
    setRagConfigDirty(false);
  }

  function handleClearSession() {
    const sessionId = createNewSessionId();
    setCurrentSessionId(sessionId);
    setState({ ...initialChatState, sessionId });
    setLlmProviders(initialLlmProvidersState);
    setRagConfig(defaultRagConfig(sessionId));
    setRagPanelOpen(false);
    setRagConfigDirty(false);
    setActiveView("assistant");
  }

  const sidebar = (
    <AppSidebar
      brand={<BrandLogo />}
      items={navItems.map((item) => ({
        ...item,
        active: item.key === activeView,
        onSelect: () => {
          setActiveView(item.key as AppView);
          if (item.key === "usage" && !analytics.summary && !analytics.loading) {
            void refreshAnalytics();
          }
        },
      }))}
      footer={
        <div className="mx-2 rounded-[18px] border border-white/8 bg-white/[0.04] p-4">
          <button
            type="button"
            onClick={handleNewChat}
            className="w-full rounded-[14px] border border-white/10 bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] py-2.5 text-sm font-semibold text-white shadow-[0_10px_20px_rgba(92,99,242,0.3)] transition hover:brightness-110"
          >
            + New Conversation
          </button>
          <div className="mt-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">
              Recent Sessions
            </p>
            <div className="mt-2 space-y-2">
              {sessions.items.slice(0, 4).map((session) => (
                <button
                  key={session.session_id}
                  type="button"
                  onClick={() => void handleSelectSession(session.session_id)}
                  className={`w-full rounded-[12px] border px-3 py-2 text-left transition ${
                    state.sessionId === session.session_id
                      ? "border-[#6c74ff] bg-white/10"
                      : "border-white/8 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.06]"
                  }`}
                >
                  <p className="truncate text-[12px] font-semibold text-white/90">{session.title}</p>
                  <p className="mt-1 truncate text-[10px] text-white/45">
                    {session.last_user_message || "Open saved conversation"}
                  </p>
                </button>
              ))}
              {!sessions.loading && sessions.items.length === 0 ? (
                <p className="rounded-[12px] border border-dashed border-white/10 px-3 py-2 text-[10px] text-white/35">
                  No saved sessions yet.
                </p>
              ) : null}
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/10">
              <PersonIcon sx={{ fontSize: 16 }} />
            </div>
            <div>
              <p className="text-xs font-semibold text-white/80">Analyst Workspace</p>
              <p className="text-[10px] text-white/40">Data Intelligence Platform</p>
            </div>
          </div>
        </div>
      }
    />
  );

  const dbStatus = health.loading
    ? "Checking…"
    : health.error
      ? "Unavailable"
      : health.db?.status === "ok"
        ? "Connected"
        : "Unavailable";

  const dbDot = health.loading
    ? "bg-amber-400"
    : health.error || health.db?.status !== "ok"
      ? "bg-rose-500"
      : "bg-emerald-400";

  const header = (
    <AppTopHeader
      left={
        <>
          <span className="meta-kicker hidden sm:block">Data Intelligence</span>
          <h2 className="font-headline text-base font-bold text-[var(--color-ink-strong)] sm:text-lg">
            Ask the Data
          </h2>
          <span className="hidden items-center gap-1.5 text-xs text-[var(--color-ink-subtle)] sm:inline-flex">
            <span className={`inline-block h-1.5 w-1.5 rounded-full ${dbDot}`} />
            Database {dbStatus}
          </span>
        </>
      }
      right={
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => void refreshHealth()}
            className="rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
          >
            Refresh status
          </button>
          <button
            type="button"
            disabled={ragPanelPreparing}
            onClick={() => void openRagPanel()}
            className={`inline-flex items-center gap-2 rounded-[var(--radius-pill)] border px-3 py-1.5 text-xs font-semibold transition ${
              ragConfig.enabled && ragConfig.rag_session_id
                ? "border-emerald-400 bg-emerald-50 text-emerald-700"
                : "border-[var(--color-border-strong)] bg-[var(--color-surface)] text-[var(--color-ink-muted)] hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
            } ${ragPanelPreparing ? "cursor-wait opacity-70" : ""}`}
          >
            <span
              className={`relative h-4 w-7 rounded-full transition ${
                ragConfig.enabled && ragConfig.rag_session_id ? "bg-emerald-500" : "bg-[#c7ccda]"
              }`}
            >
              <span
                className={`absolute top-0.5 h-3 w-3 rounded-full bg-white shadow transition ${
                  ragConfig.enabled && ragConfig.rag_session_id ? "left-3.5" : "left-0.5"
                }`}
              />
            </span>
            <span>
              {ragPanelPreparing
                ? "Opening..."
                : ragConfig.enabled && ragConfig.rag_session_id
                  ? "RAG Studio On"
                  : "RAG Studio"}
            </span>
          </button>
          <button
            type="button"
            onClick={handleClearSession}
            className="rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-rose-400 hover:text-rose-500"
          >
            Clear Session
          </button>
          {ragOptions?.enabled ? (
            <span className="hidden rounded-[var(--radius-pill)] bg-[rgba(92,99,242,0.12)] px-3 py-1.5 text-xs font-semibold text-[#4953d3] sm:inline-flex">
              RAG Studio ready
            </span>
          ) : null}
        </div>
      }
    />
  );

  return (
    <AppShell sidebar={sidebar} header={header}>
      <PageCanvas>
        {activeView === "assistant" ? (
          <div className="flex min-h-[calc(100vh-var(--space-page-y)*2-6rem)] flex-col gap-4">
            <div
              className="flex-1 overflow-y-auto rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-6 shadow-panel"
              style={{ minHeight: "400px" }}
            >
              {state.messages.length === 0 ? (
                <div className="mx-auto flex h-full max-w-4xl flex-col">
                  <section className="rounded-[18px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f5f8ff_100%)] px-8 py-10 text-center">
                    <div className="mx-auto mb-5 relative h-10 w-44">
                      <Image
                        src="/Cloudera_logo.svg.png"
                        alt="Cloudera"
                        fill
                        className="object-contain"
                        sizes="176px"
                        priority
                      />
                    </div>
                    <h3 className="font-headline text-2xl font-bold tracking-tight text-[var(--color-ink-strong)]">
                      Hello, I am the Data Analyst Assistant.
                    </h3>
                    <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-[var(--color-ink-muted)]">
                      I&apos;m here to help you analyze credit risk, outstanding exposure, portfolio quality, deposit concentration, and customer segmentation using natural language. If you need answers grounded in policy or operational documents, enable RAG Studio from the top bar first.
                    </p>
                    <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                      <button
                        type="button"
                        onClick={() => openGuideView("use-case")}
                        className="rounded-[var(--radius-pill)] bg-[var(--color-action-primary)] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[var(--color-action-primary-hover)]"
                      >
                        Open Demo Guide
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveView("settings");
                        }}
                        className="rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] bg-white px-4 py-2 text-sm font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
                      >
                        Review Model Settings
                      </button>
                    </div>
                  </section>

                  <div className="mt-6 grid gap-4 md:grid-cols-3">
                    {starterPrompts.map((item) => (
                      <StarterCard
                        key={item.title}
                        title={item.title}
                        description={item.description}
                        onClick={() => submitQuestion(item.prompt)}
                      />
                    ))}
                  </div>

                  {state.error ? (
                    <div className="mt-5">
                      <NoticePanel title="Request failed" message={state.error} tone="error" />
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
                  {state.messages.map((message) => {
                    const guardrailsNotice = getGuardrailsNotice(message.metadata);

                    return message.role === "user" ? (
                      <UserMessageCard key={message.id} content={message.content} />
                    ) : (
                      <div key={message.id} className="flex w-full flex-col items-start gap-4">
                        <AnswerCard answer={message.content} sources={message.sources} />
                        {guardrailsNotice ? (
                          <div className="w-full max-w-[56rem]">
                            <NoticePanel
                              title={guardrailsNotice.title}
                              message={guardrailsNotice.message}
                              tone={guardrailsNotice.tone}
                              badgeLabel={guardrailsNotice.badgeLabel}
                              suggestion={guardrailsNotice.suggestion}
                              compact
                            />
                          </div>
                        ) : null}
                        {message.visualization?.type ? (
                          <ResultChartCard visualization={message.visualization} />
                        ) : null}
                      </div>
                    );
                  })}

                  {state.loading ? (
                    <section className="w-full max-w-[56rem] rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-5 shadow-panel">
                      <div className="flex items-center gap-3">
                        <span className="inline-flex gap-1">
                          {[0, 1, 2].map((i) => (
                            <span
                              key={i}
                              className="inline-block h-2 w-2 animate-bounce rounded-full bg-[var(--color-action-primary)]"
                              style={{ animationDelay: `${i * 0.15}s` }}
                            />
                          ))}
                        </span>
                        <p className="text-sm text-[var(--color-ink-subtle)]">
                          Data Analyst Assistant is composing an answer…
                        </p>
                      </div>
                    </section>
                  ) : null}

                  {state.error ? (
                    <NoticePanel title="Request failed" message={state.error} tone="error" />
                  ) : null}
                </div>
              )}
            </div>

            <ChatInputPanel
              question={state.question}
              loading={state.loading}
              starterPrompts={starterPrompts.map((item) => item.prompt)}
              onQuestionChange={(question) => setState((cur) => ({ ...cur, question, error: "" }))}
              onStarterSelect={(prompt) => submitQuestion(prompt)}
              onSubmit={() => submitQuestion(state.question)}
            />
          </div>
        ) : null}

        {activeView === "guide" ? (
          <DemoGuidePanel
            sections={[...demoBriefingSections]}
            activeSectionId={activeBriefingSection}
            onSelectSection={setActiveBriefingSection}
          />
        ) : null}

        {activeView === "usage" ? (
          <UsageDashboardPanel
            loading={analytics.loading}
            error={analytics.error}
            summary={analytics.summary}
            events={analytics.events}
            onRefresh={() => {
              analyticsLoadedRef.current = true;
              void refreshAnalytics();
            }}
          />
        ) : null}

        {activeView === "settings" ? (
          <ModelSettingsPanel
            loading={llmProviders.loading}
            error={llmProviders.error}
            options={llmProviders.options}
            activeProvider={llmProviders.activeProvider}
            activeModelName={llmProviders.activeModelName}
            draftProvider={draftProvider}
            draftModelId={draftModelId}
            saving={savingModelSettings}
            onProviderChange={(provider) => {
              setDraftProvider(provider);
              const firstModel = llmProviders.options.find((option) => option.provider === provider);
              setDraftModelId(firstModel?.model_id || "");
            }}
            onModelChange={setDraftModelId}
            onSave={() => void saveModelSettings()}
          />
        ) : null}
      </PageCanvas>
      <RagConfigModal
        open={ragPanelOpen}
        saving={ragSaving}
        loadingOptions={ragOptionsLoading}
        ragAvailable={Boolean(ragOptions?.enabled)}
        ragConfigLocked={Boolean(ragConfig.enabled && ragConfig.rag_session_id && !ragConfigDirty)}
        config={ragConfig}
        chatModels={ragOptions?.chat_models ?? []}
        rerankModels={ragOptions?.rerank_models ?? []}
        knowledgeBases={ragOptions?.knowledge_bases ?? []}
        onClose={() => setRagPanelOpen(false)}
        onToggleEnabled={(enabled) => void handleToggleRag(enabled)}
        onConfigChange={(config) => {
          setRagConfig(config);
          setRagConfigDirty(true);
        }}
        onSave={() => void saveRagConfig()}
      />
      <DemoBriefingModal
        open={demoBriefingOpen}
        sections={[...demoBriefingSections]}
        activeSectionId={activeBriefingSection}
        onSelectSection={setActiveBriefingSection}
        onClose={closeDemoBriefing}
      />
    </AppShell>
  );
}
