"use client";

import { useEffect, useMemo, useState } from "react";
import GroupIcon from "@mui/icons-material/Group";
import ChatIcon from "@mui/icons-material/Chat";
import StorageIcon from "@mui/icons-material/Storage";
import SecurityIcon from "@mui/icons-material/Security";
import BarChartIcon from "@mui/icons-material/BarChart";
import InfoIcon from "@mui/icons-material/Info";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AnalyticsEventRecord, AnalyticsSummaryResponse } from "@/lib/api";

interface UsageDashboardPanelProps {
  loading: boolean;
  error: string;
  summary: AnalyticsSummaryResponse | null;
  events: AnalyticsEventRecord[];
  onRefresh: () => void;
}

const ACTIVITY_PAGE_SIZE = 5;

function formatCompact(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: value >= 1000 ? 1 : 0,
  }).format(value);
}

/** Recharts Tooltip values may be string | number; normalize for display */
function formatTooltipNumber(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) return formatCompact(value);
  if (typeof value === "string") {
    const n = Number(value);
    if (Number.isFinite(n)) return formatCompact(n);
  }
  return "";
}

function formatDate(value?: string | null): string {
  if (!value) return "No activity yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No activity yet";
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

const PIE_COLORS = ["#5c63f2", "#38bdf8", "#a78bfa"];

export function UsageDashboardPanel({
  loading,
  error,
  summary,
  events,
  onRefresh,
}: UsageDashboardPanelProps) {
  const [activityPage, setActivityPage] = useState(1);

  const coreMetrics = [
    {
      label: "Active sessions",
      value: summary ? formatCompact(summary.total_sessions) : "—",
      icon: <GroupIcon sx={{ fontSize: 20 }} />,
    },
    {
      label: "Questions",
      value: summary ? formatCompact(summary.total_questions) : "—",
      icon: <ChatIcon sx={{ fontSize: 20 }} />,
    },
    {
      label: "SQL requests",
      value: summary ? formatCompact(summary.sql_requests) : "—",
      icon: <StorageIcon sx={{ fontSize: 20 }} />,
    },
    {
      label: "Guardrails blocks",
      value: summary ? formatCompact(summary.guardrails_blocks) : "—",
      icon: <SecurityIcon sx={{ fontSize: 20 }} />,
    },
    {
      label: "Visual responses",
      value: summary ? formatCompact(summary.visualization_responses) : "—",
      icon: <BarChartIcon sx={{ fontSize: 20 }} />,
    },
  ];

  const promptTokens = summary?.estimated_prompt_tokens ?? 0;
  const completionTokens = summary?.estimated_completion_tokens ?? 0;
  const totalTokens = summary?.estimated_total_tokens ?? promptTokens + completionTokens;

  const pieSlices = useMemo(
    () =>
      [
        { name: "Prompt (est.)", value: Math.max(0, promptTokens) },
        { name: "Completion (est.)", value: Math.max(0, completionTokens) },
      ].filter((row) => row.value > 0),
    [promptTokens, completionTokens],
  );

  const trendData = useMemo(() => {
    const ordered = [...events].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );
    return ordered.map((e, i) => ({
      seq: i + 1,
      tokens: Math.max(0, e.estimated_total_tokens),
    }));
  }, [events]);

  const activityPageCount = Math.max(1, Math.ceil(events.length / ACTIVITY_PAGE_SIZE));
  const pagedEvents = useMemo(() => {
    const start = (activityPage - 1) * ACTIVITY_PAGE_SIZE;
    return events.slice(start, start + ACTIVITY_PAGE_SIZE);
  }, [activityPage, events]);

  useEffect(() => {
    setActivityPage((current) => Math.min(current, activityPageCount));
  }, [activityPageCount]);

  const promptPct =
    totalTokens > 0 ? Math.round((promptTokens / totalTokens) * 100) : 0;
  const completionPct =
    totalTokens > 0 ? Math.round((completionTokens / totalTokens) * 100) : 0;

  return (
    <div className="space-y-5">
      <section className="rounded-[24px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f5f8ff_100%)] p-6 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
              Usage Dashboard
            </p>
            <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.04] text-[var(--color-ink-strong)]">
              Adoption And Activity Overview
            </h3>
            <p className="mt-3 text-sm leading-7 text-[var(--color-ink-muted)]">
              This section summarizes recent session activity, model routing, guardrails interventions, and estimated token consumption without depending on AI-generated explanation.
            </p>
          </div>
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex items-center gap-2 rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
          >
            <RefreshIcon sx={{ fontSize: 16 }} />
            Refresh Dashboard
          </button>
        </div>

        {error ? (
          <div className="mt-5 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {coreMetrics.map((metric) => (
            <section
              key={metric.label}
              className="rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-5 py-4 transition hover:border-[var(--color-border-strong)] hover:shadow-[0_8px_24px_rgba(255,107,0,0.1)]"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--color-ink-subtle)]">
                    {metric.label}
                  </p>
                  <p className="mt-3 font-headline text-[30px] font-bold text-[var(--color-ink-strong)]">
                    {loading ? "…" : metric.value}
                  </p>
                </div>
                <div className="icon-box h-11 w-11 rounded-[14px]">
                  {metric.icon}
                </div>
              </div>
            </section>
          ))}
        </div>

        <section className="mt-6 rounded-[22px] border border-[var(--color-border-soft)] bg-white p-6 shadow-panel">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--color-border-soft)] pb-5">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
                Estimated token usage
              </p>
              <p className="mt-2 max-w-xl text-sm leading-7 text-[var(--color-ink-muted)]">
                Totals combine prompt and completion estimates so Azure OpenAI and Bedrock stay comparable. Figures scale from recent activity in the selected window.
              </p>
            </div>
            <div className="text-right">
              <p className="font-headline text-[42px] font-bold leading-none tracking-tight text-[var(--color-ink-strong)]">
                {loading ? "…" : formatCompact(totalTokens)}
              </p>
              <p className="mt-2 text-xs font-medium uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                Estimated tokens (combined)
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,260px)] lg:items-center">
            <div className="space-y-5">
              <div>
                <div className="flex items-center justify-between text-xs font-semibold text-[var(--color-ink-muted)]">
                  <span>Composition</span>
                  <span>
                    {totalTokens > 0 ? `${promptPct}% / ${completionPct}%` : "—"}
                  </span>
                </div>
                <div className="mt-3 flex h-4 overflow-hidden rounded-full bg-[var(--color-surface-muted)]">
                  {totalTokens > 0 ? (
                    <>
                      <div
                        className="h-full bg-[#5c63f2] transition-all"
                        style={{ width: `${promptPct}%` }}
                        title={`Prompt ${promptPct}%`}
                      />
                      <div
                        className="h-full bg-[#38bdf8] transition-all"
                        style={{ width: `${completionPct}%` }}
                        title={`Completion ${completionPct}%`}
                      />
                    </>
                  ) : (
                    <div className="h-full w-full bg-[var(--color-border-soft)]" />
                  )}
                </div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="rounded-[14px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#fafbff_0%,#f0f4ff_100%)] px-4 py-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-ink-subtle)]">
                      Prompt (est.)
                    </p>
                    <p className="mt-1 font-headline text-xl font-bold text-[#434ce8]">
                      {loading ? "…" : formatCompact(promptTokens)}
                    </p>
                  </div>
                  <div className="rounded-[14px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#f8fcff_0%,#e8f6ff_100%)] px-4 py-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-ink-subtle)]">
                      Completion (est.)
                    </p>
                    <p className="mt-1 font-headline text-xl font-bold text-[#0284c7]">
                      {loading ? "…" : formatCompact(completionTokens)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex min-h-[220px] flex-col items-center justify-center rounded-[20px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)]/50 px-2 py-4">
              {pieSlices.length > 0 && !loading ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieSlices}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={54}
                      outerRadius={84}
                      paddingAngle={2}
                    >
                      {pieSlices.map((entry, index) => (
                        <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatTooltipNumber(value)} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="px-4 text-center text-sm text-[var(--color-ink-muted)]">
                  {loading ? "Loading token breakdown…" : "No token estimates recorded yet in this window."}
                </p>
              )}
            </div>
          </div>

          <div className="mt-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
              Recent activity trend (tokens per event)
            </p>
            <div className="mt-3 h-[200px] w-full rounded-[18px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] px-2 py-3">
              {trendData.length > 1 && !loading ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trendData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="tokenAreaFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#5c63f2" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="#5c63f2" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis
                      dataKey="seq"
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickLine={false}
                      axisLine={false}
                      label={{ value: "Event sequence", position: "insideBottom", offset: -2, fontSize: 10, fill: "#94a3b8" }}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickLine={false}
                      axisLine={false}
                      width={40}
                    />
                    <Tooltip
                      formatter={(value) => {
                        const text = formatTooltipNumber(value);
                        return text ? [`${text} est. tokens`, "Volume"] : ["", ""];
                      }}
                      labelFormatter={(label) => `Event ${label}`}
                    />
                    <Area
                      type="linear"
                      dataKey="tokens"
                      stroke="#5c63f2"
                      strokeWidth={2}
                      fill="url(#tokenAreaFill)"
                      dot={{ r: 2.5, fill: "#5c63f2" }}
                      activeDot={{ r: 5 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center px-4 text-center text-sm text-[var(--color-ink-muted)]">
                  {loading
                    ? "Loading trend…"
                    : trendData.length === 0
                      ? "Activity will appear here as requests are logged."
                      : "At least two events are needed to show a trend line."}
                </div>
              )}
            </div>
          </div>
        </section>
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[22px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-5 shadow-panel">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                Recent Activity
              </p>
              <p className="mt-2 text-sm text-[var(--color-ink-muted)]">
                Latest event: {summary ? formatDate(summary.latest_event_at) : "No activity yet"}
              </p>
            </div>
            {loading ? (
              <span className="text-xs font-semibold text-[var(--color-ink-subtle)]">Loading…</span>
            ) : null}
          </div>

          <div className="mt-4 overflow-hidden rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)]">
            <div className="grid grid-cols-[1.25fr_0.95fr_1fr_0.8fr] gap-3 border-b border-[var(--color-border-soft)] px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-ink-subtle)]">
              <span>Question</span>
              <span>Mode</span>
              <span>Model</span>
              <span>Time</span>
            </div>
            <div className="divide-y divide-[var(--color-border-soft)]">
              {events.length === 0 && !loading ? (
                <div className="px-4 py-5 text-sm text-[var(--color-ink-muted)]">
                  No events recorded yet.
                </div>
              ) : null}
              {pagedEvents.map((event) => (
                <div
                  key={event.event_id}
                  className="grid grid-cols-[1.25fr_0.95fr_1fr_0.8fr] gap-3 px-4 py-3 text-sm text-[var(--color-ink-muted)]"
                >
                  <div>
                    <p className="font-medium text-[var(--color-ink-strong)]">
                      {event.question_excerpt || event.event_type}
                    </p>
                    <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">
                      {event.visualization_type
                        ? `Visual ${event.visualization_type}`
                        : event.guardrails_action
                          ? `Guardrails ${event.guardrails_action}`
                          : event.endpoint}
                    </p>
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink-subtle)]">
                    {event.mode || "n/a"}
                  </span>
                  <span className="text-xs font-semibold text-[var(--color-ink-subtle)]">
                    {event.model_name || event.provider || "Default"}
                  </span>
                  <span className="text-xs text-[var(--color-ink-subtle)]">
                    {formatDate(event.created_at)}
                  </span>
                </div>
              ))}
            </div>
          </div>
          {events.length > 0 ? (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-[var(--color-ink-subtle)]">
                Showing {(activityPage - 1) * ACTIVITY_PAGE_SIZE + 1}
                {"–"}
                {Math.min(activityPage * ACTIVITY_PAGE_SIZE, events.length)} of {events.length} events
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActivityPage((page) => Math.max(1, page - 1))}
                  disabled={activityPage === 1}
                  className="rounded-full border border-[var(--color-border-soft)] bg-white px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                  Page {activityPage} of {activityPageCount}
                </span>
                <button
                  type="button"
                  onClick={() => setActivityPage((page) => Math.min(activityPageCount, page + 1))}
                  disabled={activityPage === activityPageCount}
                  className="rounded-full border border-[var(--color-border-soft)] bg-white px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </section>

        <section className="space-y-5">
          <div className="rounded-[22px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f7fbff_100%)] p-5 shadow-panel">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
              Provider Usage
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {summary?.provider_breakdown.length ? (
                summary.provider_breakdown.map((item) => (
                  <span
                    key={item.provider}
                    className="rounded-full border border-[var(--color-border-soft)] bg-white px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)]"
                  >
                    {item.provider} · {formatCompact(item.count)}
                  </span>
                ))
              ) : (
                <span className="text-sm text-[var(--color-ink-muted)]">
                  No provider activity yet.
                </span>
              )}
            </div>
          </div>

          <div className="rounded-[22px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-5 shadow-panel">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
              Mode Breakdown
            </p>
            <div className="mt-4 space-y-3">
              {summary?.mode_breakdown.length ? (
                summary.mode_breakdown.map((item) => (
                  <div
                    key={item.mode}
                    className="flex items-center justify-between rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3 text-sm"
                  >
                    <span className="font-medium text-[var(--color-ink-muted)]">{item.mode}</span>
                    <span className="font-semibold text-[var(--color-ink-strong)]">
                      {formatCompact(item.count)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-[var(--color-ink-muted)]">
                  No mode breakdown available yet.
                </p>
              )}
            </div>
          </div>

          <div className="rounded-[22px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#fbfcff_0%,#eef4ff_100%)] p-5 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="icon-box h-11 w-11 rounded-[14px]">
                <InfoIcon sx={{ fontSize: 20 }} />
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
                  Reading Notes
                </p>
                <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
                  Use this panel as an operational summary, not as a billing-grade ledger.
                </p>
              </div>
            </div>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-[var(--color-ink-muted)]">
              <li>Estimated tokens are derived from message length so Azure OpenAI and Bedrock remain comparable in one dashboard.</li>
              <li>Provider usage reflects non-RAG routing. RAG Studio stays tracked as its own mode.</li>
              <li>Guardrails blocks count requests intentionally stopped before sensitive data was returned.</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
