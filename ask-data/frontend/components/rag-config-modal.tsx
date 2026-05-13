"use client";

import { useEffect } from "react";

import type {
  RagKnowledgeBaseOption,
  RagModelOption,
  RagSessionConfig,
} from "@/lib/api";

interface RagConfigModalProps {
  open: boolean;
  saving: boolean;
  loadingOptions: boolean;
  ragAvailable: boolean;
  ragConfigLocked: boolean;
  config: RagSessionConfig;
  chatModels: RagModelOption[];
  rerankModels: RagModelOption[];
  knowledgeBases: RagKnowledgeBaseOption[];
  onClose: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  onConfigChange: (config: RagSessionConfig) => void;
  onSave: () => void;
}

export function RagConfigModal({
  open,
  saving,
  loadingOptions,
  ragAvailable,
  ragConfigLocked,
  config,
  chatModels,
  rerankModels,
  knowledgeBases,
  onClose,
  onToggleEnabled,
  onConfigChange,
  onSave,
}: RagConfigModalProps) {
  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    const previousPaddingRight = document.body.style.paddingRight;
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;

    document.body.style.overflow = "hidden";
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }

    return () => {
      document.body.style.overflow = previousOverflow;
      document.body.style.paddingRight = previousPaddingRight;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const canSave =
    !saving &&
    !loadingOptions &&
    (!config.enabled ||
      (config.project_id !== null &&
        config.knowledge_base_id !== null &&
        Boolean(config.inference_model_id)));

  return (
    <div
      className="fixed inset-0 z-[70] overflow-y-auto bg-slate-950/35 p-3 sm:p-4 lg:p-6 backdrop-blur-[2px]"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="mx-auto my-2 flex min-h-[min(92vh,48rem)] w-full max-w-4xl flex-col overflow-hidden rounded-[24px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] shadow-[0_30px_80px_rgba(15,23,42,0.28)]">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--color-border-soft)] bg-[var(--color-surface)] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--color-ink-subtle)]">
              RAG Studio
            </p>
            <h3 className="mt-1 text-xl font-semibold text-[var(--color-ink-strong)]">
              Knowledge Base Configuration
            </h3>
            <p className="mt-2 text-sm text-[var(--color-ink-muted)]">
              Enable this only when the user needs answers grounded in document knowledge rather than deposit and credit tables.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--color-border-strong)] px-3 py-1.5 text-sm font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
          >
            Close
          </button>
        </div>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain px-4 py-5 sm:px-6 sm:py-6">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
            <div>
              <p className="text-sm font-semibold text-[var(--color-ink-strong)]">
                Enable RAG Studio for this chat session
              </p>
              <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">
                Saved config is reused across all following requests in the current session.
              </p>
            </div>
            <button
              type="button"
              disabled={!ragAvailable}
              onClick={() => onToggleEnabled(!config.enabled)}
              className={`inline-flex items-center gap-3 rounded-[var(--radius-pill)] border px-3 py-2 text-sm font-semibold transition ${
                config.enabled
                  ? "border-emerald-400 bg-emerald-50 text-emerald-700"
                  : "border-[var(--color-border-strong)] bg-[var(--color-surface)] text-[var(--color-ink-muted)]"
              } ${!ragAvailable ? "cursor-not-allowed opacity-50" : ""}`}
            >
              <span>{config.enabled ? "Enabled" : "Disabled"}</span>
              <span
                className={`relative h-6 w-11 rounded-full transition ${
                  config.enabled ? "bg-emerald-500" : "bg-[#c7ccda]"
                }`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition ${
                    config.enabled ? "left-[22px]" : "left-0.5"
                  }`}
                />
              </span>
            </button>
          </div>

          {loadingOptions ? (
            <div className="rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3 text-sm text-[var(--color-ink-subtle)]">
              Loading knowledge bases and model options from RAG Studio…
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
              <span className="font-medium">Session name</span>
              <input
                value={config.session_name}
                onChange={(event) =>
                  onConfigChange({ ...config, session_name: event.target.value })
                }
                disabled={loadingOptions}
                className="rounded-[14px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none"
              />
            </label>

            <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
              <span className="font-medium">Project ID</span>
              <input
                type="number"
                value={config.project_id ?? ""}
                onChange={(event) =>
                  onConfigChange({
                    ...config,
                    project_id: event.target.value ? Number(event.target.value) : null,
                  })
                }
                disabled={loadingOptions}
                className="rounded-[14px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none"
              />
            </label>

            <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)] md:col-span-2">
              <span className="font-medium">Knowledge base</span>
              <select
                value={config.knowledge_base_id ?? ""}
                disabled={loadingOptions}
                onChange={(event) => {
                  const selected = knowledgeBases.find(
                    (item) => item.id === Number(event.target.value),
                  );
                  onConfigChange({
                    ...config,
                    knowledge_base_id: Number(event.target.value),
                    knowledge_base_name: selected?.name ?? null,
                  });
                }}
                className="rounded-[14px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none"
              >
                <option value="">Select a knowledge base</option>
                {knowledgeBases.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.id})
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
              <span className="font-medium">Chat model</span>
              <select
                value={config.inference_model_id ?? ""}
                disabled={loadingOptions}
                onChange={(event) => {
                  const selected = chatModels.find((item) => item.model_id === event.target.value);
                  onConfigChange({
                    ...config,
                    inference_model_id: event.target.value,
                    inference_model_name: selected?.name ?? null,
                  });
                }}
                className="rounded-[14px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none"
              >
                <option value="">Select a model</option>
                {chatModels.map((item) => (
                  <option key={item.model_id} value={item.model_id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
              <span className="font-medium">Reranking model</span>
              <select
                value={config.rerank_model_id ?? ""}
                disabled={loadingOptions}
                onChange={(event) => {
                  const selected = rerankModels.find((item) => item.model_id === event.target.value);
                  onConfigChange({
                    ...config,
                    rerank_model_id: event.target.value || null,
                    rerank_model_name: selected?.name ?? null,
                  });
                }}
                className="rounded-[14px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none"
              >
                <option value="">No reranking</option>
                {rerankModels.map((item) => (
                  <option key={item.model_id} value={item.model_id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)] md:col-span-2">
              <span className="font-medium">
                Maximum number of document chunks: {config.response_chunks}
              </span>
              <input
                type="range"
                min={1}
                max={20}
                step={1}
                value={config.response_chunks}
                onChange={(event) =>
                  onConfigChange({
                    ...config,
                    response_chunks: Number(event.target.value),
                  })
                }
                disabled={loadingOptions}
              />
            </label>
          </div>

          <div className="rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
            <p className="mb-3 text-sm font-semibold text-[var(--color-ink-strong)]">
              Advanced options
            </p>
            <div className="grid gap-3 md:grid-cols-2">
              {[
                ["Enable Tool Calling", "enable_tool_calling"],
                ["Enable HyDE", "enable_hyde"],
                ["Enable Summary Filtering", "enable_summary_filter"],
                ["Disable Streaming", "disable_streaming"],
              ].map(([label, key]) => (
                <label key={key} className="flex items-center justify-between gap-4 rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-[var(--color-ink-muted)]">
                  <span>{label}</span>
                  <input
                    type="checkbox"
                    checked={Boolean(config.query_configuration[key as keyof typeof config.query_configuration])}
                    disabled={loadingOptions}
                    onChange={(event) =>
                      onConfigChange({
                        ...config,
                        query_configuration: {
                          ...config.query_configuration,
                          [key]: event.target.checked,
                        },
                      })
                    }
                  />
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 shrink-0 border-t border-[var(--color-border-soft)] bg-[var(--color-surface)] px-4 py-4 sm:px-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-xs text-[var(--color-ink-subtle)]">
              {ragConfigLocked ? "Saved and active for this session." : "Changes take effect after you save."}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] px-4 py-2 text-sm font-semibold text-[var(--color-ink-muted)]"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onSave}
              disabled={!canSave}
              className="rounded-[var(--radius-pill)] bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] px-5 py-2.5 text-sm font-semibold text-white shadow-[var(--shadow-accent)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving..." : "Save configuration"}
            </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
