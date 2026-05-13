import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type BadgeVariant =
  | "neutral"
  | "low"
  | "medium"
  | "high"
  | "critical"
  | "deployed"
  | "training"
  | "failed"
  | "archived"
  | "open"
  | "pending"
  | "reviewing"
  | "info";

const badgeClasses: Record<BadgeVariant, string> = {
  neutral: "bg-[var(--color-surface-subtle)] text-[var(--color-ink-muted)]",
  low: "bg-[#dff5e7] text-[#14633d]",
  medium: "bg-[#fff1d9] text-[#915d00]",
  high: "bg-[#ffdccc] text-[#983700]",
  critical: "bg-[#ba1a1a] text-white",
  deployed: "bg-[#dff5e7] text-[#14633d]",
  training: "bg-[#fff1d9] text-[#915d00]",
  failed: "bg-[#ffe0e0] text-[#991b1b]",
  archived: "bg-[#ebeaf5] text-[#5d5b70]",
  open: "bg-[#ffe9d7] text-[#8c3f00]",
  pending: "bg-[#ebeaf5] text-[#56527a]",
  reviewing: "bg-[#e3e4ff] text-[#3939c9]",
  info: "bg-[#e3e4ff] text-[#3939c9]",
};

export function Badge({
  children,
  variant = "neutral",
  className,
  icon,
}: {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
  icon?: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[var(--font-size-badge)] font-bold tracking-[0.06em]",
        badgeClasses[variant],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
