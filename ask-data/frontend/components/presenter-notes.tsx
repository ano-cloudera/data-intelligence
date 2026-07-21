"use client";

interface PresenterNotesProps {
  checklist: readonly string[];
  checkedState: Record<number, boolean>;
  onToggle: (index: number) => void;
  focusNote: string;
  lang: "en" | "id";
}

export function PresenterNotes({ checklist, checkedState, onToggle, focusNote, lang }: PresenterNotesProps) {
  return (
    <aside className="flex flex-col gap-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--color-ink-subtle)]">
        {lang === "id" ? "Catatan Presenter" : "Presenter Notes"}
      </p>

      <ul className="flex flex-col gap-2.5">
        {checklist.map((item, index) => {
          const checked = Boolean(checkedState[index]);
          return (
            <li key={item}>
              <label className="flex cursor-pointer items-start gap-2.5 text-[13px] leading-6 text-[var(--color-ink-muted)]">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggle(index)}
                  className="mt-1 h-3.5 w-3.5 shrink-0 rounded-[3px] border-[var(--color-border-strong)] text-[var(--color-brand-orange)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-action-primary)]"
                />
                <span className={checked ? "text-[var(--color-ink-subtle)] line-through decoration-[var(--color-border-strong)]" : ""}>
                  {item}
                </span>
              </label>
            </li>
          );
        })}
      </ul>

      <div className="border-t border-[var(--color-border-soft)] pt-3">
        <p className="text-[12px] leading-6 text-[var(--color-ink-subtle)]">
          <span className="font-semibold text-[var(--color-ink-muted)]">
            {lang === "id" ? "Fokus: " : "Focus: "}
          </span>
          {focusNote}
        </p>
      </div>
    </aside>
  );
}
