interface SQLPreviewCardProps {
  title: string;
  sql: string;
  subtitle?: string;
}

export function SQLPreviewCard({
  title,
  sql,
  subtitle,
}: SQLPreviewCardProps) {
  return (
    <section className="rounded-[28px] border border-white/70 bg-white/85 p-6 shadow-panel backdrop-blur">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        {subtitle ? (
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        ) : null}
      </div>
      <pre className="overflow-x-auto rounded-3xl bg-slate-950 px-4 py-4 font-mono text-sm leading-6 text-teal-100">
        <code>{sql}</code>
      </pre>
    </section>
  );
}
