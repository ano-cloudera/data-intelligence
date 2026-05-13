import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

const toneClasses = {
  neutral: "border-[var(--color-border-soft)] bg-[var(--color-surface-strong)] text-[var(--color-ink-strong)]",
  error: "border-[#ffd4d1] bg-[#fff3f2] text-[#7c1d18]",
  warning: "border-[#ffe2c8] bg-[#fff5eb] text-[#8a3d00]",
  success: "border-[#cfe9dd] bg-[#effaf4] text-[#165b38]",
} as const;

export function SkeletonBlock({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-[14px] bg-[linear-gradient(90deg,#edf0f6_0%,#f6f8fb_50%,#edf0f6_100%)] bg-[length:200%_100%]",
        className,
      )}
      {...props}
    />
  );
}

export function StatePanel({
  title,
  description,
  action,
  tone = "neutral",
  className,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  tone?: keyof typeof toneClasses;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-[20px] border px-5 py-4 shadow-[0_6px_14px_rgba(15,23,42,0.03)]",
        toneClasses[tone],
        className,
      )}
    >
      <p className="body-strong">{title}</p>
      <p className="body-copy mt-1.5">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
