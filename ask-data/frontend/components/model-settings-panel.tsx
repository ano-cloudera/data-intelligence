"use client";

import CloudIcon from "@mui/icons-material/Cloud";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import InfoIcon from "@mui/icons-material/Info";
import SaveIcon from "@mui/icons-material/Save";

import type { LLMProviderOption } from "@/lib/api";

interface ModelSettingsPanelProps {
  loading: boolean;
  error: string;
  options: LLMProviderOption[];
  activeProvider: string;
  activeModelName: string;
  draftProvider: string;
  draftModelId: string;
  saving: boolean;
  onProviderChange: (provider: string) => void;
  onModelChange: (modelId: string) => void;
  onSave: () => void;
}

function providerLabel(provider: string): string {
  if (provider === "local_qwen") return "Qwen (Ollama)";
  if (provider === "bedrock") return "Amazon Bedrock";
  return "Azure OpenAI";
}

function providerDescription(provider: string): string {
  if (provider === "local_qwen")
    return "Model Qwen2.5 lokal via Ollama. Digunakan untuk demo Bank Jawa Timur tanpa ketergantungan cloud.";
  if (provider === "bedrock")
    return "Use Amazon Bedrock for alternative model families and cross-provider evaluation.";
  return "Use Azure OpenAI for the configured production-aligned deployment path.";
}

function providerIcon(provider: string) {
  if (provider === "bedrock") return <CloudIcon sx={{ fontSize: 18 }} />;
  return <SmartToyIcon sx={{ fontSize: 18 }} />;
}

export function ModelSettingsPanel({
  loading,
  error,
  options,
  activeProvider,
  activeModelName,
  draftProvider,
  draftModelId,
  saving,
  onProviderChange,
  onModelChange,
  onSave,
}: ModelSettingsPanelProps) {
  const providerOptions = Array.from(new Set(options.map((option) => option.provider)));
  const modelsForProvider = options.filter((option) => option.provider === draftProvider);
  const selectedDraftModel =
    modelsForProvider.find((option) => option.model_id === draftModelId) ?? modelsForProvider[0] ?? null;

  return (
    <div className="space-y-5">
      <section className="rounded-[24px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f6f8ff_100%)] p-6 shadow-panel">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
          Model Settings
        </p>
        <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.04] text-[var(--color-ink-strong)]">
          Select The Active AI Connection
        </h3>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--color-ink-muted)]">
          Choose the connection first, then pick the available model for that provider. The selected configuration is saved in this browser and applied to the app session.
        </p>

        {error ? (
          <div className="mt-5 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
              Connection
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {providerOptions.map((provider) => {
                const selected = provider === draftProvider;
                return (
                  <button
                    key={provider}
                    type="button"
                    onClick={() => onProviderChange(provider)}
                    className={`rounded-[18px] border px-4 py-4 text-left transition ${
                      selected
                        ? "border-[#5c63f2] bg-[rgba(92,99,242,0.08)] shadow-[0_10px_24px_rgba(92,99,242,0.08)]"
                        : "border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] hover:border-[#7c83ff] hover:bg-[rgba(92,99,242,0.04)]"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="icon-box mt-0.5 h-10 w-10 shrink-0 rounded-[14px]">
                        {providerIcon(provider)}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-[var(--color-ink-strong)]">
                          {providerLabel(provider)}
                        </p>
                        <p className="mt-2 text-xs leading-5 text-[var(--color-ink-subtle)]">
                          {providerDescription(provider)}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                Model
              </p>
              <div className="mt-3 rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-xs font-semibold text-[var(--color-ink-strong)]">
                      {selectedDraftModel?.model_name || "No model available"}
                    </p>
                    <p className="mt-1 text-[11px] text-[var(--color-ink-subtle)]">
                      {modelsForProvider.length > 0
                        ? `${modelsForProvider.length} model${modelsForProvider.length === 1 ? "" : "s"} available for ${providerLabel(draftProvider)}`
                        : "No model options are currently available for this provider."}
                    </p>
                  </div>
                  {modelsForProvider.length > 0 ? (
                    <span className="rounded-full border border-[var(--color-border-soft)] bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                      Active catalog
                    </span>
                  ) : null}
                </div>
                <label className="relative block">
                  <span className="sr-only">Model</span>
                  <select
                    value={draftModelId}
                    onChange={(event) => onModelChange(event.target.value)}
                    disabled={loading || modelsForProvider.length === 0}
                    className="w-full appearance-none rounded-[14px] border border-white/60 bg-white px-4 py-3 pr-11 text-sm font-semibold text-[var(--color-ink-strong)] outline-none transition focus:border-[#7c83ff] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {modelsForProvider.map((option) => (
                      <option key={`${option.provider}-${option.model_id}`} value={option.model_id}>
                        {option.model_name}
                      </option>
                    ))}
                  </select>
                  <span className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-[var(--color-ink-subtle)]">
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden>
                      <path d="m5.5 7.75 4.5 4.5 4.5-4.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                </label>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3">
              <div className="text-xs text-[var(--color-ink-subtle)]">
                {loading ? "Loading configured providers…" : "The saved choice is applied to the active chat session."}
              </div>
              <button
                type="button"
                onClick={onSave}
                disabled={saving || loading || !draftProvider}
                className="inline-flex items-center gap-2 rounded-[var(--radius-button)] px-4 py-2 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60"
                style={{ background: "linear-gradient(135deg, #FF6B00 0%, #E54E00 100%)" }}
              >
                <SaveIcon sx={{ fontSize: 16 }} />
                {saving ? "Saving..." : "Save Model Settings"}
              </button>
            </div>
          </section>

          <section className="space-y-4">
            <div className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5 shadow-panel">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                Active Runtime
              </p>
              <div className="mt-4 space-y-3">
                <div className="rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="icon-box h-10 w-10 shrink-0 rounded-[14px]">
                      {providerIcon(activeProvider)}
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                        Provider
                      </p>
                      <p className="mt-1 text-sm font-semibold text-[var(--color-ink-strong)]">
                        {providerLabel(activeProvider)}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="icon-box h-10 w-10 rounded-[14px]">
                      <SmartToyIcon sx={{ fontSize: 18 }} />
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                        Model
                      </p>
                      <p className="mt-1 text-sm font-semibold text-[var(--color-ink-strong)]">
                        {activeModelName || "Default configured model"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-[20px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#fbfcff_0%,#eef4ff_100%)] p-5 shadow-panel">
              <div className="flex items-start gap-3">
                <div className="icon-box h-11 w-11 shrink-0 rounded-[14px]">
                  <InfoIcon sx={{ fontSize: 20 }} />
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
                    Selection Guidance
                  </p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-ink-muted)]">
                    Both providers follow the same governed chat and SQL path. What changes here is the model family used for generation.
                  </p>
                </div>
              </div>
              <ul className="mt-4 space-y-3 text-sm leading-7 text-[var(--color-ink-muted)]">
                <li>Azure OpenAI and Amazon Bedrock both use the same guardrails, session memory, and analytics workflow.</li>
                <li>When Bedrock discovery is enabled on the backend, this list reflects the models available to the active AWS account and region.</li>
                <li>Your saved choice stays in this browser and is applied to the active chat session until you change it again.</li>
              </ul>
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}
