"use client";

import { useEffect, useRef } from "react";

interface ChatInputPanelProps {
  question: string;
  loading: boolean;
  starterPrompts: string[];
  onQuestionChange: (value: string) => void;
  onStarterSelect: (value: string) => void;
  onSubmit: () => void;
}

export function ChatInputPanel({
  question,
  loading,
  starterPrompts,
  onQuestionChange,
  onStarterSelect,
  onSubmit,
}: ChatInputPanelProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [question]);

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    if (!loading) onSubmit();
  }

  return (
    <section
      className="rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] shadow-panel"
      style={{ padding: "var(--space-4)" }}
    >
      <div
        className="rounded-[var(--radius-control)] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)]"
        style={{ padding: "var(--space-4)" }}
      >
        <textarea
          ref={textareaRef}
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          placeholder="Tanyakan tentang segmentasi nasabah, credit risk, churn probability, atau analitik cabang Bank XYZ."
          className="w-full overflow-hidden bg-transparent px-1 py-1 text-sm leading-6 text-[var(--color-ink-strong)] outline-none placeholder:text-[var(--color-ink-subtle)]"
          style={{ resize: "none" }}
        />

        <div className="mt-3 flex items-center justify-end border-t border-[var(--color-border-soft)] pt-3">
          <button
            type="button"
            disabled={loading}
            onClick={onSubmit}
            className="inline-flex items-center gap-2 rounded-[var(--radius-button)] px-5 py-2.5 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60"
            style={{ background: "linear-gradient(135deg, #FF6B00 0%, #E54E00 100%)" }}
            onMouseEnter={(e) => {
              if (!loading) {
                (e.currentTarget as HTMLButtonElement).style.background =
                  "linear-gradient(135deg, #FFA726 0%, #F25C00 100%)";
                (e.currentTarget as HTMLButtonElement).style.boxShadow =
                  "0px 4px 12px rgba(255, 107, 0, 0.35)";
              }
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background =
                "linear-gradient(135deg, #FF6B00 0%, #E54E00 100%)";
              (e.currentTarget as HTMLButtonElement).style.boxShadow = "";
            }}
          >
            {loading ? (
              <>
                <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Analyzing…
              </>
            ) : (
              <>
                Ask
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
    </section>
  );
}
