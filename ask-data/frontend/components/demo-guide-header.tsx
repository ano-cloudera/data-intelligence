"use client";

interface DemoGuideHeaderProps {
  title: string;
  meta: string;
  supportingText: string;
  stageIndex: number;
  stageCount: number;
}

export function DemoGuideHeader({ title, meta, supportingText, stageIndex, stageCount }: DemoGuideHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 pb-4">
      <div className="min-w-0">
        <h1 className="font-headline text-xl font-bold text-[var(--color-ink-strong)]">{title}</h1>
        <p className="mt-1 text-[12px] text-[var(--color-ink-subtle)]">{meta}</p>
        <p className="mt-2 max-w-2xl text-[13px] leading-6 text-[var(--color-ink-muted)]">{supportingText}</p>
      </div>
      <span className="shrink-0 text-[12px] font-medium tabular-nums text-[var(--color-ink-subtle)]">
        {String(stageIndex + 1).padStart(2, "0")} / {String(stageCount).padStart(2, "0")}
      </span>
    </div>
  );
}
