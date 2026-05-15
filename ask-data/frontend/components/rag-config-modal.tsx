"use client";

import { useEffect } from "react";

export interface RagCollectionOption {
  name: string;
  document_count: number;
}

export interface VectorRagConfig {
  enabled: boolean;
  collection_name: string | null;
  top_k: number;
}

interface RagConfigModalProps {
  open: boolean;
  saving: boolean;
  loadingOptions: boolean;
  ragAvailable: boolean;
  ragConfigLocked: boolean;
  config: VectorRagConfig;
  collections: RagCollectionOption[];
  onClose: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  onConfigChange: (config: VectorRagConfig) => void;
  onSave: () => void;
}

export function RagConfigModal({
  open,
  saving,
  loadingOptions,
  ragAvailable,
  ragConfigLocked,
  config,
  collections,
  onClose,
  onToggleEnabled,
  onConfigChange,
  onSave,
}: RagConfigModalProps) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    const prevPad = document.body.style.paddingRight;
    const sbw = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = "hidden";
    if (sbw > 0) document.body.style.paddingRight = `${sbw}px`;
    return () => {
      document.body.style.overflow = prev;
      document.body.style.paddingRight = prevPad;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) return null;

  const canSave =
    !saving &&
    !loadingOptions &&
    (!config.enabled || Boolean(config.collection_name));

  return (
    <div
      className="fixed inset-0 z-[70] overflow-y-auto bg-slate-950/35 p-3 sm:p-4 lg:p-6 backdrop-blur-[2px]"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="mx-auto my-2 flex min-h-[min(92vh,32rem)] w-full max-w-2xl flex-col overflow-hidden rounded-[24px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] shadow-[0_30px_80px_rgba(15,23,42,0.28)]">

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--color-border-soft)] bg-[var(--color-surface)] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--color-ink-subtle)]">
              Dokumen Referensi
            </p>
            <h3 className="mt-1 text-xl font-semibold text-[var(--color-ink-strong)]">
              Konfigurasi Knowledge Base
            </h3>
            <p className="mt-2 text-sm text-[var(--color-ink-muted)]">
              Aktifkan RAG agar jawaban asisten dapat merujuk dokumen kebijakan atau prosedur Bank Jatim.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--color-border-strong)] px-3 py-1.5 text-sm font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
          >
            Tutup
          </button>
        </div>

        {/* Body */}
        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain px-4 py-5 sm:px-6 sm:py-6">

          {/* Enable toggle */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-[18px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
            <div>
              <p className="text-sm font-semibold text-[var(--color-ink-strong)]">
                Aktifkan RAG untuk sesi ini
              </p>
              <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">
                Asisten akan mencari konteks dari dokumen sebelum menjawab.
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
              <span>{config.enabled ? "Aktif" : "Nonaktif"}</span>
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

          {!ragAvailable && (
            <div className="rounded-[14px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              RAG belum dikonfigurasi di backend. Set <code className="font-mono">CHROMA_ENABLED=true</code> di environment backend.
            </div>
          )}

          {loadingOptions && (
            <div className="rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3 text-sm text-[var(--color-ink-subtle)]">
              Memuat daftar collection…
            </div>
          )}

          {/* Collection picker */}
          <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
            <span className="font-medium text-[var(--color-ink-strong)]">Collection dokumen</span>
            <select
              value={config.collection_name ?? ""}
              disabled={loadingOptions || !config.enabled}
              onChange={(e) =>
                onConfigChange({ ...config, collection_name: e.target.value || null })
              }
              className="rounded-[14px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none disabled:opacity-50"
            >
              <option value="">Pilih collection</option>
              {collections.map((col) => (
                <option key={col.name} value={col.name}>
                  {col.name} ({col.document_count} chunk)
                </option>
              ))}
            </select>
            {collections.length === 0 && !loadingOptions && config.enabled && (
              <p className="text-xs text-[var(--color-ink-subtle)]">
                Belum ada collection. Upload PDF terlebih dahulu via endpoint <code className="font-mono">/rag/ingest</code>.
              </p>
            )}
          </label>

          {/* Top-K slider */}
          <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
            <span className="font-medium text-[var(--color-ink-strong)]">
              Jumlah chunk referensi: <span className="text-[var(--color-ink-strong)]">{config.top_k}</span>
            </span>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={config.top_k}
              disabled={!config.enabled}
              onChange={(e) =>
                onConfigChange({ ...config, top_k: Number(e.target.value) })
              }
              className="disabled:opacity-50"
            />
            <p className="text-xs text-[var(--color-ink-subtle)]">
              Semakin banyak chunk, konteks lebih kaya namun respons lebih lambat.
            </p>
          </label>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 shrink-0 border-t border-[var(--color-border-soft)] bg-[var(--color-surface)] px-4 py-4 sm:px-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-xs text-[var(--color-ink-subtle)]">
              {ragConfigLocked
                ? "Konfigurasi aktif untuk sesi ini."
                : "Perubahan berlaku setelah disimpan."}
            </div>
            <div className="flex gap-3 sm:justify-end">
              <button
                type="button"
                onClick={onClose}
                className="rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] px-4 py-2 text-sm font-semibold text-[var(--color-ink-muted)]"
              >
                Batal
              </button>
              <button
                type="button"
                onClick={onSave}
                disabled={!canSave}
                className="rounded-[var(--radius-pill)] bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] px-5 py-2.5 text-sm font-semibold text-white shadow-[var(--shadow-accent)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {saving ? "Menyimpan..." : "Simpan konfigurasi"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
