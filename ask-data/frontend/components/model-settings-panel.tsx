"use client";

import { useState } from "react";
import InfoIcon from "@mui/icons-material/Info";
import SaveIcon from "@mui/icons-material/Save";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import TableChartIcon from "@mui/icons-material/TableChart";

import type { LLMProviderOption, RagCollectionOption, RagOptionsResponse, TableLockConfig, TablePreviewResponse } from "@/lib/api";
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
  tablePreviewData: TablePreviewResponse | null;
  tablePreviewLoading: boolean;
  onProviderChange: (provider: string) => void;
  onModelChange: (modelId: string) => void;
  onSave: () => void;
  onRagToggle: (enabled: boolean) => void;
  onRagConfigChange: (config: VectorRagConfig) => void;
  onRagSave: () => void;
  onTableLockChange: (cfg: TableLockConfig) => void;
  onTableLockSave: () => void;
}

const TABLE_SCHEMA_SECTIONS = [
  {
    section: { en: "Identity", id: "Identitas" },
    columns: [
      { key: "customer_id", type: "VARCHAR", desc_en: "Unique customer identifier", desc_id: "ID nasabah unik" },
      { key: "customer_name", type: "VARCHAR", desc_en: "Customer full name (masked in output)", desc_id: "Nama lengkap nasabah (disamarkan)" },
      { key: "customer_code", type: "VARCHAR", desc_en: "Internal customer code", desc_id: "Kode nasabah internal" },
      { key: "account_number", type: "VARCHAR", desc_en: "Primary account number", desc_id: "Nomor rekening utama" },
      { key: "customer_since", type: "DATE", desc_en: "Date of first account opening", desc_id: "Tanggal pembukaan rekening pertama" },
      { key: "customer_tenure_years", type: "INT", desc_en: "Years as active customer", desc_id: "Lama menjadi nasabah (tahun)" },
    ],
  },
  {
    section: { en: "Demographics", id: "Demografi" },
    columns: [
      { key: "age_band", type: "VARCHAR", desc_en: "Age band bracket (e.g. 25–34)", desc_id: "Kelompok usia (misal 25–34)" },
      { key: "gender", type: "VARCHAR", desc_en: "Customer gender", desc_id: "Jenis kelamin nasabah" },
      { key: "city", type: "VARCHAR", desc_en: "Customer home city", desc_id: "Kota asal nasabah" },
      { key: "district", type: "VARCHAR", desc_en: "District / kecamatan", desc_id: "Kecamatan nasabah" },
      { key: "branch_name", type: "VARCHAR", desc_en: "Servicing branch name", desc_id: "Nama cabang pelayanan" },
      { key: "occupation", type: "VARCHAR", desc_en: "Customer occupation category", desc_id: "Kategori pekerjaan nasabah" },
      { key: "income_band", type: "VARCHAR", desc_en: "Monthly income band", desc_id: "Kelompok pendapatan bulanan" },
    ],
  },
  {
    section: { en: "Product Holding", id: "Kepemilikan Produk" },
    columns: [
      { key: "has_savings", type: "BOOLEAN", desc_en: "Holds a savings account", desc_id: "Memiliki rekening tabungan" },
      { key: "has_current_account", type: "BOOLEAN", desc_en: "Holds a current account", desc_id: "Memiliki rekening giro" },
      { key: "has_deposit", type: "BOOLEAN", desc_en: "Holds a time deposit", desc_id: "Memiliki deposito berjangka" },
      { key: "has_loan", type: "BOOLEAN", desc_en: "Has an active loan", desc_id: "Memiliki pinjaman aktif" },
      { key: "has_mobile_banking", type: "BOOLEAN", desc_en: "Registered for mobile banking", desc_id: "Terdaftar mobile banking" },
      { key: "has_internet_banking", type: "BOOLEAN", desc_en: "Registered for internet banking", desc_id: "Terdaftar internet banking" },
    ],
  },
  {
    section: { en: "Balance", id: "Saldo" },
    columns: [
      { key: "avg_savings_balance", type: "DECIMAL", desc_en: "3-month average savings balance (IDR)", desc_id: "Rata-rata saldo tabungan 3 bulan (IDR)" },
      { key: "avg_deposit_balance", type: "DECIMAL", desc_en: "Average time deposit balance (IDR)", desc_id: "Rata-rata saldo deposito (IDR)" },
      { key: "total_deposit_balance", type: "DECIMAL", desc_en: "Total deposit balance across all tenors", desc_id: "Total saldo deposito semua tenor" },
      { key: "outstanding_loan_balance", type: "DECIMAL", desc_en: "Outstanding loan principal (IDR)", desc_id: "Saldo pokok pinjaman (IDR)" },
    ],
  },
  {
    section: { en: "Behavioral", id: "Perilaku" },
    columns: [
      { key: "last_transaction_date", type: "DATE", desc_en: "Date of last recorded transaction", desc_id: "Tanggal transaksi terakhir tercatat" },
      { key: "days_since_last_txn", type: "INT", desc_en: "Days elapsed since last transaction", desc_id: "Hari sejak transaksi terakhir" },
      { key: "txn_frequency_30d", type: "INT", desc_en: "Transaction count in last 30 days", desc_id: "Jumlah transaksi 30 hari terakhir" },
      { key: "active_months_12m", type: "INT", desc_en: "Months with at least 1 transaction in last year", desc_id: "Bulan aktif bertransaksi dalam setahun" },
      { key: "digital_login_count_30d", type: "INT", desc_en: "Digital channel logins in last 30 days", desc_id: "Login digital 30 hari terakhir" },
    ],
  },
  {
    section: { en: "Dormant Risk", id: "Risiko Dormant" },
    columns: [
      { key: "dormant_flag", type: "BOOLEAN", desc_en: "True if account is currently dormant", desc_id: "True jika rekening saat ini dormant" },
      { key: "dormant_risk_level", type: "VARCHAR", desc_en: "Risk level: low / medium / high", desc_id: "Level risiko: low / medium / high" },
      { key: "dormant_probability", type: "DECIMAL", desc_en: "Model-predicted dormancy probability (0–1)", desc_id: "Probabilitas dormant dari model (0–1)" },
      { key: "dormant_reason", type: "VARCHAR", desc_en: "Primary reason code for dormancy classification", desc_id: "Kode alasan utama klasifikasi dormant" },
    ],
  },
  {
    section: { en: "Segmentation", id: "Segmentasi" },
    columns: [
      { key: "customer_segment", type: "VARCHAR", desc_en: "Assigned customer segment label", desc_id: "Label segmen nasabah" },
      { key: "segment_score", type: "DECIMAL", desc_en: "Numeric score driving the segment assignment", desc_id: "Skor numerik untuk penentuan segmen" },
      { key: "segment_description", type: "VARCHAR", desc_en: "Human-readable segment description", desc_id: "Deskripsi segmen yang dapat dibaca" },
    ],
  },
  {
    section: { en: "Campaign", id: "Kampanye" },
    columns: [
      { key: "recommended_campaign", type: "VARCHAR", desc_en: "Next-best campaign recommendation", desc_id: "Rekomendasi kampanye terbaik berikutnya" },
      { key: "recommended_channel", type: "VARCHAR", desc_en: "Preferred contact channel for campaign", desc_id: "Channel kontak yang direkomendasikan" },
      { key: "next_best_action", type: "VARCHAR", desc_en: "Specific action for relationship manager", desc_id: "Tindakan spesifik untuk relationship manager" },
    ],
  },
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
  ragAutoStatus: { en: "Knowledge Base: Auto", id: "Knowledge Base: Otomatis" },
  ragAutoNote: {
    en: "Document and policy questions are automatically routed to the knowledge base. No manual configuration needed.",
    id: "Pertanyaan dokumen dan kebijakan secara otomatis diarahkan ke knowledge base. Tidak perlu konfigurasi manual.",
  },
  ragAutoActiveBadge: { en: "Auto-routing active", id: "Auto-routing aktif" },
  ragConfigureManually: { en: "Override manually", id: "Konfigurasi manual" },
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
  tablePreviewData,
  tablePreviewLoading,
  onModelChange,
  onSave,
  onRagToggle,
  onRagConfigChange,
  onRagSave,
  onTableLockChange,
  onTableLockSave,
}: ModelSettingsPanelProps) {
  const [previewTab, setPreviewTab] = useState<"schema" | "data">("schema");
  const [showAdvancedRag, setShowAdvancedRag] = useState(false);
  const qwenModels = options.filter((o) => o.provider === "local_qwen");

  const isRagAutoMode = ragOptions?.enabled === true && !ragConfig.enabled;

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

              {isRagAutoMode ? (
                /* AUTO-MODE: chromadb detected, user hasn't manually configured */
                <div className="mt-4 space-y-3">
                  <div className="flex items-start gap-3 rounded-[16px] border border-emerald-200 bg-emerald-50 px-4 py-3">
                    <span className="mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full bg-emerald-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-emerald-800">
                        {tr("ragAutoStatus", lang)}
                      </p>
                      <p className="mt-0.5 text-xs leading-4 text-emerald-700">
                        {tr("ragAutoNote", lang)}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-emerald-700 whitespace-nowrap">
                      {tr("ragAutoActiveBadge", lang)}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowAdvancedRag((v) => !v)}
                    className="flex items-center gap-1 text-xs font-semibold text-[#5c63f2] hover:underline"
                  >
                    {tr("ragConfigureManually", lang)}
                    <span className="text-[10px]">{showAdvancedRag ? "▲" : "▶"}</span>
                  </button>

                  {showAdvancedRag && (
                    <div className="space-y-4 pt-1">
                      {ragOptionsLoading && (
                        <div className="rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3 text-sm text-[var(--color-ink-subtle)]">
                          {tr("ragLoading", lang)}
                        </div>
                      )}
                      <div className="flex flex-wrap items-center justify-between gap-4 rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
                        <div>
                          <p className="text-sm font-semibold text-[var(--color-ink-strong)]">{tr("ragEnable", lang)}</p>
                          <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">{tr("ragEnableNote", lang)}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => onRagToggle(!ragConfig.enabled)}
                          className="inline-flex items-center gap-3 rounded-[var(--radius-pill)] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2 text-sm font-semibold text-[var(--color-ink-muted)] transition"
                        >
                          <span>{tr("ragInactive", lang)}</span>
                          <span className="relative h-6 w-11 rounded-full bg-[#c7ccda] transition">
                            <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition" />
                          </span>
                        </button>
                      </div>
                      <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                        <span className="font-medium text-[var(--color-ink-strong)]">{tr("ragCollection", lang)}</span>
                        <select
                          value={ragConfig.collection_name ?? ""}
                          disabled={ragOptionsLoading}
                          onChange={(e) => onRagConfigChange({ ...ragConfig, collection_name: e.target.value || null })}
                          className="rounded-[12px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none disabled:opacity-50"
                        >
                          <option value="">{tr("ragCollectionPlaceholder", lang)}</option>
                          {ragCollections.map((col) => (
                            <option key={col.name} value={col.name}>{col.name} ({col.document_count} chunk)</option>
                          ))}
                        </select>
                      </label>
                      <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                        <span className="font-medium text-[var(--color-ink-strong)]">
                          {tr("ragTopK", lang)}: <span className="text-[var(--color-ink-strong)]">{ragConfig.top_k}</span>
                        </span>
                        <input type="range" min={1} max={10} step={1} value={ragConfig.top_k}
                          onChange={(e) => onRagConfigChange({ ...ragConfig, top_k: Number(e.target.value) })}
                        />
                        <p className="text-xs text-[var(--color-ink-subtle)]">{tr("ragTopKNote", lang)}</p>
                      </label>
                      <div className="flex items-center justify-between gap-3 pt-1">
                        <p className="text-xs text-[var(--color-ink-subtle)]">{tr("ragConfigUnsaved", lang)}</p>
                        <button type="button" onClick={onRagSave} disabled={!ragCanSave}
                          className="rounded-[var(--radius-pill)] bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] px-5 py-2 text-sm font-semibold text-white shadow-[var(--shadow-accent)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60">
                          {ragSaving ? tr("ragSaving", lang) : tr("ragSave", lang)}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* MANUAL MODE: user explicitly configured, or chromadb not available */
                <div className="mt-4 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-4 rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-4">
                    <div>
                      <p className="text-sm font-semibold text-[var(--color-ink-strong)]">{tr("ragEnable", lang)}</p>
                      <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">{tr("ragEnableNote", lang)}</p>
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
                      <span className={`relative h-6 w-11 rounded-full transition ${ragConfig.enabled ? "bg-emerald-500" : "bg-[#c7ccda]"}`}>
                        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition ${ragConfig.enabled ? "left-[22px]" : "left-0.5"}`} />
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

                  <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                    <span className="font-medium text-[var(--color-ink-strong)]">{tr("ragCollection", lang)}</span>
                    <select
                      value={ragConfig.collection_name ?? ""}
                      disabled={ragOptionsLoading || !ragConfig.enabled}
                      onChange={(e) => onRagConfigChange({ ...ragConfig, collection_name: e.target.value || null })}
                      className="rounded-[12px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 outline-none disabled:opacity-50"
                    >
                      <option value="">{tr("ragCollectionPlaceholder", lang)}</option>
                      {ragCollections.map((col) => (
                        <option key={col.name} value={col.name}>{col.name} ({col.document_count} chunk)</option>
                      ))}
                    </select>
                    {ragCollections.length === 0 && !ragOptionsLoading && ragConfig.enabled && (
                      <p className="text-xs text-[var(--color-ink-subtle)]">{tr("ragNoCollection", lang)}</p>
                    )}
                  </label>

                  <label className="flex flex-col gap-2 text-sm text-[var(--color-ink-muted)]">
                    <span className="font-medium text-[var(--color-ink-strong)]">
                      {tr("ragTopK", lang)}: <span className="text-[var(--color-ink-strong)]">{ragConfig.top_k}</span>
                    </span>
                    <input type="range" min={1} max={10} step={1} value={ragConfig.top_k}
                      disabled={!ragConfig.enabled}
                      onChange={(e) => onRagConfigChange({ ...ragConfig, top_k: Number(e.target.value) })}
                      className="disabled:opacity-50"
                    />
                    <p className="text-xs text-[var(--color-ink-subtle)]">{tr("ragTopKNote", lang)}</p>
                  </label>

                  <div className="flex items-center justify-between gap-3 pt-1">
                    <p className="text-xs text-[var(--color-ink-subtle)]">
                      {ragConfigLocked ? tr("ragConfigLocked", lang) : tr("ragConfigUnsaved", lang)}
                    </p>
                    <button type="button" onClick={onRagSave} disabled={!ragCanSave}
                      className="rounded-[var(--radius-pill)] bg-[linear-gradient(135deg,#6970ff_0%,#5c63f2_100%)] px-5 py-2 text-sm font-semibold text-white shadow-[var(--shadow-accent)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60">
                      {ragSaving ? tr("ragSaving", lang) : tr("ragSave", lang)}
                    </button>
                  </div>
                </div>
              )}
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
                    customer_dormant_segment
                  </p>
                </div>
              </div>
              <p className="mb-4 text-xs leading-5 text-[var(--color-ink-muted)]">
                {tr("tableNote", lang)}
              </p>

              {/* Tab switcher */}
              <div className="mb-3 flex gap-1 rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] p-1">
                {(["schema", "data"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setPreviewTab(tab)}
                    className={`flex-1 rounded-[10px] py-1.5 text-xs font-semibold transition ${
                      previewTab === tab
                        ? "bg-white text-[var(--color-ink-strong)] shadow-sm"
                        : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink-strong)]"
                    }`}
                  >
                    {tab === "schema"
                      ? lang === "id" ? "Skema" : "Schema"
                      : lang === "id" ? "Preview Data" : "Preview Data"}
                  </button>
                ))}
              </div>

              {previewTab === "schema" ? (
                <div className="max-h-[520px] overflow-y-auto rounded-[12px] border border-[var(--color-border-soft)]">
                  {TABLE_SCHEMA_SECTIONS.map((section) => (
                    <div key={section.section.en}>
                      <div className="sticky top-0 z-10 border-b border-[var(--color-border-soft)] bg-[#eef1ff] px-3 py-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#4953d3]">
                          {section.section[lang]}
                        </span>
                      </div>
                      {section.columns.map((col, idx) => (
                        <div
                          key={col.key}
                          className={`flex items-start gap-2 px-3 py-2 text-xs ${
                            idx < section.columns.length - 1 ? "border-b border-[var(--color-border-soft)]" : ""
                          }`}
                        >
                          <span className="w-44 shrink-0 font-mono text-[#4953d3]">{col.key}</span>
                          <span className="w-20 shrink-0 text-[var(--color-ink-subtle)]">{col.type}</span>
                          <span className="text-[var(--color-ink-muted)]">
                            {lang === "id" ? col.desc_id : col.desc_en}
                          </span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-[12px] border border-[var(--color-border-soft)]">
                  {tablePreviewLoading ? (
                    <div className="flex items-center justify-center py-10 text-sm text-[var(--color-ink-subtle)]">
                      {lang === "id" ? "Memuat data…" : "Loading data…"}
                    </div>
                  ) : tablePreviewData && tablePreviewData.columns.length > 0 ? (
                    (() => {
                      const allCols = tablePreviewData.columns;
                      const truncate = (val: unknown, max = 16): string => {
                        const s = val === null || val === undefined ? "" : String(val);
                        return s.length > max ? s.slice(0, max) + "…" : s;
                      };
                      return (
                        <div className="overflow-hidden rounded-[12px]">
                          <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: 320 }}>
                            <table className="text-xs" style={{ minWidth: "max-content", borderCollapse: "collapse" }}>
                              <thead>
                                <tr className="border-b border-[var(--color-border-soft)] bg-[var(--color-surface-muted)]">
                                  {allCols.map((col) => (
                                    <th key={col} className="whitespace-nowrap px-3 py-2 text-left font-mono font-semibold text-[#4953d3]" style={{ position: "sticky", top: 0, background: "var(--color-surface-muted)", zIndex: 10 }}>
                                      {col}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {tablePreviewData.rows.map((row, rowIdx) => (
                                  <tr
                                    key={rowIdx}
                                    className={rowIdx < tablePreviewData.rows.length - 1 ? "border-b border-[var(--color-border-soft)]" : ""}
                                  >
                                    {allCols.map((col) => (
                                      <td key={col} className="whitespace-nowrap px-3 py-2 text-[var(--color-ink-muted)]">
                                        {row[col] === null || row[col] === undefined ? (
                                          <span className="italic text-[var(--color-ink-subtle)]">—</span>
                                        ) : (
                                          <span title={String(row[col])}>
                                            {truncate(row[col])}
                                          </span>
                                        )}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <div className="border-t border-[var(--color-border-soft)] px-3 py-1.5">
                            <span className="text-[10px] text-[var(--color-ink-subtle)]">
                              {lang === "id"
                                ? `${allCols.length} kolom · ${tablePreviewData.rows.length} baris · geser ke kanan untuk lihat semua kolom`
                                : `${allCols.length} columns · ${tablePreviewData.rows.length} rows · scroll right to see all columns`}
                            </span>
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="flex items-center justify-center py-10 text-sm text-[var(--color-ink-subtle)]">
                      {lang === "id" ? "Tidak ada data tersedia." : "No preview data available."}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
