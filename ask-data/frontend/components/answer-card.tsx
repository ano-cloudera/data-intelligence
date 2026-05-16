import type { ReactNode } from "react";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import ArticleIcon from "@mui/icons-material/Article";

import type { AnswerSource } from "@/lib/api";

interface AnswerCardProps {
  answer: string;
  sources?: AnswerSource[];
}

type ContentBlock =
  | { type: "paragraph"; text: string }
  | { type: "list"; items: string[]; ordered: boolean }
  | { type: "table"; rows: string[][] };

function formatScore(score: number | null | undefined): string | null {
  if (typeof score !== "number" || Number.isNaN(score)) return null;
  return score.toFixed(3);
}

function sanitizeAnswer(answer: string): string {
  return answer
    .replace(/<a\b[^>]*>([\s\S]*?)<\/a>/gi, "$1")
    .replace(/<\/?[^>]+>/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function parseInline(text: string): ReactNode[] {
  const segments = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return segments.map((segment, index) => {
    if (segment.startsWith("**") && segment.endsWith("**")) {
      return <strong key={index}>{segment.slice(2, -2)}</strong>;
    }
    return <span key={index}>{segment}</span>;
  });
}

function isSeparatorRow(line: string): boolean {
  return line
    .split("|")
    .map((part) => part.trim())
    .filter(Boolean)
    .every((part) => /^:?-{2,}:?$/.test(part));
}

function parsePipeRow(line: string): string[] {
  return line
    .split("|")
    .map((part) => part.trim())
    .filter((part, index, array) => !(index === 0 && part === "") && !(index === array.length - 1 && part === ""));
}

function isTableLine(line: string): boolean {
  return line.includes("|") && parsePipeRow(line).length >= 2;
}

function parseAnswerBlocks(answer: string): ContentBlock[] {
  const lines = sanitizeAnswer(answer).split("\n");
  const blocks: ContentBlock[] = [];
  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];
    const line = raw.trim();

    if (!line) {
      i += 1;
      continue;
    }

    if (isTableLine(line)) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim() && isTableLine(lines[i].trim())) {
        tableLines.push(lines[i].trim());
        i += 1;
      }

      const rows = tableLines
        .filter((tableLine) => !isSeparatorRow(tableLine))
        .map(parsePipeRow)
        .filter((row) => row.length >= 2);

      if (rows.length > 0) {
        blocks.push({ type: "table", rows });
        continue;
      }
    }

    const bulletMatch = line.match(/^([-*•])\s+(.+)$/);
    const orderedMatch = line.match(/^(\d+)\.\s+(.+)$/);
    if (bulletMatch || orderedMatch) {
      const ordered = Boolean(orderedMatch);
      const items: string[] = [];

      while (i < lines.length) {
        const current = lines[i].trim();
        const currentBullet = current.match(/^([-*•])\s+(.+)$/);
        const currentOrdered = current.match(/^(\d+)\.\s+(.+)$/);
        if (ordered && currentOrdered) {
          items.push(currentOrdered[2].trim());
          i += 1;
          continue;
        }
        if (!ordered && currentBullet) {
          items.push(currentBullet[2].trim());
          i += 1;
          continue;
        }
        break;
      }

      blocks.push({ type: "list", items, ordered });
      continue;
    }

    const paragraphLines: string[] = [];
    while (i < lines.length) {
      const current = lines[i].trim();
      if (!current || isTableLine(current) || /^([-*•])\s+/.test(current) || /^\d+\.\s+/.test(current)) {
        break;
      }
      paragraphLines.push(current);
      i += 1;
    }

    blocks.push({ type: "paragraph", text: paragraphLines.join(" ") });
  }

  return blocks;
}

function renderBlock(block: ContentBlock, index: number): ReactNode {
  if (block.type === "paragraph") {
    return (
      <p key={index} className="text-[15px] leading-7 text-[var(--color-ink-strong)]">
        {parseInline(block.text)}
      </p>
    );
  }

  if (block.type === "list") {
    const ListTag = block.ordered ? "ol" : "ul";
    return (
      <ListTag
        key={index}
        className={`space-y-2 pl-5 text-[15px] leading-7 text-[var(--color-ink-strong)] ${
          block.ordered ? "list-decimal" : "list-disc"
        }`}
      >
        {block.items.map((item, itemIndex) => (
          <li key={itemIndex}>{parseInline(item)}</li>
        ))}
      </ListTag>
    );
  }

  const [header, ...body] = block.rows;
  return (
    <div
      key={index}
      className="overflow-x-auto rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)]"
    >
      <table className="min-w-full divide-y divide-[var(--color-border-soft)] text-sm">
        <thead className="bg-white/60">
          <tr>
            {header.map((cell, cellIndex) => (
              <th
                key={cellIndex}
                className="px-4 py-3 text-left font-semibold text-[var(--color-ink-strong)]"
              >
                {parseInline(cell)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--color-border-soft)]">
          {body.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-3 align-top text-[var(--color-ink-muted)]">
                  {parseInline(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AnswerCard({ answer, sources = [] }: AnswerCardProps) {
  const blocks = parseAnswerBlocks(answer);

  return (
    <section className="w-full max-w-[56rem] rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] shadow-panel">
      <div className="flex items-center gap-2 border-b border-[var(--color-border-soft)] px-5 py-3">
        <span className="icon-box h-7 w-7 rounded-full">
          <SmartToyIcon sx={{ fontSize: 16 }} />
        </span>
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
          Analyst Response
        </span>
      </div>
      <div className="space-y-4 px-5 py-4">
        {blocks.map((block, index) => renderBlock(block, index))}

        {sources.length > 0 ? (
          <div className="mt-5 border-t border-[var(--color-border-soft)] pt-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--color-ink-subtle)]">
              Relevant Documents ({sources.length})
            </p>
            <div className="grid gap-3">
              {sources.map((source, index) => (
                <div
                  key={`${source.document_id ?? "doc"}-${source.node_id ?? index}`}
                  className="rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface-muted)] px-4 py-3"
                >
                  {/* Header row */}
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[rgba(255,107,0,0.1)] text-[var(--color-brand-orange)]">
                        <ArticleIcon sx={{ fontSize: 15 }} />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-[var(--color-ink-strong)]">
                          {source.title}
                        </p>
                        {formatScore(source.score) ? (
                          <p className="text-[10px] text-[var(--color-ink-subtle)]">
                            Relevance: {formatScore(source.score)}
                          </p>
                        ) : null}
                      </div>
                      <span className="shrink-0 rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.14em] text-rose-700">
                        PDF
                      </span>
                    </div>
                    {/* Action buttons */}
                    <div className="flex shrink-0 gap-2">
                      {source.preview_url ? (
                        <a
                          href={source.preview_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-[12px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[var(--color-action-primary)] hover:text-[var(--color-action-primary)]"
                        >
                          Buka PDF
                        </a>
                      ) : null}
                      {source.download_url ? (
                        <a
                          href={source.download_url}
                          download
                          className="rounded-[12px] border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)] transition hover:border-[#5c63f2] hover:text-[#5c63f2]"
                        >
                          Unduh
                        </a>
                      ) : null}
                      {!source.preview_url && !source.download_url ? (
                        <span className="rounded-[12px] border border-[var(--color-border-soft)] bg-white/50 px-3 py-1.5 text-xs font-medium text-[var(--color-ink-subtle)]">
                          Link tidak tersedia
                        </span>
                      ) : null}
                    </div>
                  </div>
                  {/* Excerpt */}
                  {source.excerpt ? (
                    <p className="mt-3 line-clamp-3 text-xs leading-5 text-[var(--color-ink-muted)]">
                      {source.excerpt}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
