"use client";

import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import BarChartIcon from "@mui/icons-material/BarChart";
import CampaignIcon from "@mui/icons-material/Campaign";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import PhoneAndroidIcon from "@mui/icons-material/PhoneAndroid";
import SavingsIcon from "@mui/icons-material/Savings";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

export type StarterCardVariant = "segment" | "risk" | "balance" | "campaign" | "city" | "digital" | "default";

const variantIcon: Record<StarterCardVariant, React.ReactNode> = {
  segment: <BarChartIcon sx={{ fontSize: 16 }} />,
  risk: <WarningAmberIcon sx={{ fontSize: 16 }} />,
  balance: <SavingsIcon sx={{ fontSize: 16 }} />,
  campaign: <CampaignIcon sx={{ fontSize: 16 }} />,
  city: <LocationOnIcon sx={{ fontSize: 16 }} />,
  digital: <PhoneAndroidIcon sx={{ fontSize: 16 }} />,
  default: <BarChartIcon sx={{ fontSize: 16 }} />,
};

interface StarterCardProps {
  title: string;
  description: string;
  onClick: () => void;
  variant?: StarterCardVariant;
}

/**
 * Compact work-shortcut row — not a promotional card.
 * Used in a vertical stack under the composer on the empty-state workspace.
 */
export function StarterCard({ title, description, onClick, variant = "default" }: StarterCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex w-full items-center gap-3 rounded-[12px] border border-transparent px-3 py-2.5 text-left transition-colors hover:border-[var(--color-border-soft)] hover:bg-[var(--color-surface-muted)]"
    >
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[9px] bg-[var(--color-surface-muted)] text-[var(--color-ink-subtle)] transition-colors group-hover:bg-[var(--color-action-soft)] group-hover:text-[var(--color-action-primary)]">
        {variantIcon[variant]}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[13px] font-medium text-[var(--color-ink-strong)]">{title}</span>
        <span className="block truncate text-[12px] text-[var(--color-ink-subtle)]">{description}</span>
      </span>
      <ArrowForwardIcon
        sx={{ fontSize: 15 }}
        className="shrink-0 text-[var(--color-ink-subtle)] opacity-0 transition-opacity group-hover:opacity-100"
      />
    </button>
  );
}
