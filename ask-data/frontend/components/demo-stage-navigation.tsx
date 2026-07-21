"use client";

interface DemoStage {
  id: string;
  label: { en: string; id: string };
}

interface DemoStageNavigationProps {
  stages: readonly DemoStage[];
  activeIndex: number;
  onSelect: (index: number) => void;
  lang: "en" | "id";
}

export function DemoStageNavigation({ stages, activeIndex, onSelect, lang }: DemoStageNavigationProps) {
  return (
    <nav
      aria-label={lang === "id" ? "Tahapan demo" : "Demo stages"}
      className="flex gap-6 overflow-x-auto border-b border-[var(--color-border-soft)]"
    >
      {stages.map((stage, index) => {
        const isActive = index === activeIndex;
        return (
          <button
            key={stage.id}
            type="button"
            onClick={() => onSelect(index)}
            aria-current={isActive ? "step" : undefined}
            className={`shrink-0 whitespace-nowrap border-b-2 py-3 text-[13px] font-semibold transition ${
              isActive
                ? "border-[var(--color-brand-orange)] text-[var(--color-brand-orange)]"
                : "border-transparent text-[var(--color-ink-muted)] hover:text-[var(--color-ink-strong)]"
            }`}
          >
            {String(index + 1).padStart(2, "0")} {stage.label[lang]}
          </button>
        );
      })}
    </nav>
  );
}
