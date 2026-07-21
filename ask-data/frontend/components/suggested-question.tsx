"use client";

import { useState } from "react";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";

interface SuggestedQuestionProps {
  question: string;
  lang: "en" | "id";
}

export function SuggestedQuestion({ question, lang }: SuggestedQuestionProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(question);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      // clipboard unavailable — no-op, button remains usable
    }
  }

  return (
    <div className="flex items-center justify-between gap-3 rounded-[8px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-3 py-2.5">
      <span className="min-w-0 truncate text-[13px] text-[var(--color-ink-strong)]">{question}</span>
      <button
        type="button"
        onClick={handleCopy}
        aria-label={lang === "id" ? "Salin pertanyaan" : "Copy question"}
        className="flex shrink-0 items-center gap-1.5 rounded-[6px] border border-transparent px-2 py-1 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-border-soft)] hover:text-[var(--color-ink-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-action-primary)]"
      >
        {copied ? (
          <>
            <CheckIcon sx={{ fontSize: 14 }} className="text-emerald-600" />
            <span className="text-emerald-600">{lang === "id" ? "Tersalin" : "Copied"}</span>
          </>
        ) : (
          <>
            <ContentCopyIcon sx={{ fontSize: 14 }} />
            {lang === "id" ? "Salin" : "Copy"}
          </>
        )}
      </button>
    </div>
  );
}
