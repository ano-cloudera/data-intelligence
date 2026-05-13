import type { HTMLAttributes, ReactNode, TableHTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export function TableCard({
  className,
  children,
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function DataTable({
  className,
  children,
}: TableHTMLAttributes<HTMLTableElement>) {
  return <table className={cn("w-full border-collapse text-left", className)}>{children}</table>;
}

export function TableHeadCell({
  className,
  children,
  numeric,
  ...props
}: ThHTMLAttributes<HTMLTableCellElement> & { numeric?: boolean }) {
  return (
    <th
      className={cn(
        "bg-[var(--color-surface-muted)] px-5 py-4 text-[13px] font-semibold tracking-[0.02em] text-[var(--color-ink-subtle)]",
        "sticky top-0 z-[1] backdrop-blur-sm",
        numeric && "text-right",
        className,
      )}
      {...props}
    >
      {children}
    </th>
  );
}

export function TableCell({
  className,
  children,
  numeric,
  ...props
}: TdHTMLAttributes<HTMLTableCellElement> & { numeric?: boolean }) {
  return (
    <td
      className={cn(
        "px-5 py-4 align-middle text-[14px] font-medium leading-[1.5] text-[var(--color-ink-strong)]",
        numeric && "text-right tabular-nums",
        className,
      )}
      {...props}
    >
      {children}
    </td>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-[180px] flex-col items-center justify-center gap-3 rounded-[var(--radius-panel)] border border-dashed border-[var(--color-border-soft)] bg-[var(--color-surface)] px-6 py-10 text-center">
      <h3 className="font-headline text-[var(--font-size-card-title)] font-[var(--font-weight-card-title)] text-[var(--color-ink-strong)]">{title}</h3>
      <p className="max-w-md body-copy">{description}</p>
      {action}
    </div>
  );
}
