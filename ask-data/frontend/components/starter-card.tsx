import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";

interface StarterCardProps {
  title: string;
  description: string;
  onClick: () => void;
}

export function StarterCard({ title, description, onClick }: StarterCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-5 text-left shadow-panel transition hover:-translate-y-0.5 hover:border-[var(--color-action-primary)] hover:shadow-[0_22px_48px_rgba(255,107,0,0.12)]"
    >
      <div className="icon-box mb-4 h-9 w-9">
        <AutoAwesomeIcon sx={{ fontSize: 18 }} />
      </div>
      <h3 className="font-headline text-sm font-semibold text-[var(--color-ink-strong)]">{title}</h3>
      <p className="mt-1.5 text-xs leading-5 text-[var(--color-ink-subtle)]">{description}</p>
    </button>
  );
}
