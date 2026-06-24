"use client";

import { useEffect, useRef } from "react";
import CloseIcon from "@mui/icons-material/Close";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";

interface PdfViewerModalProps {
  open: boolean;
  url: string | null;
  title: string;
  onClose: () => void;
}

export function PdfViewerModal({ open, url, title, onClose }: PdfViewerModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open || !url) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="flex h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] shadow-2xl">
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--color-border-soft)] px-5 py-3">
          <p className="truncate text-sm font-semibold text-[var(--color-ink-strong)]">{title}</p>
          <div className="flex shrink-0 items-center gap-2">
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 rounded-[12px] border border-[var(--color-border-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
            >
              <OpenInNewIcon sx={{ fontSize: 13 }} />
              Buka di tab baru
            </a>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-ink-muted)] transition hover:bg-[var(--color-surface-muted)] hover:text-[var(--color-ink-strong)]"
              aria-label="Tutup"
            >
              <CloseIcon sx={{ fontSize: 18 }} />
            </button>
          </div>
        </div>
        {/* PDF iframe */}
        <iframe
          src={url}
          title={title}
          className="flex-1 w-full border-0"
          style={{ minHeight: 0 }}
        />
      </div>
    </div>
  );
}
