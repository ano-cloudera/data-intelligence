"use client";

import { useEffect, useRef } from "react";

interface ChatInputPanelProps {
  question: string;
  loading: boolean;
  starterPrompts: string[];
  onQuestionChange: (value: string) => void;
  onStarterSelect: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
}

export function ChatInputPanel({
  question,
  loading,
  onQuestionChange,
  onSubmit,
  placeholder,
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
    if (!loading && question.trim()) onSubmit();
  }

  const canSubmit = !loading && question.trim().length > 0;

  return (
    <div className="flex items-end gap-2 rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-2 pl-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-colors focus-within:border-[var(--color-action-primary)] focus-within:shadow-[0_0_0_3px_rgba(92,99,242,0.1)]">
      <textarea
        ref={textareaRef}
        value={question}
        onChange={(e) => onQuestionChange(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        disabled={loading}
        placeholder={placeholder ?? "Ask anything about your customer data..."}
        className="min-h-[24px] w-full flex-1 resize-none overflow-hidden bg-transparent py-2 text-[14px] leading-6 text-[var(--color-ink-strong)] outline-none placeholder:text-[var(--color-ink-subtle)] disabled:opacity-60"
      />

      <button
        type="button"
        disabled={!canSubmit}
        onClick={onSubmit}
        aria-label="Send question"
        className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-[var(--color-action-primary)] text-white transition-all duration-150 hover:bg-[var(--color-action-primary-hover)] disabled:cursor-not-allowed disabled:bg-[var(--color-surface-subtle)] disabled:text-[var(--color-ink-subtle)]"
      >
        {loading ? (
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent opacity-80" />
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        )}
      </button>
    </div>
  );
}
