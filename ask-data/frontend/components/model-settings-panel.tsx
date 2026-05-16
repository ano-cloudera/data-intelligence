"use client";

import InfoIcon from "@mui/icons-material/Info";
import SaveIcon from "@mui/icons-material/Save";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import TableChartIcon from "@mui/icons-material/TableChart";

import type { LLMProviderOption, RagCollectionOption, RagOptionsResponse, TableLockConfig } from "@/lib/api";
import type { VectorRagConfig } from "@/components/rag-config-modal";

interface ModelSettingsPanelProps {
  loading: boolean;
  error: string;
  options: LLMProviderOption[];
  activeProvider: string;
  activeModelName: string;
  draftProvider: string;
  draftModelId: string;
  saving: boolean;
  lang: "en" | "id";
  ragConfig: VectorRagConfig;
  ragOptions: RagOptionsResponse | null;
  ragOptionsLoading: boolean;
  ragCollections: RagCollectionOption[];
  ragSaving: boolean;
  ragConfigLocked: boolean;
  availableTables: string[];
  tableLockConfig: TableLockConfig;
  tableLockSaving: boolean;
  tableLockConfigLocked: boolean;
  onProviderChange: (provider: string) => void;
  onModelChange: (modelId: string) => void;
  onSave: () => void;
  onRagToggle: (enabled: boolean) => void;
  onRagConfigChange: (config: VectorRagConfig) => void;
  onRagSave: () => void;
  onTableLockChange: (cfg: TableLockConfig) => void;
  onTableLockSave: () => void;
}

const TABLE_COLUMNS = [
  { key: "customer_id", type: "VARCHAR", desc_en: "Unique customer identifier", desc_id: "ID nasabah unik" },
  { key: "customer_name", type: "VARCHAR", desc_en: "Customer full name (masked in output)", desc_id: "Nama lengkap nasabah (disamarkan di output)" },
  { key: "customer_segment", type: "VARCHAR", desc_en: "Assigned customer segment label", desc_id: "Label segmen nasabah" },
  { key: "dormant_risk_level", type: "VARCHAR", desc_en: "Dormancy risk: low / medium / high", desc_id: "Risiko dormant: low / medium / high" },
  { key: "deposit_balance", type: "DECIMAL", desc_en: "Total deposit balance (IDR)", desc_id: "Total saldo deposito (IDR)" },
  { key: "city", type: "VARCHAR", desc_en: "Customer city / branch city", desc_id: "Kota nasabah / kota cabang" },
  { key: "product_type", type: "VARCHAR", desc_en: "Primary deposit product type", desc_id: "Jenis produk deposito utama" },
  { key: "last_transaction_date", type: "DATE", desc_en: "Date of last recorded transaction", desc_id: "Tanggal transaksi terakhir tercatat" },
];

const t = {
  heading: { en: "Settings", id: "Pengaturan" },
  subheading: { en: "AI Model & Knowledge Base Configuration", id: "Konfigurasi Model AI & Knowledge Base" },
  modelSection: { en: "AI Model", id: "Model AI" },
  modelActive: { en: "Active Model", id: "Model Aktif" },
  modelName: { en: "Qwen 2.5 (14B Instruct)", id: "Qwen 2.5 (14B Instruct)" },
  modelNote: { en: "Hosted on Cloudera AI Workbench via vLLM", id: "Dijalankan di Cloudera AI Workbench via vLLM" },
  disclaimerTitle: { en: "Single Model — Future Expansion Ready", id: "Satu Model — Siap untuk Ekspansi" },
  disclaimerBody: {
    en: "This deployment currently uses one AI model (Qwen 2.5) to ensure consistent, governed responses across all sessions. Future releases will support additional model providers — including Amazon Bedrock and Azure OpenAI — for cross-provider evaluation and cost optimization.",
    id: "Deployment ini saat ini menggunakan satu model AI (Qwen 2.5) untuk memastikan respons yang konsisten dan terkelola di semua sesi. Rilis mendatang akan mendukung provider model tambahan — termasuk Amazon Bedrock dan Azure OpenAI — untuk evaluasi lintas-provider dan optimasi biaya.",
  },
  saveBtn: { en: "Apply Settings", id: "Terapkan Pengaturan" },
  saving: { en: "Saving...", id: "Menyimpan..." },
  tableSection: { en: "Data Table Preview", id: "Pratinjau Tabel Data" },
  tableNote: {
    en: "All queries in this session are scoped to the table below. Column-level data governance is enforced — individual customer records are protected.",
    id: "Semua query dalam sesi ini dibatasi pada tabel di bawah. Tata kelola data tingkat kolom diterapkan — catatan nasabah individu dilindungi.",
  },
  tableName: { en: "Table", id: "Tabel" },
  colName: { en: "Column", id: "Kolom" },
  colType: { en: "Type", id: "Tipe" },
  colDesc: { en: "Description", id: "Deskripsi" },
  ragSection: { en: "Knowledge Base (RAG)", id: "Knowledge Base (RAG)" },
  ragNote: {
    en: "Enable to let the assistant reference internal policy or procedure documents when answering questions.",
    id: "Aktifkan agar asisten dapat merujuk dokumen kebijakan atau prosedur internal saat menjawab pertanyaan.",
  },
  ragEnable: { en: "Enable Knowledge Base for this session", id: "Aktifkan Knowledge Base untuk sesi ini" },
  ragEnableNote: { en: "The assistant will search document context before answering.", id: "Asisten akan mencari konteks dokumen sebelum menjawab." },
  ragActive: { en: "Active", id: "Aktif" },
  ragInactive: { en: "Inactive", id: "Nonaktif" },
  ragCollection: { en: "Document collection", id: "Koleksi dokumen" },
  ragCollectionPlaceholder: { en: "Select collection", id: "Pilih collection" },
  ragNoCollection: { en: "No collections yet. Ingest a PDF via /rag/ingest endpoint.", id: "Belum ada koleksi. Upload PDF via endpoint /rag/ingest." },
  ragTopK: { en: "Reference chunks", id: "Jumlah chunk referensi" },
  ragTopKNote: { en: "More chunks give richer context but slower responses.", id: "Lebih banyak chunk memberikan konteks lebih kaya namun respons lebih lambat." },
  ragUnavailable: { en: "RAG is not configured on the backend. Set CHROMA_ENABLED=true in backend environment.", id: "RAG belum dikonfigurasi di backend. Set CHROMA_ENABLED=true di environment backend." },
  ragLoading: { en: "Loading collections…", id: "Memuat daftar collection…" },
  ragConfigLocked: { en: "Configuration active for this session.", id: "Konfigurasi aktif untuk sesi ini." },
  ragConfigUnsaved: { en: "Changes take effect after saving.", id: "Perubahan berlaku setelah disimpan." },
  ragSave: { en: "Save Knowledge Base", id: "Simpan Knowledge Base" },
  ragSaving: { en: "Saving...", id: "Menyimpan..." },
  tableLockSection: { en: "Active Table Lock", id: "Kunci Tabel Aktif" },
  tableLockNote: { en: "Lock all queries in this session to one table.", id: "Kunci semua query sesi ini ke satu tabel." },
  tableLockSelect: { en: "Select table", id: "Pilih tabel" },
  tableLockPlaceholder: { en: "No lock (use default)", id: "Tanpa kunci (gunakan default)" },
  tableLockSave: { en: "Lock Table", id: "Kunci Tabel" },
  tableLockSaving: { en: "Saving...", id: "Menyimpan..." },
  tableLockLocked: { en: "Table locked for this session.", id: "Tabel dikunci untuk sesi ini." },
  tableLockUnsaved: { en: "Changes take effect after saving.", id: "Perubahan berlaku setelah disimpan." },
};

function tr(key: keyof typeof t, lang: "en" | "id"): string {
  return t[key][lang];
}

export function ModelSettingsPanel({
  loading,
  error,
  options,
  activeModelName,
  draftProvider,
  draftModelId,
  saving,
  lang,
  ragConfig,
  ragOptions,
  ragOptionsLoading,
  ragCollections,
  ragSaving,
  ragConfigLocked,
  availableTables,
  tableLockConfig,
  tableLockSaving,
  tableLockConfigLocked,
  onModelChange,
  onSave,
  onRagToggle,
  onRagConfigChange,
  onRagSave,
  onTableLockChange,
  onTableLockSave,
}: ModelSettingsPanelProps) {
  const qwenModels = options.filter((o) => o.provider === "local_qwen");
  const selectedModel =
    qwenModels.find((o) => o.model_id === draftModelId) ?? qwenModels[0] ?? null;

  const ragCanSave =
    !ragSaving &&
    !ragOptionsLoading &&
    (!ragConfig.enabled || Boolean(ragConfig.collection_name));

  return (
    <div className="space-y-5">
      {/* Header */}
      <section className="rounded-[24px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f6f8ff_100%)] p-6 shadow-panel">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
          {tr("heading", lang)}
        </p>
        <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.04] text-[var(--color-ink-strong)]">
          {tr("subheading", lang)}
        </h3>

        {error ? (
          <div className="mt-5 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          {/* Left: Model + RAG */}
          <div className="space-y-5">
            {/* Model section */}
            <section className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                {tr("modelSection", lang)}
              </p>

              <div className="mt-4 rounded-[18px] border border-[#5c63f2] bg-[rgba(92,99,242,0.06)] px-4 py-4">
                <div className="flex items-start gap-3">
                  <div className="icon-box mt-0.5 h-10 w-10 shrink-0 rounded-[14px]">
                    <SmartToyIcon sx={{ fontSize: 18 }} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-[var(--color-ink-strong)]">
                      {tr("modelActive", lang)}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-[var(--color-ink-subtle)]">
                      {tr("modelNote", lang)}
                    </p>
                    {qwenModels.length > 0 ? (
                      <div className="mt-3">
                        <label className="sr-only">Model</label>
                        <select
                          value={draftModelId}
                          onChange={(e) => onModelChange(e.target.value)}
                          disabled={loading || qwenModels.length <= 1}
                          className="w-full appearance-none rounded-[12px] border border-[var(--color-border-soft)] bg-white px-3 py-2.5 pr-8 text-sm font-semibold text-[var(--color-ink-strong)] outline-none transition focus:border-[#7c83ff] disabled:opacity-70"
                        >
                          {qwenModels.map((option) => (
                            <option key={option.model_id} value={option.model_id}>
                              {option.model_name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <p className="mt-2 text-sm font-semibold text-[var(--color-ink-strong)]">
                        {activeModelName || tr("modelName", lang)}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={onSave}
                  disabled={saving || loading}
                  className="inline-flex items-center gap-2 rounded-[var(--radius-button)] px-4 py-2 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60"
                  style={{ background: "linear-gradient(135deg, #FF6B00 0%, #E54E00 100%)" }}
                >
                  <SaveIcon sx={{ fontSize: 16 }} />
                  {saving ? tr("saving", lang) : tr("saveBtn", lang)}
                </button>
              </div>
            </section>

            {/* Table Lock Section */}
            <section className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                {tr("tableLockSection", lang)}
              </p>
              <p className="mt-2 text-xs leading-5 text-[var(--color-ink-muted)]">
                {tr("tableLockNote", lang)}
              </p>

              <div className="mt-4 space-y-3">
                <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                  <span className="font-medium text-[var(--color-ink-strong)]">{tr("tableLockSelect", lang)}</span>
                  <select
                    value={tableLockConfig.locked_table ?? ""}
                    onChange={(e) =>
                      onTableLockChange({ ...tableLockConfig, locked_table: e.target.value || null })
                    }
                    className="rounded-[12px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none"
                  >
                    <option value="">{tr("tableLockPlaceholder", lang)}</option>
                    {availableTables.map((tbl) => (
                      <option key={tbl} value={tbl}>
                        {tbl}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="flex items-center justify-between gap-3 pt-1">
                  <p className="text-xs text-[var(--color-ink-subtle)]">
                    {tableLockConfigLocked ? tr("tableLockLocked", lang) : tr("tableLockUnsaved", lang)}
                  </p>
                  <button
                    type="button"
                    onClick={onTableLockSave}
                    disabled={tableLockSaving}
                    className="rounded-[var(--radius-pill)] bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] px-5 py-2 text-sm font-semibold text-white shadow-[var(--shadow-accent)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {tableLockSaving ? tr("tableLockSaving", lang) : tr("tableLockSave", lang)}
                  </button>
                </div>
              </div>
            </section>

            {/* RAG Section */}
            <section className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                {tr("ragSection", lang)}
              </p>
              <p className="mt-2 text-xs leading-5 text-[var(--color-ink-muted)]">
                {tr("ragNote", lang)}
              </p>

              <div className="mt-4 space-y-4">
                {/* Enable toggle */}
                <div className="flex flex-wrap items-center justify-between gap-4 rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
                  <div>
                    <p className="text-sm font-semibold text-[var(--color-ink-strong)]">
                      {tr("ragEnable", lang)}
                    </p>
                    <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">
                      {tr("ragEnableNote", lang)}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={!ragOptions?.enabled}
                    onClick={() => onRagToggle(!ragConfig.enabled)}
                    className={`inline-flex items-center gap-3 rounded-[var(--radius-pill)] border px-3 py-2 text-sm font-semibold transition ${
                      ragConfig.enabled
                        ? "border-emerald-400 bg-emerald-50 text-emerald-700"
                        : "border-[var(--color-border-strong)] bg-[var(--color-surface)] text-[var(--color-ink-muted)]"
                    } ${!ragOptions?.enabled ? "cursor-not-allowed opacity-50" : ""}`}
                  >
                    <span>{ragConfig.enabled ? tr("ragActive", lang) : tr("ragInactive", lang)}</span>
                    <span
                      className={`relative h-6 w-11 rounded-full transition ${
                        ragConfig.enabled ? "bg-emerald-500" : "bg-[#c7ccda]"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition ${
                          ragConfig.enabled ? "left-[22px]" : "left-0.5"
                        }`}
                      />
                    </span>
                  </button>
                </div>

                {!ragOptions?.enabled && (
                  <div className="rounded-[12px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                    {tr("ragUnavailable", lang)}
                  </div>
                )}

                {ragOptionsLoading && (
                  <div className="rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3 text-sm text-[var(--color-ink-subtle)]">
                    {tr("ragLoading", lang)}
                  </div>
                )}

                {/* Collection picker */}
                <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                  <span className="font-medium text-[var(--color-ink-strong)]">{tr("ragCollection", lang)}</span>
                  <select
                    value={ragConfig.collection_name ?? ""}
                    disabled={ragOptionsLoading || !ragConfig.enabled}
                    onChange={(e) =>
                      onRagConfigChange({ ...ragConfig, collection_name: e.target.value || null })
                    }
                    className="rounded-[12px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none disabled:opacity-50"
                  >
                    <option value="">{tr("ragCollectionPlaceholder", lang)}</option>
                    {ragCollections.map((col) => (
                      <option key={col.name} value={col.name}>
                        {col.name} ({col.document_count} chunk)
                      </option>
                    ))}
                  </select>
                  {ragCollections.length === 0 && !ragOptionsLoading && ragConfig.enabled && (
                    <p className="text-xs text-[var(--color-ink-subtle)]">
                      {tr("ragNoCollection", lang)}
                    </p>
                  )}
                </label>

                {/* Top-K slider */}
                <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                  <span className="font-medium text-[var(--color-ink-strong)]">
                    {tr("ragTopK", lang)}: <span className="text-[var(--color-ink-strong)]">{ragConfig.top_k}</span>
                  </span>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    step={1}
                    value={ragConfig.top_k}
                    disabled={!ragConfig.enabled}
                    onChange={(e) =>
                      onRagConfigChange({ ...ragConfig, top_k: Number(e.target.value) })
                    }
                    className="disabled:opacity-50"
                  />
                  <p className="text-xs text-[var(--color-ink-subtle)]">
                    {tr("ragTopKNote", lang)}
                  </p>
                </label>

                {/* RAG save */}
                <div className="flex items-center justify-between gap-3 pt-1">
                  <p className="text-xs text-[var(--color-ink-subtle)]">
                    {ragConfigLocked ? tr("ragConfigLocked", lang) : tr("ragConfigUnsaved", lang)}
                  </p>
                  <button
                    type="button"
                    onClick={onRagSave}
                    disabled={!ragCanSave}
                    className="rounded-[var(--radius-pill)] bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] px-5 py-2 text-sm font-semibold text-white shadow-[var(--shadow-accent)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {ragSaving ? tr("ragSaving", lang) : tr("ragSave", lang)}
                  </button>
                </div>
              </div>
            </section>
          </div>

          {/* Right: Disclaimer + Data Table Preview */}
          <div className="space-y-5">
            {/* Disclaimer */}
            <div className="rounded-[20px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#fbfcff_0%,#eef4ff_100%)] p-5 shadow-panel">
              <div className="flex items-start gap-3">
                <div className="icon-box h-11 w-11 shrink-0 rounded-[14px]">
                  <InfoIcon sx={{ fontSize: 20 }} />
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4968cf]">
                    {tr("disclaimerTitle", lang)}
                  </p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-ink-muted)]">
                    {tr("disclaimerBody", lang)}
                  </p>
                </div>
              </div>
            </div>

            {/* Data Table Preview */}
            <div className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5 shadow-panel">
              <div className="flex items-center gap-2 mb-3">
                <div className="icon-box h-8 w-8 shrink-0 rounded-[12px]">
                  <TableChartIcon sx={{ fontSize: 16 }} />
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
                    {tr("tableSection", lang)}
                  </p>
                  <p className="mt-0.5 text-[10px] font-mono text-[#4968cf]">
                    cai_sdx_se_indonesia.customer_dormant_segment
                  </p>
                </div>
              </div>
              <p className="mb-3 text-xs leading-5 text-[var(--color-ink-muted)]">
                {tr("tableNote", lang)}
              </p>
              <div className="overflow-x-auto rounded-[12px] border border-[var(--color-border-soft)]">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[var(--color-border-soft)] bg-[var(--color-surface-muted)]">
                      <th className="px-3 py-2 text-left font-semibold text-[var(--color-ink-subtle)]">{tr("colName", lang)}</th>
                      <th className="px-3 py-2 text-left font-semibold text-[var(--color-ink-subtle)]">{tr("colType", lang)}</th>
                      <th className="px-3 py-2 text-left font-semibold text-[var(--color-ink-subtle)]">{tr("colDesc", lang)}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {TABLE_COLUMNS.map((col, idx) => (
                      <tr
                        key={col.key}
                        className={idx < TABLE_COLUMNS.length - 1 ? "border-b border-[var(--color-border-soft)]" : ""}
                      >
                        <td className="px-3 py-2 font-mono text-[#4953d3]">{col.key}</td>
                        <td className="px-3 py-2 text-[var(--color-ink-subtle)]">{col.type}</td>
                        <td className="px-3 py-2 text-[var(--color-ink-muted)]">
                          {lang === "id" ? col.desc_id : col.desc_en}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
