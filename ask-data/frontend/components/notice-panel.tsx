interface NoticePanelProps {
  title: string;
  message: string;
  tone?: "empty" | "error" | "warning";
  badgeLabel?: string;
  suggestion?: string;
  compact?: boolean;
}

const toneClasses: Record<NonNullable<NoticePanelProps["tone"]>, string> = {
  empty: "border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] text-[var(--color-ink-muted)]",
  error: "border-rose-200 bg-rose-50 text-rose-700",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
};

const badgeClasses: Record<NonNullable<NoticePanelProps["tone"]>, string> = {
  empty: "bg-white/80 text-[var(--color-ink-subtle)] border-[var(--color-border-soft)]",
  error: "bg-white/60 text-rose-700 border-rose-200",
  warning: "bg-white/60 text-amber-800 border-amber-200",
};

function ToneIcon({ tone }: { tone: NonNullable<NoticePanelProps["tone"]> }) {
  if (tone === "error") {
    return (
      <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-rose-100 text-rose-600">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
          <path d="M8 1.5 14 12.5a1 1 0 0 1-.88 1.5H2.88A1 1 0 0 1 2 12.5l6-11Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
          <path d="M8 5.5v3.5M8 11.5h.01" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (tone === "warning") {
    return (
      <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-amber-100 text-amber-700">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
          <path d="M8 2.2a5.8 5.8 0 1 1 0 11.6A5.8 5.8 0 0 1 8 2.2Z" stroke="currentColor" strokeWidth="1.4" />
          <path d="M8 5.2v3.1M8 10.8h.01" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  return (
    <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white/80 text-[var(--color-ink-subtle)]">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
        <circle cx="8" cy="8" r="5.8" stroke="currentColor" strokeWidth="1.4" />
        <path d="M8 7.2v3M8 5.2h.01" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    </span>
  );
}

export function NoticePanel({
  title,
  message,
  tone = "empty",
  badgeLabel,
  suggestion,
  compact = false,
}: NoticePanelProps) {
  return (
    <section className={`rounded-[var(--radius-panel)] border shadow-panel ${compact ? "p-3 sm:p-4" : "p-5"} ${toneClasses[tone]}`}>
      <div className={`flex items-start ${compact ? "gap-2.5" : "gap-3"}`}>
        {compact ? null : <ToneIcon tone={tone} />}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className={`${compact ? "text-xs" : "text-sm"} font-semibold`}>{title}</h3>
            {badgeLabel ? (
              <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${badgeClasses[tone]}`}>
                {badgeLabel}
              </span>
            ) : null}
          </div>
          <p className={`${compact ? "mt-1 text-xs leading-5" : "mt-1.5 text-sm leading-6"} opacity-85`}>{message}</p>
          {suggestion ? (
            <p className={`${compact ? "mt-1.5 text-xs leading-5" : "mt-3 text-sm leading-6"} font-medium opacity-90`}>
              {suggestion}
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
