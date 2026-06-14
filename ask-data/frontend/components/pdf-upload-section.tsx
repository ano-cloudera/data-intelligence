"use client";

import { useEffect, useRef, useState } from "react";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutlined";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutlined";
import AutorenewIcon from "@mui/icons-material/Autorenew";
import CloseIcon from "@mui/icons-material/Close";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";

interface FileEntry {
  id: string;
  file: File;
  status: "idle" | "uploading" | "processing" | "done" | "error";
  progress: number; // 0–100
  message: string;
  jobRunId: string | null;
  pollCount: number;
}

interface PdfUploadSectionProps {
  lang: "en" | "id";
  backendUrl: string;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
const MAX_POLL = 120; // 10 menit @ 5s interval
const POLL_INTERVAL = 5000;

const t = {
  section:        { en: "Upload PDF to Knowledge Base", id: "Upload PDF ke Knowledge Base" },
  note:           { en: "Select one or more PDF files to be processed and added to the RAG knowledge base via CAI Job.", id: "Pilih satu atau beberapa file PDF untuk diproses dan ditambahkan ke knowledge base RAG melalui CAI Job." },
  collection:     { en: "Knowledge Base Collection", id: "Koleksi Knowledge Base" },
  selectFiles:    { en: "Select PDF Files", id: "Pilih File PDF" },
  uploadAll:      { en: "Upload All", id: "Upload Semua" },
  uploading:      { en: "Uploading…", id: "Mengupload…" },
  processing:     { en: "CAI Job running…", id: "CAI Job berjalan…" },
  done:           { en: "Done", id: "Selesai" },
  error:          { en: "Failed", id: "Gagal" },
  checkStatus:    { en: "Check", id: "Cek" },
  noFiles:        { en: "No files selected", id: "Belum ada file dipilih" },
  fileTooLarge:   { en: "too large (max 50 MB)", id: "terlalu besar (maks 50 MB)" },
  notPdf:         { en: "not a PDF file", id: "bukan file PDF" },
  allDone:        { en: "All files processed!", id: "Semua file selesai diproses!" },
};

function tr(key: keyof typeof t, lang: "en" | "id") {
  return t[key][lang];
}

function uid() {
  return Math.random().toString(36).slice(2);
}

export function PdfUploadSection({ lang, backendUrl }: PdfUploadSectionProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [collections, setCollections] = useState<string[]>(["bank_jatim_knowledge"]);
  const [collection, setCollection] = useState("bank_jatim_knowledge");
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const pollTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // Fetch available collections on mount
  useEffect(() => {
    fetch(`${backendUrl}/rag/collections`)
      .then((r) => r.json())
      .then((data) => {
        const cols: string[] = data.collections ?? [];
        if (cols.length > 0) {
          setCollections(cols);
          setCollection(cols[0]);
        }
      })
      .catch(() => {});
  }, [backendUrl]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      Object.values(pollTimers.current).forEach(clearTimeout);
    };
  }, []);

  function updateEntry(id: string, patch: Partial<FileEntry>) {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, ...patch } : e))
    );
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? []);
    if (!selected.length) return;

    const newEntries: FileEntry[] = selected.map((file) => {
      let status: FileEntry["status"] = "idle";
      let message = "";

      if (!file.name.toLowerCase().endsWith(".pdf")) {
        status = "error";
        message = `${file.name}: ${tr("notPdf", lang)}`;
      } else if (file.size > MAX_FILE_SIZE) {
        status = "error";
        message = `${file.name}: ${tr("fileTooLarge", lang)}`;
      }

      return {
        id: uid(),
        file,
        status,
        progress: 0,
        message,
        jobRunId: null,
        pollCount: 0,
      };
    });

    setEntries((prev) => [...prev, ...newEntries]);
    // Reset input so same files can be re-added after removal
    e.target.value = "";
  }

  function removeEntry(id: string) {
    clearTimeout(pollTimers.current[id]);
    delete pollTimers.current[id];
    setEntries((prev) => prev.filter((e) => e.id !== id));
  }

  // Upload single file via XHR to track upload progress (fetch doesn't support it)
  function uploadFile(entry: FileEntry): Promise<void> {
    return new Promise((resolve) => {
      updateEntry(entry.id, { status: "uploading", progress: 0, message: "" });

      const form = new FormData();
      form.append("file", entry.file);

      const xhr = new XMLHttpRequest();

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          // Upload phase = 0–50%
          const pct = Math.round((e.loaded / e.total) * 50);
          updateEntry(entry.id, { progress: pct });
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            if (data.status === "processing" && data.job_run_id) {
              updateEntry(entry.id, {
                status: "processing",
                progress: 50,
                jobRunId: data.job_run_id,
                message: "",
              });
              startPolling(entry.id, data.job_run_id);
            } else {
              updateEntry(entry.id, {
                status: "done",
                progress: 100,
                message: data.message ?? "",
              });
            }
          } catch {
            updateEntry(entry.id, { status: "error", message: "Invalid response" });
          }
        } else {
          let detail = "Upload failed";
          try { detail = JSON.parse(xhr.responseText)?.detail ?? detail; } catch {}
          updateEntry(entry.id, { status: "error", progress: 0, message: detail });
        }
        resolve();
      };

      xhr.onerror = () => {
        updateEntry(entry.id, { status: "error", progress: 0, message: "Network error" });
        resolve();
      };

      xhr.open(
        "POST",
        `${backendUrl}/rag/upload-pdf?collection_name=${encodeURIComponent(collection)}`
      );
      xhr.send(form);
    });
  }

  function startPolling(id: string, jobRunId: string) {
    let count = 0;

    async function poll() {
      if (count >= MAX_POLL) {
        updateEntry(id, { status: "error", message: "Timeout waiting for CAI Job" });
        return;
      }

      try {
        const res = await fetch(`${backendUrl}/rag/job-status/${jobRunId}`);
        const data = await res.json();
        const s: string = data.status ?? "";
        count++;

        if (s === "ENGINE_SUCCEEDED") {
          updateEntry(id, { status: "done", progress: 100, pollCount: count });
          return;
        } else if (s.includes("FAILED")) {
          updateEntry(id, { status: "error", progress: 0, message: `Job ${s}`, pollCount: count });
          return;
        } else {
          // Ease progress from 50% → 95% during processing
          const progress = Math.min(95, 50 + Math.round((count / MAX_POLL) * 45 * 10));
          updateEntry(id, { progress, pollCount: count });
        }
      } catch {
        count++;
      }

      pollTimers.current[id] = setTimeout(poll, POLL_INTERVAL);
    }

    pollTimers.current[id] = setTimeout(poll, POLL_INTERVAL);
  }

  async function handleUploadAll() {
    const toUpload = entries.filter((e) => e.status === "idle");
    // Sequential upload — safer for CAI rate limits
    for (const entry of toUpload) {
      await uploadFile(entry);
    }
  }

  async function handleCheckStatus(entry: FileEntry) {
    if (!entry.jobRunId) return;
    try {
      const res = await fetch(`${backendUrl}/rag/job-status/${entry.jobRunId}`);
      const data = await res.json();
      const s: string = data.status ?? "";
      if (s === "ENGINE_SUCCEEDED") {
        updateEntry(entry.id, { status: "done", progress: 100 });
      } else if (s.includes("FAILED")) {
        updateEntry(entry.id, { status: "error", progress: 0, message: `Job ${s}` });
      } else {
        updateEntry(entry.id, { message: `Status: ${s}` });
      }
    } catch {
      updateEntry(entry.id, { message: lang === "id" ? "Gagal cek status." : "Failed to check status." });
    }
  }

  const idleCount = entries.filter((e) => e.status === "idle").length;
  const allDone = entries.length > 0 && entries.every((e) => e.status === "done");
  const anyBusy = entries.some((e) => e.status === "uploading" || e.status === "processing");

  return (
    <section className="rounded-[20px] border border-[var(--color-border-soft)] bg-white p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--color-ink-subtle)]">
        {tr("section", lang)}
      </p>
      <p className="mt-2 text-xs leading-5 text-[var(--color-ink-muted)]">
        {tr("note", lang)}
      </p>

      {/* Collection dropdown */}
      <div className="mt-4">
        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-[var(--color-ink-muted)]">
          {tr("collection", lang)}
        </label>
        <select
          value={collection}
          onChange={(e) => setCollection(e.target.value)}
          disabled={anyBusy}
          className="w-full rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-3 py-2 text-sm text-[var(--color-ink-base)] outline-none focus:border-[#5c63f2] focus:ring-1 focus:ring-[#5c63f2] disabled:opacity-50"
        >
          {collections.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* File picker + Upload button */}
      <div className="mt-3 flex items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={anyBusy}
          className="flex items-center gap-1.5 rounded-[12px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-3 py-2 text-xs font-medium text-[var(--color-ink-base)] hover:bg-[var(--color-surface-hover)] disabled:opacity-50 transition-colors"
        >
          <FolderOpenIcon sx={{ fontSize: 15 }} />
          {tr("selectFiles", lang)}
        </button>

        {idleCount > 0 && (
          <button
            type="button"
            onClick={handleUploadAll}
            disabled={anyBusy}
            className="flex items-center gap-1.5 rounded-[12px] bg-[#5c63f2] px-4 py-2 text-xs font-semibold text-white hover:bg-[#4a50d4] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <UploadFileIcon sx={{ fontSize: 14 }} />
            {tr("uploadAll", lang)} ({idleCount})
          </button>
        )}
      </div>

      {/* File list */}
      {entries.length > 0 && (
        <div className="mt-4 space-y-2">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-3 py-2.5"
            >
              {/* Top row: filename + status icon + remove */}
              <div className="flex items-center gap-2">
                <span className="flex-1 truncate text-xs font-medium text-[var(--color-ink-base)]">
                  {entry.file.name}
                </span>

                {/* Status icon */}
                {entry.status === "done" && (
                  <CheckCircleOutlineIcon sx={{ fontSize: 15 }} className="text-emerald-500 shrink-0" />
                )}
                {entry.status === "error" && (
                  <ErrorOutlineIcon sx={{ fontSize: 15 }} className="text-rose-500 shrink-0" />
                )}
                {(entry.status === "uploading" || entry.status === "processing") && (
                  <AutorenewIcon sx={{ fontSize: 15 }} className="animate-spin text-[#5c63f2] shrink-0" />
                )}

                {/* Check status button (processing only) */}
                {entry.status === "processing" && entry.jobRunId && (
                  <button
                    type="button"
                    onClick={() => handleCheckStatus(entry)}
                    className="shrink-0 rounded-[8px] border border-amber-300 bg-white px-2 py-0.5 text-[10px] font-medium text-amber-700 hover:bg-amber-50"
                  >
                    {tr("checkStatus", lang)}
                  </button>
                )}

                {/* Remove button */}
                {entry.status !== "uploading" && entry.status !== "processing" && (
                  <button
                    type="button"
                    onClick={() => removeEntry(entry.id)}
                    className="shrink-0 text-[var(--color-ink-subtle)] hover:text-rose-500 transition-colors"
                  >
                    <CloseIcon sx={{ fontSize: 14 }} />
                  </button>
                )}
              </div>

              {/* Progress bar */}
              {(entry.status === "uploading" || entry.status === "processing" || entry.status === "done") && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-[10px] text-[var(--color-ink-muted)]">
                      {entry.status === "uploading"
                        ? tr("uploading", lang)
                        : entry.status === "processing"
                        ? tr("processing", lang)
                        : tr("done", lang)}
                    </span>
                    <span className="text-[10px] font-semibold text-[#5c63f2]">
                      {entry.progress}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-[var(--color-border-soft)] overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        entry.status === "done"
                          ? "bg-emerald-500"
                          : "bg-[#5c63f2]"
                      }`}
                      style={{ width: `${entry.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Error / message */}
              {entry.status === "error" && entry.message && (
                <p className="mt-1.5 text-[10px] text-rose-500">{entry.message}</p>
              )}
              {entry.status === "done" && entry.message && (
                <p className="mt-1.5 text-[10px] text-emerald-600">{entry.message}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* All done banner */}
      {allDone && (
        <div className="mt-3 flex items-center gap-2 rounded-[12px] border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-xs text-emerald-700">
          <CheckCircleOutlineIcon sx={{ fontSize: 15 }} />
          {tr("allDone", lang)}
        </div>
      )}
    </section>
  );
}
