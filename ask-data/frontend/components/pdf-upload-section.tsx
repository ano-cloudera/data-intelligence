"use client";

import { useRef, useState } from "react";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import AutorenewIcon from "@mui/icons-material/Autorenew";

type UploadStatus = "idle" | "uploading" | "processing" | "done" | "error";

interface PdfUploadSectionProps {
  lang: "en" | "id";
  backendUrl: string;
  defaultCollection?: string;
}

const t = {
  section:      { en: "Upload PDF to Knowledge Base", id: "Upload PDF ke Knowledge Base" },
  note:         { en: "Upload a PDF document to be processed and added to the RAG knowledge base via CAI Job.", id: "Upload dokumen PDF untuk diproses dan ditambahkan ke knowledge base RAG melalui CAI Job." },
  selectBtn:    { en: "Select PDF", id: "Pilih PDF" },
  uploadBtn:    { en: "Upload & Ingest", id: "Upload & Ingest" },
  uploading:    { en: "Uploading…", id: "Mengupload…" },
  processing:   { en: "CAI Job running…", id: "CAI Job berjalan…" },
  checkStatus:  { en: "Check Status", id: "Cek Status" },
  done:         { en: "Ingested successfully!", id: "Berhasil diingest!" },
  error:        { en: "Failed", id: "Gagal" },
  collection:   { en: "Collection", id: "Collection" },
  noFile:       { en: "No file selected", id: "Belum ada file dipilih" },
  fileTooLarge: { en: "File too large (max 50 MB).", id: "File terlalu besar (maks 50 MB)." },
  notPdf:       { en: "Only PDF files are supported.", id: "Hanya file PDF yang didukung." },
};

function tr(key: keyof typeof t, lang: "en" | "id") {
  return t[key][lang];
}

export function PdfUploadSection({ lang, backendUrl, defaultCollection = "bank_jatim_knowledge" }: PdfUploadSectionProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [collection, setCollection] = useState(defaultCollection);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [message, setMessage] = useState("");
  const [jobRunId, setJobRunId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [validationError, setValidationError] = useState("");

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setValidationError("");
    setStatus("idle");
    setMessage("");
    setJobRunId(null);

    if (!f) { setFile(null); return; }
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setValidationError(tr("notPdf", lang));
      setFile(null);
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setValidationError(tr("fileTooLarge", lang));
      setFile(null);
      return;
    }
    setFile(f);
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("uploading");
    setMessage("");
    setValidationError("");

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(
        `${backendUrl}/rag/upload-pdf?collection_name=${encodeURIComponent(collection)}`,
        { method: "POST", body: form }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      if (data.status === "processing" && data.job_run_id) {
        setJobRunId(data.job_run_id);
        setJobId(data.job_id ?? null);
        setStatus("processing");
        setMessage(data.message ?? "");
      } else {
        setStatus("done");
        setMessage(data.message ?? "Done.");
      }
    } catch (err: unknown) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Unknown error");
    }
  }

  async function handleCheckStatus() {
    if (!jobRunId) return;
    try {
      const res = await fetch(`${backendUrl}/rag/job-status/${jobRunId}`);
      const data = await res.json();
      const s: string = data.status ?? "";
      if (s === "ENGINE_SUCCEEDED") {
        setStatus("done");
        setMessage(lang === "id" ? "Job selesai! Dokumen berhasil diingest." : "Job completed! Document ingested successfully.");
      } else if (s.includes("FAILED")) {
        setStatus("error");
        setMessage(`Job ${s}`);
      } else {
        setMessage(`Status: ${s}`);
      }
    } catch {
      setMessage(lang === "id" ? "Gagal cek status." : "Failed to check status.");
    }
  }

  const busy = status === "uploading" || status === "processing";

  return (
    <section className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
        {tr("section", lang)}
      </p>
      <p className="mt-2 text-xs leading-5 text-[var(--color-ink-muted)]">
        {tr("note", lang)}
      </p>

      {/* Collection input */}
      <div className="mt-4">
        <label className="mb-1 block text-[11px] font-medium text-[var(--color-ink-muted)] uppercase tracking-wide">
          {tr("collection", lang)}
        </label>
        <input
          type="text"
          value={collection}
          onChange={(e) => setCollection(e.target.value)}
          disabled={busy}
          className="w-full rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-3 py-2 text-sm text-[var(--color-ink-base)] outline-none focus:border-[#5c63f2] focus:ring-1 focus:ring-[#5c63f2] disabled:opacity-50"
        />
      </div>

      {/* File picker */}
      <div className="mt-3 flex items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={busy}
          className="flex items-center gap-1.5 rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-3 py-2 text-xs font-medium text-[var(--color-ink-base)] hover:bg-[var(--color-surface-hover)] disabled:opacity-50"
        >
          <UploadFileIcon sx={{ fontSize: 15 }} />
          {tr("selectBtn", lang)}
        </button>
        <span className="truncate text-xs text-[var(--color-ink-muted)]">
          {file ? file.name : tr("noFile", lang)}
        </span>
      </div>

      {validationError && (
        <p className="mt-2 text-xs text-rose-500">{validationError}</p>
      )}

      {/* Upload button */}
      <button
        type="button"
        onClick={handleUpload}
        disabled={!file || busy}
        className="mt-3 flex items-center gap-1.5 rounded-[14px] bg-[#5c63f2] px-4 py-2 text-xs font-semibold text-white hover:bg-[#4a50d4] disabled:cursor-not-allowed disabled:opacity-40 transition-colors"
      >
        {status === "uploading" && <AutorenewIcon sx={{ fontSize: 14 }} className="animate-spin" />}
        {status === "uploading" ? tr("uploading", lang) : tr("uploadBtn", lang)}
      </button>

      {/* Status indicator */}
      {(status === "processing" || status === "done" || status === "error") && (
        <div className={`mt-3 flex items-start gap-2 rounded-[12px] border px-3 py-2.5 text-xs ${
          status === "done"
            ? "border-emerald-200 bg-emerald-50 text-emerald-700"
            : status === "error"
            ? "border-rose-200 bg-rose-50 text-rose-700"
            : "border-amber-200 bg-amber-50 text-amber-700"
        }`}>
          {status === "done" && <CheckCircleOutlineIcon sx={{ fontSize: 15, marginTop: "1px" }} />}
          {status === "error" && <ErrorOutlineIcon sx={{ fontSize: 15, marginTop: "1px" }} />}
          {status === "processing" && <AutorenewIcon sx={{ fontSize: 15, marginTop: "1px" }} className="animate-spin" />}
          <div className="flex-1">
            <p>{status === "processing" ? tr("processing", lang) : message}</p>
            {status === "processing" && message && (
              <p className="mt-0.5 text-[10px] opacity-70">{message}</p>
            )}
          </div>
          {status === "processing" && jobRunId && (
            <button
              type="button"
              onClick={handleCheckStatus}
              className="shrink-0 rounded-[8px] border border-amber-300 bg-white px-2 py-0.5 text-[10px] font-medium text-amber-700 hover:bg-amber-100"
            >
              {tr("checkStatus", lang)}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
