import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

export type ShellNavItem = {
  key: string;
  label: string;
  icon: ReactNode;
  active?: boolean;
  onSelect?: () => void;
};

export function SidebarNavButton({
  active,
  icon,
  label,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  active?: boolean;
  icon: ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      className={cn(
        "group mx-2 flex w-[calc(100%-1rem)] items-center gap-3 rounded-2xl border px-4 py-3.5 text-left transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8ec5ff] focus-visible:ring-offset-2 focus-visible:ring-offset-[#08004D]",
        "active:translate-y-px",
        active
          ? "border-[#7dcfff] bg-[linear-gradient(180deg,#6970ff_0%,#5c63f2_100%)] text-white shadow-[0_16px_28px_rgba(92,99,242,0.24)]"
          : "border-transparent bg-transparent text-[#8f94ff] hover:border-white/6 hover:bg-white/[0.055] hover:text-[#c5c7ff]",
        className,
      )}
      aria-current={active ? "page" : undefined}
      {...props}
    >
      <span
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border transition-colors duration-150",
          active
            ? "border-white/12 bg-white/12 text-white"
            : "border-white/6 bg-white/[0.04] text-[#9ea1ff] group-hover:border-white/10 group-hover:bg-white/[0.08] group-hover:text-[#d6d8ff]",
        )}
      >
        {icon}
      </span>
      <span className="min-w-0 font-headline text-[15px] font-semibold tracking-[-0.01em]">
        {label}
      </span>
    </button>
  );
}

export function AppSidebar({
  brand,
  items,
  footer,
}: {
  brand: ReactNode;
  items: ShellNavItem[];
  footer?: ReactNode;
}) {
  return (
    <aside className="app-sidebar hidden lg:fixed lg:left-0 lg:top-0 lg:z-50 lg:flex lg:h-full lg:w-[var(--shell-sidebar-w)] lg:flex-col lg:overflow-hidden lg:py-7 lg:shadow-2xl">
      <div className="px-5 pb-2">{brand}</div>
      <nav className="nav-group mt-6 flex-1">
        {items.map((item) => (
          <SidebarNavButton
            key={item.key}
            active={item.active}
            icon={item.icon}
            label={item.label}
            onClick={item.onSelect}
          />
        ))}
      </nav>
      {footer ? <div className="mt-auto px-2">{footer}</div> : null}
    </aside>
  );
}

export function AppTopHeader({
  left,
  right,
}: {
  left: ReactNode;
  right?: ReactNode;
}) {
  return (
    <header className="app-topbar sticky left-0 right-0 top-0 z-40 border-b border-[var(--color-border-soft)] shadow-[0_8px_24px_rgba(15,23,42,0.04)] lg:left-[var(--shell-sidebar-w)]">
      <div className="absolute inset-x-0 bottom-0 h-[2px] bg-[#5F67F6]" />
      <div className="relative flex min-h-[var(--shell-header-h)] w-full flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8 lg:py-0">
        <div className="topbar-meta min-w-0">{left}</div>
        {right ? <div className="flex w-full flex-wrap items-center gap-3 lg:ml-6 lg:w-auto lg:shrink-0 lg:justify-end">{right}</div> : null}
      </div>
    </header>
  );
}

export function AppShell({
  sidebar,
  header,
  children,
}: {
  sidebar: ReactNode;
  header: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="app-shell text-[var(--color-ink-strong)]">
      {sidebar}
      <div className="min-h-screen lg:ml-[var(--shell-sidebar-w)]">
        {header}
        <main className="min-h-[calc(100vh-var(--shell-header-h))] bg-[var(--color-page-bg)]">
          {children}
        </main>
      </div>
    </div>
  );
}

export function PageCanvas({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("page-canvas", className)} {...props}>
      {children}
    </div>
  );
}

export function PageHeaderBlock({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("page-header-block", className)} {...props}>
      {children}
    </div>
  );
}

export function PageSection({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLElement>) {
  return (
    <section className={cn("page-section", className)} {...props}>
      {children}
    </section>
  );
}

export function FilterBar({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("filter-bar", className)} {...props}>
      {children}
    </div>
  );
}

export function FilterGroup({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("filter-group", className)} {...props}>
      {children}
    </div>
  );
}

export function MetricGrid({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("metric-grid", className)} {...props}>
      {children}
    </div>
  );
}

export function StickyRail({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("sticky-rail", className)} {...props}>
      {children}
    </div>
  );
}
