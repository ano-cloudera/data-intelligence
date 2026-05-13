import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "tertiary" | "destructive" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-action-primary)] text-white shadow-[var(--shadow-accent)] hover:-translate-y-[1px] hover:bg-[var(--color-action-primary-hover)] hover:shadow-[0_18px_26px_rgba(95,103,246,0.24)] active:translate-y-0 active:bg-[var(--color-action-primary-pressed)] active:shadow-[0_10px_18px_rgba(95,103,246,0.18)]",
  secondary:
    "bg-[var(--color-surface-strong)] text-[var(--color-ink-strong)] border border-[var(--color-border-soft)] hover:-translate-y-[1px] hover:bg-[var(--color-surface-muted)] hover:shadow-[0_10px_20px_rgba(15,23,42,0.06)] active:translate-y-0 active:bg-[var(--color-surface-subtle)] active:shadow-none",
  tertiary:
    "bg-transparent text-[var(--color-action-primary)] border border-transparent hover:bg-[var(--color-action-soft)] active:bg-[var(--color-surface-subtle)]",
  destructive:
    "bg-[var(--color-danger-strong)] text-white shadow-[0_14px_24px_rgba(186,26,26,0.18)] hover:-translate-y-[1px] hover:bg-[#9f111d] hover:shadow-[0_18px_30px_rgba(186,26,26,0.24)] active:translate-y-0 active:bg-[#840d18] active:shadow-[0_10px_16px_rgba(186,26,26,0.18)]",
  ghost:
    "bg-white/8 text-white hover:bg-white/14 active:bg-white/18",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 rounded-xl px-3.5 text-[13px]",
  md: "h-10 rounded-[14px] px-4 text-[13px]",
  lg: "h-12 rounded-[16px] px-5 text-[14px]",
};

export function Button({
  variant = "secondary",
  size = "md",
  className,
  children,
  leadingIcon,
  trailingIcon,
  loading = false,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  loading?: boolean;
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold tracking-[0.01em] transition-all duration-150 ease-out",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-action-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-white",
        "disabled:pointer-events-none disabled:translate-y-0 disabled:opacity-50 disabled:shadow-none",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      aria-busy={loading}
      disabled={props.disabled || loading}
      {...props}
    >
      {loading ? (
        <span
          aria-hidden="true"
          className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent opacity-80"
        />
      ) : (
        leadingIcon
      )}
      {children}
      {!loading ? trailingIcon : null}
    </button>
  );
}
