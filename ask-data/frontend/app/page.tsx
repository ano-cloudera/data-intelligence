"use client";

import { useEffect, useRef, useState } from "react";
import AutoStoriesIcon from "@mui/icons-material/AutoStories";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import BarChartIcon from "@mui/icons-material/BarChart";
import TuneIcon from "@mui/icons-material/Tune";
import PersonIcon from "@mui/icons-material/Person";

import { AnswerCard } from "@/components/answer-card";
import { BrandLogo } from "@/components/brand-logo";
import { ChatInputPanel } from "@/components/chat-input-panel";
import { DemoGuidePanel, type DemoStageContent } from "@/components/demo-guide-panel";
import { ModelSettingsPanel, type McpServer } from "@/components/model-settings-panel";
import { NoticePanel } from "@/components/notice-panel";
import { ResultChartCard } from "@/components/result-chart-card";
import { ResultGraphCard } from "@/components/result-graph-card";
import type { GraphData } from "@/components/result-graph-card";
import { ResultTableCard } from "@/components/result-table-card";
import { StarterCard, type StarterCardVariant } from "@/components/starter-card";
import dynamic from "next/dynamic";
import type { MapFeature } from "@/components/result-map-card";
const ResultMapCard = dynamic(() => import("@/components/result-map-card"), { ssr: false });
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
  type HealthResponse,
  type AnalyticsEventRecord,
  type AnalyticsSummaryResponse,
  type LLMProviderOption,
  type LLMProviderSelectionResponse,
  type RagCollectionOption,
  type RagOptionsResponse,
  type SessionStatePayload,
  type SessionSummary,
  type TableLockConfig,
  type TablePreviewResponse,
  type VisualizationSpec,
} from "@/lib/api";
import type { VectorRagConfig } from "@/components/rag-config-modal";
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
  mode?: string;
  timestamp?: string;
  sources?: AnswerSource[];
  metadata?: Record<string, unknown>;
  visualization?: VisualizationSpec | null;
  graphData?: GraphData | null;
  rows?: Array<Record<string, unknown>>;
  columns?: string[];
  row_count?: number;
  truncated?: boolean;
  limit_applied?: boolean;
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

const LLM_PROVIDER_STORAGE_KEY = "ask-data-llm-provider";
const LLM_MODEL_STORAGE_KEY = "ask-data-llm-model";

const defaultRagConfig = (): VectorRagConfig => ({
  enabled: false,
  collection_name: null,
  top_k: 3,
});

const starterPrompts: Array<{
  title: { en: string; id: string };
  description: { en: string; id: string };
  prompt: { en: string; id: string };
  variant: StarterCardVariant;
}> = [
  {
    title: { en: "Customer Segment Distribution", id: "Distribusi Segmen Nasabah" },
    description: { en: "How many customers are in each segment?", id: "Berapa nasabah di tiap segmen?" },
    prompt: { en: "Show customer count by customer segment", id: "Tampilkan jumlah nasabah berdasarkan customer segment" },
    variant: "segment",
  },
  {
    title: { en: "Dormancy Risk Breakdown", id: "Distribusi Risiko Dormant" },
    description: { en: "Distribution by dormancy risk level", id: "Distribusi berdasarkan level risiko dormant" },
    prompt: { en: "Show customer count by dormant risk level", id: "Tampilkan jumlah nasabah per dormant risk level" },
    variant: "risk",
  },
  {
    title: { en: "Campaign Recommendations", id: "Rekomendasi Kampanye" },
    description: { en: "Top campaigns for high-risk dormant customers", id: "Kampanye terbaik untuk nasabah dormant risiko tinggi" },
    prompt: { en: "What campaigns are recommended for high dormancy risk customers?", id: "Kampanye apa yang direkomendasikan untuk nasabah dormant risk high?" },
    variant: "campaign",
  },
];


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
  activeProvider: "local_qwen",
  activeModelName: "",
  error: "",
};

const initialAnalyticsState: AnalyticsState = {
  loading: false,
  summary: null,
  events: [],
  error: "",
};

const LOADING_MESSAGES: { en: string; id: string }[] = [
  { en: "Querying the database…", id: "Memuat data dari database…" },
  { en: "Analyzing 10,000+ customer records…", id: "Menganalisis 10.000+ data nasabah…" },
  { en: "Running segmentation logic…", id: "Menjalankan logika segmentasi…" },
  { en: "Generating insights…", id: "Menyusun insight…" },
  { en: "Consulting knowledge base…", id: "Memeriksa knowledge base…" },
  { en: "Composing your answer…", id: "Menyusun jawaban…" },
];

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
    label: "Settings",
    icon: <TuneIcon sx={{ fontSize: 22 }} />,
  },
];

const demoStages: readonly DemoStageContent[] = [
  {
    id: "context",
    label: { en: "Context", id: "Konteks" },
    stageTitle: { en: "Set the scene", id: "Bangun konteks" },
    say: {
      en: "Today we're looking at how a portfolio team can go from a broad question to a governed, auditable answer — in one conversation.",
      id: "Hari ini kita akan lihat bagaimana tim portfolio bisa mulai dari pertanyaan luas sampai jawaban yang aman dan bisa diaudit — dalam satu percakapan.",
    },
    ask: "Berapa jumlah nasabah per cluster segmentasi?",
    highlight: {
      en: "Natural-language question routed straight to governed SQL — no separate BI tool, no analyst hand-off.",
      id: "Pertanyaan bahasa natural langsung dirutekan ke SQL yang terkelola — tanpa tool BI terpisah, tanpa serah terima ke analis.",
    },
    transition: {
      en: "Now let's narrow from the whole portfolio down to the customers who actually need attention.",
      id: "Sekarang kita persempit dari seluruh portofolio ke nasabah yang benar-benar perlu perhatian.",
    },
    checklist: {
      en: ["Keep the opening under 30 seconds", "Frame this as a live conversation, not a report", "Name the audience pain point before asking"],
      id: ["Jaga pembukaan di bawah 30 detik", "Framing sebagai percakapan langsung, bukan laporan", "Sebutkan pain point audiens sebelum bertanya"],
    },
    focusNote: { en: "Establish the portfolio baseline.", id: "Bangun baseline portofolio." },
  },
  {
    id: "explore",
    label: { en: "Explore", id: "Eksplorasi" },
    stageTitle: { en: "Explore the risk", id: "Eksplorasi risiko" },
    say: {
      en: "Let's move from distribution to risk — who are the customers driving exposure right now?",
      id: "Mari beralih dari distribusi ke risiko — nasabah mana yang mendorong eksposur saat ini?",
    },
    ask: "Tampilkan nasabah dengan churn risk HIGH dan credit risk BAD",
    highlight: {
      en: "Compound filters generated automatically — the model composes the WHERE clause from plain language.",
      id: "Filter majemuk dibuat otomatis — model menyusun klausa WHERE dari bahasa biasa.",
    },
    transition: {
      en: "One of these customers stands out. Let's look closer at their profile.",
      id: "Salah satu nasabah ini menonjol. Mari lihat lebih dekat profilnya.",
    },
    checklist: {
      en: ["Pause on the result table", "Pick one customer to carry forward", "Connect the filter logic to a real risk policy"],
      id: ["Jeda pada tabel hasil", "Pilih satu nasabah untuk dibawa ke tahap berikutnya", "Kaitkan logika filter dengan kebijakan risiko nyata"],
    },
    focusNote: { en: "Narrow the portfolio to actionable risk.", id: "Persempit portofolio ke risiko yang bisa ditindaklanjuti." },
  },
  {
    id: "investigate",
    label: { en: "Investigate", id: "Investigasi" },
    stageTitle: { en: "Investigate the network", id: "Investigasi jaringan" },
    say: {
      en: "This is where it gets interesting — this customer's risk doesn't exist in isolation. Let's see who else is connected.",
      id: "Di sinilah menariknya — risiko nasabah ini tidak berdiri sendiri. Mari lihat siapa lagi yang terhubung.",
    },
    ask: "Tampilkan jaringan risiko untuk cif 5&(FDyJM",
    highlight: {
      en: "Graph analytics surfaces co-borrowers, guarantors, and branch clusters — contagion risk a table alone can't show.",
      id: "Graph analytics menampilkan co-borrower, guarantor, dan klaster cabang — risiko menular yang tidak terlihat dari tabel biasa.",
    },
    transition: {
      en: "Now that we see the exposure, let's find out what policy says we should do about it.",
      id: "Setelah melihat eksposurnya, mari cari tahu apa yang direkomendasikan kebijakan.",
    },
    checklist: {
      en: ["Let the graph render before narrating", "Point out contagion score, not just node count", "Tie this back to real portfolio risk"],
      id: ["Biarkan graph selesai render sebelum narasi", "Soroti contagion score, bukan cuma jumlah node", "Kaitkan kembali ke risiko portofolio nyata"],
    },
    focusNote: { en: "Show risk that only graph analytics can surface.", id: "Tunjukkan risiko yang hanya bisa dilihat lewat graph analytics." },
  },
  {
    id: "close",
    label: { en: "Close", id: "Penutup" },
    stageTitle: { en: "Close with action", id: "Tutup dengan aksi" },
    say: {
      en: "We've found the risk and understood its network — now let's turn that into a concrete next step.",
      id: "Kita sudah menemukan risiko dan memahami jaringannya — sekarang mari ubah menjadi langkah konkret.",
    },
    ask: "Kampanye apa yang paling cocok dijalankan untuk nasabah-nasabah ini?",
    highlight: {
      en: "From question to recommended campaign in one flow — no separate tooling, fully auditable end to end.",
      id: "Dari pertanyaan ke rekomendasi kampanye dalam satu alur — tanpa tooling terpisah, sepenuhnya bisa diaudit.",
    },
    transition: {
      en: "That's the full loop — explore, investigate, and act, all in one governed conversation.",
      id: "Itu satu putaran penuh — eksplorasi, investigasi, dan aksi, semua dalam satu percakapan yang terkelola.",
    },
    checklist: {
      en: ["Land on a business action, not a chart", "Recap the loop in one sentence", "Open the floor for audience questions"],
      id: ["Berhenti di aksi bisnis, bukan grafik", "Rangkum satu putaran dalam satu kalimat", "Buka sesi tanya jawab audiens"],
    },
    focusNote: { en: "End on a decision, not a dataset.", id: "Akhiri dengan keputusan, bukan dataset." },
  },
] as const;

export default function HomePage() {
  const submitInFlightRef = useRef(false);
  const [state, setState] = useState<ChatState>(initialChatState);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState<SessionsState>(initialSessionsState);
  const [llmProviders, setLlmProviders] = useState<LLMProvidersState>(initialLlmProvidersState);
  const [analytics, setAnalytics] = useState<AnalyticsState>(initialAnalyticsState);
  const [activeView, setActiveView] = useState<AppView>("guide");
  const [draftProvider, setDraftProvider] = useState("local_qwen");
  const [draftModelId, setDraftModelId] = useState("");
  const [savingModelSettings, setSavingModelSettings] = useState(false);
  const [activeBriefingSection, setActiveBriefingSection] = useState<string>("context");
  const [lang, setLang] = useState<"en" | "id">("en");
  const [health, setHealth] = useState<HealthState>({
    loading: true,
    app: null,
    db: null,
    error: "",
  });
  const [ragOptions, setRagOptions] = useState<RagOptionsResponse | null>(null);
  const [ragOptionsLoading, setRagOptionsLoading] = useState(false);
  const [ragCollections, setRagCollections] = useState<RagCollectionOption[]>([]);
  const [ragConfig, setRagConfig] = useState<VectorRagConfig>(defaultRagConfig());
  const [ragSessionId, setRagSessionId] = useState<string>("");
  const [ragSaving, setRagSaving] = useState(false);
  const [ragConfigDirty, setRagConfigDirty] = useState(false);
  const [tableLockConfig, setTableLockConfig] = useState<TableLockConfig>({ session_id: "", locked_table: null });
  const [tableLockSaving, setTableLockSaving] = useState(false);
  const [tableLockDirty, setTableLockDirty] = useState(false);
  const [availableTables, setAvailableTables] = useState<string[]>([]);
  const [tablePreviewData, setTablePreviewData] = useState<TablePreviewResponse | null>(null);
  const [tablePreviewLoading, setTablePreviewLoading] = useState(false);
  const [mcpServers, setMcpServers] = useState<McpServer[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem("mcp_servers") || "[]") as McpServer[];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    const sessionId = getCurrentSessionId() || getOrCreateSessionId();
    setCurrentSessionId(sessionId);
    setState((cur) => ({ ...cur, sessionId }));
    setRagSessionId(sessionId);
    setRagConfig(defaultRagConfig());
    void loadSessionHistory(sessionId);

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
    apiClient.listTables().then((r) => {
      setAvailableTables(r.tables);
      // Auto-lock ke tabel pertama jika belum ada lock tersimpan dan hanya satu tabel
      setTableLockConfig((cur) => {
        if (cur.locked_table === null && r.tables.length === 1) {
          return { ...cur, locked_table: r.tables[0] };
        }
        return cur;
      });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    const table = tableLockConfig.locked_table ?? availableTables[0] ?? null;
    if (!table) return;
    setTablePreviewLoading(true);
    apiClient.getTablePreview(table)
      .then((data) => setTablePreviewData(data))
      .catch(() => setTablePreviewData(null))
      .finally(() => setTablePreviewLoading(false));
  }, [tableLockConfig.locked_table, availableTables]);

  useEffect(() => {
    if (!state.sessionId) return;
    void loadSavedRagConfig(state.sessionId);
    void loadSavedTableLock(state.sessionId);
    void loadLlmProviders(state.sessionId);
  }, [state.sessionId]);

  useEffect(() => {
    if (!state.loading) { setLoadingMsgIdx(0); return; }
    const iv = setInterval(() => setLoadingMsgIdx((i) => (i + 1) % LOADING_MESSAGES.length), 2500);
    return () => clearInterval(iv);
  }, [state.loading]);

  useEffect(() => {
    const iv = setInterval(() => void refreshHealth(), 30_000);
    return () => clearInterval(iv);
  }, []);

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
        activeProvider: "local_qwen",
        activeModelName: "",
        error: error instanceof Error ? error.message : "Unable to load model providers.",
      });
      setDraftProvider("local_qwen");
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

  async function handleDeleteSession(sessionId: string) {
    try {
      await apiClient.deleteSession(sessionId);
      if (state.sessionId === sessionId) {
        handleNewChat();
      }
      await refreshSessions();
    } catch {
      // session may already be gone — refresh list anyway
      await refreshSessions();
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
    setRagConfig(defaultRagConfig());
    setRagSessionId(sessionId);
    setRagConfigDirty(false);
    setTableLockConfig({ session_id: sessionId, locked_table: null });
    setTableLockDirty(false);
    await loadSessionHistory(sessionId);
    await loadSavedRagConfig(sessionId);
    await loadSavedTableLock(sessionId);
  }

  async function loadRagOptions() {
    setRagOptionsLoading(true);
    try {
      const options = await apiClient.ragOptions();
      setRagOptions(options);
      setRagCollections(options.collections);
      if (!ragConfig.collection_name && options.collections.length > 0) {
        setRagConfig((cur) => ({
          ...cur,
          collection_name: options.collections[0].name,
        }));
      }
    } catch {
      setRagOptions({ enabled: false, collections: [] });
      setRagCollections([]);
    } finally {
      setRagOptionsLoading(false);
    }
  }

  async function ensureRagOptionsLoaded() {
    if (ragOptionsLoading) return;
    if (ragOptions !== null) return;
    await loadRagOptions();
  }

  function openGuideView(sectionId?: string) {
    if (sectionId) {
      setActiveBriefingSection(sectionId);
    }
    setActiveView("guide");
  }

  async function loadSavedRagConfig(sessionId: string) {
    try {
      const saved = await apiClient.getRagConfig(sessionId);
      setRagConfig({
        enabled: saved.enabled,
        collection_name: saved.collection_name,
        top_k: saved.top_k || 3,
      });
      setRagConfigDirty(false);
    } catch {
      setRagConfig(defaultRagConfig());
      setRagConfigDirty(false);
    }
  }

  async function loadSavedTableLock(sessionId: string) {
    try {
      const saved = await apiClient.getTableLock(sessionId);
      if (saved.locked_table) {
        setTableLockConfig({ session_id: sessionId, locked_table: saved.locked_table });
        setTableLockDirty(false);
      } else {
        // Tidak ada lock tersimpan — auto-lock ke tabel pertama jika tersedia
        const tables = await apiClient.listTables().then((r) => r.tables).catch(() => [] as string[]);
        const defaultTable = tables.length > 0 ? tables[0] : null;
        if (defaultTable) {
          await apiClient.saveTableLock({ session_id: sessionId, locked_table: defaultTable });
          setTableLockConfig({ session_id: sessionId, locked_table: defaultTable });
        } else {
          setTableLockConfig({ session_id: sessionId, locked_table: null });
        }
        setTableLockDirty(false);
      }
    } catch {
      setTableLockConfig({ session_id: sessionId, locked_table: null });
      setTableLockDirty(false);
    }
  }

  function handleMcpServersChange(servers: McpServer[]) {
    setMcpServers(servers);
    if (typeof window !== "undefined") {
      localStorage.setItem("mcp_servers", JSON.stringify(servers));
    }
  }

  async function handleMcpTest(_id: string, url: string): Promise<boolean> {
    try {
      const res = await fetch(`/api/mcp-proxy?url=${encodeURIComponent(url)}`);
      const data = await res.json();
      return data.status === "ok";
    } catch {
      return false;
    }
  }

  async function saveTableLock(overrideLockedTable?: string | null) {
    const sessionId = state.sessionId;
    if (!sessionId) return;
    const lockedTable = overrideLockedTable !== undefined ? overrideLockedTable : tableLockConfig.locked_table;
    setTableLockSaving(true);
    try {
      const saved = await apiClient.saveTableLock({
        session_id: sessionId,
        locked_table: lockedTable,
      });
      setTableLockConfig({ session_id: sessionId, locked_table: saved.locked_table });
      setTableLockDirty(false);
    } catch (error) {
      setState((cur) => ({
        ...cur,
        error: error instanceof Error ? error.message : "Unable to save table lock.",
      }));
    } finally {
      setTableLockSaving(false);
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
      // Detect graph/risk network request — accepts CUST###### ids or a cif
      // token (e.g. "5&(FDyJM") explicitly introduced by the word "cif".
      // Requires the captured token to contain at least one digit or symbol
      // so ordinary words ("dengan", "customer") never get mistaken for a cif.
      const hasGraphKeyword = /jaringan|network|risiko|risk|propagasi|terhubung|connected|graph/i.test(trimmed);
      const custIdMatch = trimmed.match(/\b(CUST\d{6,})\b/i);
      const cifMatch = trimmed.match(/\bcif\b[^\w]*([A-Za-z0-9!@#$%^&*()<>]{6,12})\b/i);
      const cifLooksValid = cifMatch ? /[0-9!@#$%^&*()<>]/.test(cifMatch[1]) : false;
      const graphMatch = custIdMatch ?? (cifLooksValid ? cifMatch : null);
      const isGraphRequest = Boolean(graphMatch) && hasGraphKeyword;

      const connectedMcpUrls = mcpServers
        .filter((s) => s.status === "connected")
        .map((s) => s.url);
      const response = await apiClient.chatAnswer({
        question: trimmed,
        session_id: sessionId,
        mcp_server_urls: connectedMcpUrls.length > 0 ? connectedMcpUrls : undefined,
      });

      // Fetch graph data if graph request detected
      let graphData: GraphData | null = null;
      if (isGraphRequest && graphMatch) {
        try {
          const rawId = graphMatch[1];
          const targetId = custIdMatch ? rawId.toUpperCase() : rawId;
          graphData = (await apiClient.getRiskNetwork(targetId, 2)) as GraphData;
        } catch {
          // graph fetch failure is non-fatal
        }
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        mode: response.mode ?? undefined,
        timestamp: new Date().toISOString(),
        sources: response.sources ?? [],
        metadata: response.metadata ?? {},
        visualization: response.visualization ?? null,
        graphData: graphData,
        rows: response.rows ?? [],
        columns: response.columns ?? [],
        row_count: response.row_count ?? 0,
        truncated: response.truncated ?? false,
        limit_applied: response.limit_applied ?? false,
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
    const sessionId = state.sessionId || ragSessionId;
    if (!sessionId) return;

    setRagSaving(true);
    try {
      const saved = await apiClient.saveRagConfig({
        session_id: sessionId,
        enabled: ragConfig.enabled,
        collection_name: ragConfig.collection_name,
        top_k: ragConfig.top_k,
      });
      setRagConfig({
        enabled: saved.enabled,
        collection_name: saved.collection_name,
        top_k: saved.top_k || 3,
      });
      setRagConfigDirty(false);
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
    setRagConfig((cur) => ({ ...cur, enabled }));
    setRagConfigDirty(true);
  }

  function handleNewChat() {
    const sessionId = createNewSessionId();
    setCurrentSessionId(sessionId);
    setActiveView("assistant");
    setState({ ...initialChatState, sessionId });
    setLlmProviders(initialLlmProvidersState);
    setRagConfig(defaultRagConfig());
    setRagSessionId(sessionId);
    setRagConfigDirty(false);
    setTableLockConfig({ session_id: sessionId, locked_table: null });
    setTableLockDirty(false);
  }

  function handleClearSession() {
    const sessionId = createNewSessionId();
    setCurrentSessionId(sessionId);
    setState({ ...initialChatState, sessionId });
    setLlmProviders(initialLlmProvidersState);
    setRagConfig(defaultRagConfig());
    setRagSessionId(sessionId);
    setRagConfigDirty(false);
    setTableLockConfig({ session_id: sessionId, locked_table: null });
    setTableLockDirty(false);
    setActiveView("assistant");
  }

  const sidebar = (
    <AppSidebar
      brand={<BrandLogo />}
      mobileOpen={mobileSidebarOpen}
      onMobileClose={() => setMobileSidebarOpen(false)}
      items={navItems.map((item) => ({
        ...item,
        active: item.key === activeView,
        onSelect: () => {
          setActiveView(item.key as AppView);
          setMobileSidebarOpen(false);
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
            <div className="mt-2 max-h-[220px] space-y-2 overflow-y-auto pr-0.5 scrollbar-thin">
              {sessions.items.map((session) => (
                <div
                  key={session.session_id}
                  className={`group relative flex items-center rounded-[12px] border transition ${
                    state.sessionId === session.session_id
                      ? "border-[#6c74ff] bg-white/10"
                      : "border-white/8 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.06]"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => void handleSelectSession(session.session_id)}
                    className="min-w-0 flex-1 px-3 py-2 text-left"
                  >
                    <p className="truncate text-[12px] font-semibold text-white/90">{session.title}</p>
                    <p className="mt-1 truncate text-[10px] text-white/45">
                      {session.last_user_message || "Open saved conversation"}
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); void handleDeleteSession(session.session_id); }}
                    className="mr-1.5 shrink-0 rounded-[8px] p-1 text-white/30 transition hover:bg-white/10 hover:text-rose-400"
                    title="Delete conversation"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6M14 11v6" /><path d="M9 6V4h6v2" />
                    </svg>
                  </button>
                </div>
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
          <div className="relative mt-3">
            <button
              type="button"
              onClick={() => setShowClearConfirm((v) => !v)}
              className="w-full rounded-[12px] border border-white/10 py-1.5 text-[11px] font-semibold text-white/40 transition hover:border-rose-400/40 hover:text-rose-400"
            >
              {lang === "id" ? "Bersihkan Sesi" : "Clear Session"}
            </button>
            {showClearConfirm ? (
              <div className="absolute bottom-full left-0 right-0 z-50 mb-2 rounded-[16px] border border-rose-200 bg-white p-3 shadow-lg">
                <p className="mb-2.5 text-xs font-semibold text-[var(--color-ink-strong)]">
                  {lang === "id" ? "Hapus semua chat?" : "Clear all messages?"}
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowClearConfirm(false)}
                    className="flex-1 rounded-[10px] border border-[var(--color-border-strong)] bg-white py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:bg-[var(--color-surface-muted)]"
                  >
                    {lang === "id" ? "Batal" : "Cancel"}
                  </button>
                  <button
                    type="button"
                    onClick={() => { handleClearSession(); setShowClearConfirm(false); }}
                    className="flex-1 rounded-[10px] bg-rose-500 py-1.5 text-xs font-semibold text-white transition hover:bg-rose-600"
                  >
                    {lang === "id" ? "Hapus" : "Clear"}
                  </button>
                </div>
              </div>
            ) : null}
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
      onMenuClick={() => setMobileSidebarOpen(true)}
      left={
        <>
          <h2 className="font-headline text-base font-bold text-[var(--color-ink-strong)] sm:text-lg">
            Data Intelligence Assistant
          </h2>
          <span className="hidden items-center gap-1.5 text-xs text-[var(--color-ink-subtle)] sm:inline-flex">
            <span className={`inline-block h-1.5 w-1.5 rounded-full ${dbDot}`} />
            Database {dbStatus}
          </span>
        </>
      }
      right={
        <div className="flex items-center gap-3">
          <div className="flex items-center rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] bg-[var(--color-surface)] p-0.5">
            <button
              type="button"
              onClick={() => setLang("en")}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${lang === "en" ? "bg-[var(--color-action-primary)] text-white shadow" : "text-[var(--color-ink-muted)] hover:text-[var(--color-action-primary)]"}`}
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => setLang("id")}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${lang === "id" ? "bg-[var(--color-action-primary)] text-white shadow" : "text-[var(--color-ink-muted)] hover:text-[var(--color-action-primary)]"}`}
            >
              ID
            </button>
          </div>
        </div>
      }
    />
  );

  return (
    <AppShell sidebar={sidebar} header={header}>
      <PageCanvas>
        {activeView === "assistant" ? (
          <div className="flex min-h-[calc(100vh-var(--space-page-y)*2-6rem)] flex-col">
            <div
              className="flex-1 overflow-y-auto"
              style={{ minHeight: "400px" }}
            >
              {state.messages.length === 0 ? (
                <div className="workspace-fade-in mx-auto flex h-full max-w-[820px] flex-col justify-center py-12">
                  {/* Workspace label */}
                  <p className="text-center text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--color-ink-subtle)]">
                    {lang === "id" ? "Ruang Kerja Analis" : "Analyst Workspace"}
                  </p>

                  {/* Short natural heading */}
                  <h1 className="mt-2 text-center font-headline text-[26px] font-bold leading-tight tracking-tight text-[var(--color-ink-strong)]">
                    {lang === "id" ? "Apa yang ingin Anda periksa hari ini?" : "What would you like to explore?"}
                  </h1>
                  <p className="mt-1.5 text-center text-[13px] text-[var(--color-ink-subtle)]">
                    {lang === "id"
                      ? "Tanyakan tentang nasabah, transaksi, segmen, atau dokumen kebijakan."
                      : "Ask about customers, transactions, segments, or policy documents."}
                  </p>

                  {/* Composer — focal point */}
                  <div className="mt-7">
                    <ChatInputPanel
                      question={state.question}
                      loading={state.loading}
                      starterPrompts={starterPrompts.map((item) => item.prompt[lang])}
                      onQuestionChange={(question) => setState((cur) => ({ ...cur, question, error: "" }))}
                      onStarterSelect={(prompt) => submitQuestion(prompt)}
                      onSubmit={() => submitQuestion(state.question)}
                      placeholder={lang === "id" ? "Ajukan pertanyaan tentang data nasabah Anda..." : "Ask a question about your customer data..."}
                    />
                    <div className="mt-2 flex items-center justify-center gap-1.5 text-[11px] text-[var(--color-ink-subtle)]">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
                      {lang === "id" ? "Terhubung ke data warehouse Bank XYZ" : "Connected to Bank XYZ data warehouse"}
                    </div>
                  </div>

                  {/* Suggested questions — compact shortcut list, not promo cards */}
                  <div className="mt-8 rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface)]">
                    <p className="px-3 pt-3 pb-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--color-ink-subtle)]">
                      {lang === "id" ? "Pertanyaan yang Disarankan" : "Suggested Questions"}
                    </p>
                    <div className="divide-y divide-[var(--color-border-soft)] px-1 pb-1">
                      {starterPrompts.map((item) => (
                        <StarterCard
                          key={item.title.en}
                          title={item.title[lang]}
                          description={item.description[lang]}
                          onClick={() => submitQuestion(item.prompt[lang])}
                          variant={item.variant}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Data scope — small, not a KPI card */}
                  <p className="mt-4 text-center text-[11px] text-[var(--color-ink-subtle)]">
                    {lang === "id" ? "Cakupan data: " : "Available data: "}
                    <span className="font-medium text-[var(--color-ink-muted)]">10K+ {lang === "id" ? "nasabah" : "customers"}</span>
                    {" · "}
                    <span className="font-medium text-[var(--color-ink-muted)]">7 {lang === "id" ? "segmen" : "segments"}</span>
                    {" · "}
                    <span className="font-medium text-[var(--color-ink-muted)]">57 {lang === "id" ? "dokumen" : "documents"}</span>
                  </p>

                  {state.error ? (
                    <div className="mt-5">
                      <NoticePanel title="Request failed" message={state.error} tone="error" />
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="workspace-fade-in mx-auto flex w-full max-w-5xl flex-col gap-5 px-1 py-5">
                  {state.messages.map((message) => {
                    const guardrailsNotice = getGuardrailsNotice(message.metadata);

                    return message.role === "user" ? (
                      <UserMessageCard key={message.id} content={message.content} />
                    ) : (
                      <div key={message.id} className="flex w-full flex-col items-start gap-4">
                        <AnswerCard answer={message.content} sources={message.sources} mode={message.mode} timestamp={message.timestamp} lang={lang} />
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
                        {message.visualization?.type === "map" ? (
                          <div className="w-full max-w-[56rem]">
                            <ResultMapCard
                              features={(message.visualization.features ?? []) as unknown as MapFeature[]}
                              metric={message.visualization.metric ?? "total"}
                            />
                          </div>
                        ) : message.visualization?.type ? (
                          <ResultChartCard visualization={message.visualization} />
                        ) : null}
                        {message.graphData && (
                          <div className="w-full max-w-[56rem]">
                            <ResultGraphCard data={message.graphData} />
                          </div>
                        )}
                        {!message.visualization?.type && (message.rows?.length ?? 0) > 0 && (message.columns?.length ?? 0) > 0 ? (
                          <div className="w-full max-w-[56rem]">
                            <ResultTableCard
                              columns={message.columns!}
                              rows={message.rows!}
                              rowCount={message.row_count ?? message.rows!.length}
                              truncated={message.truncated ?? false}
                              limitApplied={message.limit_applied ?? false}
                            />
                          </div>
                        ) : null}
                      </div>
                    );
                  })}

                  {state.loading ? (
                    <div className="flex w-full max-w-[56rem] items-center gap-2.5 px-1">
                      <span className="inline-flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <span
                            key={i}
                            className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--color-action-primary)]"
                            style={{ animation: `pulse-dot 1.2s ease-in-out infinite`, animationDelay: `${i * 0.15}s` }}
                          />
                        ))}
                      </span>
                      <p key={loadingMsgIdx} className="text-[13px] text-[var(--color-ink-subtle)]">
                        {LOADING_MESSAGES[loadingMsgIdx][lang]}
                      </p>
                    </div>
                  ) : null}

                  {state.error ? (
                    <NoticePanel title="Request failed" message={state.error} tone="error" />
                  ) : null}
                </div>
              )}
            </div>

            {state.messages.length > 0 ? (
              <div className="sticky bottom-0 mx-auto w-full max-w-5xl border-t border-[var(--color-border-soft)] bg-[var(--color-page-bg)] px-1 pb-4 pt-3">
                <ChatInputPanel
                  question={state.question}
                  loading={state.loading}
                  starterPrompts={starterPrompts.map((item) => item.prompt[lang])}
                  onQuestionChange={(question) => setState((cur) => ({ ...cur, question, error: "" }))}
                  onStarterSelect={(prompt) => submitQuestion(prompt)}
                  onSubmit={() => submitQuestion(state.question)}
                  placeholder={lang === "id" ? "Ajukan pertanyaan lanjutan..." : "Ask a follow-up question..."}
                />
              </div>
            ) : null}
          </div>
        ) : null}

        {activeView === "guide" ? (
          <DemoGuidePanel
            stages={demoStages}
            activeStageId={activeBriefingSection}
            onSelectStage={setActiveBriefingSection}
            lang={lang}
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
            lang={lang}
            ragConfig={ragConfig}
            ragOptions={ragOptions}
            ragOptionsLoading={ragOptionsLoading}
            ragCollections={ragCollections}
            ragSaving={ragSaving}
            ragConfigLocked={Boolean(ragConfig.enabled && ragConfig.collection_name && !ragConfigDirty)}
            onProviderChange={(provider) => {
              setDraftProvider(provider);
              const firstModel = llmProviders.options.find((option) => option.provider === provider);
              setDraftModelId(firstModel?.model_id || "");
            }}
            onModelChange={setDraftModelId}
            onSave={() => void saveModelSettings()}
            onRagToggle={(enabled) => void handleToggleRag(enabled)}
            onRagConfigChange={(config) => {
              setRagConfig(config);
              setRagConfigDirty(true);
            }}
            onRagSave={() => void saveRagConfig()}
            availableTables={availableTables}
            tableLockConfig={tableLockConfig}
            tableLockSaving={tableLockSaving}
            tableLockConfigLocked={tableLockConfig.locked_table !== null && !tableLockDirty}
            onTableLockChange={(cfg) => {
              setTableLockConfig(cfg);
              setTableLockDirty(true);
            }}
            onTableLockSave={(lockedTable) => void saveTableLock(lockedTable)}
            tablePreviewData={tablePreviewData}
            tablePreviewLoading={tablePreviewLoading}
            mcpServers={mcpServers}
            onMcpServersChange={handleMcpServersChange}
            onMcpTest={handleMcpTest}
          />
        ) : null}
      </PageCanvas>
    </AppShell>
  );
}
