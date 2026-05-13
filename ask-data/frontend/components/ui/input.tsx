import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

const fieldBase =
  "w-full rounded-[16px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-4 text-[14px] text-[var(--color-ink-strong)] shadow-[0_1px_2px_rgba(15,23,42,0.02)] transition-all duration-150 placeholder:text-[var(--color-ink-subtle)] hover:border-[#c8cedf] hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-action-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-page-bg)] disabled:cursor-not-allowed disabled:bg-[var(--color-surface-muted)] disabled:text-[var(--color-ink-subtle)] disabled:shadow-none";

export function TextInput({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldBase, "h-12", className)} {...props} />;
}

export function TextArea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldBase, "min-h-[120px] py-3", className)} {...props} />;
}
