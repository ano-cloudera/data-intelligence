"use client";

import { SuggestedQuestion } from "@/components/suggested-question";

interface PresenterRunbookProps {
  stageTitle: string;
  say: string;
  ask: string;
  highlight: string;
  transition: string;
  lang: "en" | "id";
}

function RunbookRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-[var(--color-border-soft)] py-4 last:border-b-0">
      <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--color-brand-orange)]">
        {label}
      </p>
      <div className="mt-2">{children}</div>
    </div>
  );
}

export function PresenterRunbook({ stageTitle, say, ask, highlight, transition, lang }: PresenterRunbookProps) {
  return (
    <div>
      <h2 className="font-headline text-lg font-bold text-[var(--color-ink-strong)]">{stageTitle}</h2>

      <div className="mt-3">
        <RunbookRow label="SAY">
          <p className="text-[14px] leading-7 text-[var(--color-ink-strong)]">{say}</p>
        </RunbookRow>

        <RunbookRow label="ASK">
          <SuggestedQuestion question={ask} lang={lang} />
        </RunbookRow>

        <RunbookRow label={lang === "id" ? "SOROTAN" : "HIGHLIGHT"}>
          <p className="text-[14px] leading-7 text-[var(--color-ink-muted)]">{highlight}</p>
        </RunbookRow>

        <RunbookRow label={lang === "id" ? "TRANSISI" : "TRANSITION"}>
          <p className="text-[14px] leading-7 text-[var(--color-ink-muted)]">{transition}</p>
        </RunbookRow>
      </div>
    </div>
  );
}
