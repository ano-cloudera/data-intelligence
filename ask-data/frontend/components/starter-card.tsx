"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import BarChartIcon from "@mui/icons-material/BarChart";
import CampaignIcon from "@mui/icons-material/Campaign";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import PhoneAndroidIcon from "@mui/icons-material/PhoneAndroid";
import SavingsIcon from "@mui/icons-material/Savings";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

export type StarterCardVariant = "segment" | "risk" | "balance" | "campaign" | "city" | "digital" | "default";

const variantStyles: Record<StarterCardVariant, { icon: React.ReactNode; hover: string; iconBg: string }> = {
  segment: {
    icon: <BarChartIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-[#5c63f2] hover:shadow-[0_22px_48px_rgba(92,99,242,0.13)]",
    iconBg: "bg-[rgba(92,99,242,0.1)] text-[#4953d3]",
  },
  risk: {
    icon: <WarningAmberIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-rose-400 hover:shadow-[0_22px_48px_rgba(244,63,94,0.12)]",
    iconBg: "bg-rose-50 text-rose-600",
  },
  balance: {
    icon: <SavingsIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-emerald-400 hover:shadow-[0_22px_48px_rgba(16,185,129,0.12)]",
    iconBg: "bg-emerald-50 text-emerald-600",
  },
  campaign: {
    icon: <CampaignIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-orange-400 hover:shadow-[0_22px_48px_rgba(251,146,60,0.13)]",
    iconBg: "bg-orange-50 text-orange-600",
  },
  city: {
    icon: <LocationOnIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-sky-400 hover:shadow-[0_22px_48px_rgba(14,165,233,0.12)]",
    iconBg: "bg-sky-50 text-sky-600",
  },
  digital: {
    icon: <PhoneAndroidIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-violet-400 hover:shadow-[0_22px_48px_rgba(139,92,246,0.12)]",
    iconBg: "bg-violet-50 text-violet-600",
  },
  default: {
    icon: <AutoAwesomeIcon sx={{ fontSize: 18 }} />,
    hover: "hover:border-[var(--color-action-primary)] hover:shadow-[0_22px_48px_rgba(255,107,0,0.12)]",
    iconBg: "bg-[rgba(255,107,0,0.08)] text-[var(--color-action-primary)]",
  },
};

interface StarterCardProps {
  title: string;
  description: string;
  onClick: () => void;
  variant?: StarterCardVariant;
}

export function StarterCard({ title, description, onClick, variant = "default" }: StarterCardProps) {
  const { icon, hover, iconBg } = variantStyles[variant];
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[var(--color-surface)] p-5 text-left shadow-panel transition hover:-translate-y-0.5 ${hover}`}
    >
      <div className={`mb-4 flex h-9 w-9 items-center justify-center rounded-[12px] ${iconBg}`}>
        {icon}
      </div>
      <h3 className="font-headline text-sm font-semibold text-[var(--color-ink-strong)]">{title}</h3>
      <p className="mt-1.5 text-xs leading-5 text-[var(--color-ink-subtle)]">{description}</p>
    </button>
  );
}
