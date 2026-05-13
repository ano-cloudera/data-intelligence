interface ResultTableCardProps {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  rowCount: number;
  truncated: boolean;
  limitApplied: boolean;
}

export function ResultTableCard({
  columns,
  rows,
  rowCount,
  truncated,
  limitApplied,
}: ResultTableCardProps) {
  return (
    <section className="rounded-[28px] border border-white/70 bg-white/85 p-6 shadow-panel backdrop-blur">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Result preview</h3>
          <p className="mt-1 text-sm text-slate-500">
            {rowCount} row{rowCount === 1 ? "" : "s"} returned
            {limitApplied ? " with safety LIMIT applied" : ""}
          </p>
        </div>
        {truncated ? (
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">
            Preview truncated
          </span>
        ) : null}
      </div>

      {rows.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
          Query completed, but no rows were returned.
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-slate-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-100 text-left text-slate-600">
                <tr>
                  {columns.map((column) => (
                    <th key={column} className="px-4 py-3 font-semibold">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {rows.map((row, rowIndex) => (
                  <tr key={rowIndex} className="align-top">
                    {columns.map((column) => (
                      <td key={`${rowIndex}-${column}`} className="px-4 py-3 text-slate-700">
                        {String(row[column] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
