"use client";

interface DemoStageActionsProps {
  stageIndex: number;
  stageCount: number;
  onPrevious: () => void;
  onNext: () => void;
  lang: "en" | "id";
}

export function DemoStageActions({ stageIndex, stageCount, onPrevious, onNext, lang }: DemoStageActionsProps) {
  const isFirst = stageIndex === 0;
  const isLast = stageIndex === stageCount - 1;

  return (
    <div className="sticky bottom-0 mt-6 flex items-center justify-between border-t border-[var(--color-border-soft)] bg-[var(--color-surface)] px-1 py-3">
      <button
        type="button"
        onClick={onPrevious}
        disabled={isFirst}
        className="rounded-[8px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-4 py-2 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-border-strong)] hover:text-[var(--color-ink-strong)] disabled:cursor-not-allowed disabled:opacity-40"
      >
        {lang === "id" ? "Sebelumnya" : "Previous"}
      </button>
      <button
        type="button"
        onClick={onNext}
        disabled={isLast}
        className="rounded-[8px] bg-[var(--color-brand-orange)] px-4 py-2 text-xs font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isLast
          ? (lang === "id" ? "Selesai" : "Done")
          : (lang === "id" ? "Tahap Berikutnya" : "Next stage")}
      </button>
    </div>
  );
}
