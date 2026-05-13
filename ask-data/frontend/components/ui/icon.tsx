import { cn } from "@/lib/cn";

export function AppIcon({
  name,
  className = "h-5 w-5",
}: {
  name: string;
  className?: string;
}) {
  const common = {
    className: cn("shrink-0", className),
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    viewBox: "0 0 24 24",
    "aria-hidden": true,
  };

  switch (name) {
    case "dashboard":
      return (
        <svg {...common}>
          <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
          <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
          <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
          <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
        </svg>
      );
    case "smart_toy":
      return (
        <svg {...common}>
          <path d="M12 3.5v3" />
          <path d="M7.5 9.5A2.5 2.5 0 0 1 10 7h4a2.5 2.5 0 0 1 2.5 2.5v5A3.5 3.5 0 0 1 13 18H11a3.5 3.5 0 0 1-3.5-3.5z" />
          <circle cx="10" cy="12" r="1" />
          <circle cx="14" cy="12" r="1" />
          <path d="M10 15h4" />
          <path d="M7.5 11H5.5" />
          <path d="M18.5 11h-2" />
        </svg>
      );
    case "policy":
    case "shield":
      return (
        <svg {...common}>
          <path d="M12 3.5 18.5 6v5.4c0 4.3-2.7 8.2-6.5 9.6-3.8-1.4-6.5-5.3-6.5-9.6V6z" />
          <path d="m9.5 12 1.8 1.8 3.7-3.8" />
        </svg>
      );
    case "hub":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="2.2" />
          <circle cx="5.5" cy="7" r="1.8" />
          <circle cx="18.5" cy="7" r="1.8" />
          <circle cx="5.5" cy="17" r="1.8" />
          <circle cx="18.5" cy="17" r="1.8" />
          <path d="M10.3 10.7 6.9 8.2" />
          <path d="m13.7 10.7 3.4-2.5" />
          <path d="m10.3 13.3-3.4 2.5" />
          <path d="m13.7 13.3 3.4 2.5" />
        </svg>
      );
    case "settings":
    case "tune":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="2.8" />
          <path d="M12 4.5v2" />
          <path d="M12 17.5v2" />
          <path d="M4.5 12h2" />
          <path d="M17.5 12h2" />
          <path d="m6.8 6.8 1.4 1.4" />
          <path d="m15.8 15.8 1.4 1.4" />
          <path d="m17.2 6.8-1.4 1.4" />
          <path d="m8.2 15.8-1.4 1.4" />
        </svg>
      );
    case "group":
      return (
        <svg {...common}>
          <circle cx="12" cy="8.5" r="2.6" />
          <path d="M6.5 18a5.5 5.5 0 0 1 11 0" />
        </svg>
      );
    case "groups":
      return (
        <svg {...common}>
          <circle cx="9" cy="9" r="2.4" />
          <circle cx="16.5" cy="10" r="2" />
          <path d="M4.8 18a4.5 4.5 0 0 1 8.4 0" />
          <path d="M13.6 18a3.8 3.8 0 0 1 6 0" />
        </svg>
      );
    case "filter_list":
      return (
        <svg {...common}>
          <path d="M4 7h16" />
          <path d="M7 12h10" />
          <path d="M10 17h4" />
        </svg>
      );
    case "monitoring":
    case "query_stats":
      return (
        <svg {...common}>
          <path d="M4 19.5h16" />
          <path d="M6.5 15.5 10 12l3 2.2 4.5-5.7" />
          <path d="M17.5 8.5h2v2" />
        </svg>
      );
    case "donut_large":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="7.5" />
          <path d="M12 4.5a7.5 7.5 0 0 1 7.5 7.5" />
          <path d="M12 12V4.5" />
        </svg>
      );
    case "neurology":
      return (
        <svg {...common}>
          <circle cx="12" cy="5.5" r="1.5" />
          <circle cx="6" cy="10" r="1.5" />
          <circle cx="18" cy="10" r="1.5" />
          <circle cx="8" cy="17.5" r="1.5" />
          <circle cx="16" cy="17.5" r="1.5" />
          <path d="M12 7v3" />
          <path d="m10.8 9.8-3.3-.6" />
          <path d="m13.2 9.8 3.3-.6" />
          <path d="M7 11.5 8 16" />
          <path d="m17 11.5-1 4.5" />
          <path d="M9.5 17.5h5" />
        </svg>
      );
    case "public":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M3.8 12h16.4" />
          <path d="M12 3.8a13.4 13.4 0 0 1 0 16.4" />
          <path d="M12 3.8a13.4 13.4 0 0 0 0 16.4" />
        </svg>
      );
    case "arrow_forward":
      return (
        <svg {...common}>
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      );
    case "crisis_alert":
    case "report":
      return (
        <svg {...common}>
          <path d="M12 4.5 20 18.5H4z" />
          <path d="M12 9v4.5" />
          <path d="M12 16.5h.01" />
        </svg>
      );
    case "priority_high":
      return (
        <svg {...common}>
          <path d="M12 5.5v8" />
          <path d="M12 17.5h.01" />
        </svg>
      );
    case "share":
      return (
        <svg {...common}>
          <circle cx="6" cy="12" r="2" />
          <circle cx="17.5" cy="6" r="2" />
          <circle cx="17.5" cy="18" r="2" />
          <path d="m7.8 11 7.9-4" />
          <path d="m7.8 13 7.9 4" />
        </svg>
      );
    case "smartphone":
      return (
        <svg {...common}>
          <rect x="7.5" y="3.5" width="9" height="17" rx="2" />
          <path d="M11 6h2" />
          <path d="M11.5 17.5h1" />
        </svg>
      );
    case "warning":
      return (
        <svg {...common}>
          <path d="M12 4.5 20 18.5H4z" />
          <path d="M12 9v4.5" />
          <path d="M12 16.5h.01" />
        </svg>
      );
    case "bolt":
      return (
        <svg {...common}>
          <path d="m13.5 3.5-7 9h4.5l-1 8 7-9H12z" />
        </svg>
      );
    case "timeline":
      return (
        <svg {...common}>
          <path d="M5.5 6.5h4" />
          <path d="M14.5 6.5h4" />
          <path d="M5.5 12h7" />
          <path d="M15.5 17.5h3" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="10" cy="6.5" r="1.4" />
          <circle cx="14" cy="17.5" r="1.4" />
        </svg>
      );
    case "edit_note":
      return (
        <svg {...common}>
          <path d="M4.5 19.5h6" />
          <path d="M12.5 6.5h7" />
          <path d="M12.5 10.5h7" />
          <path d="M12.5 14.5h5" />
          <path d="m4.5 16.5 6.8-6.8 2.5 2.5-6.8 6.8-3 .5z" />
        </svg>
      );
    case "account_balance":
      return (
        <svg {...common}>
          <path d="M4 9h16" />
          <path d="M6 9v7" />
          <path d="M10 9v7" />
          <path d="M14 9v7" />
          <path d="M18 9v7" />
          <path d="M3.5 19.5h17" />
          <path d="M12 4 4 7.5h16z" />
        </svg>
      );
    case "send":
      return (
        <svg {...common}>
          <path d="m4 19 16-7L4 5l2.7 7z" />
          <path d="M6.7 12H20" />
        </svg>
      );
    case "refresh":
      return (
        <svg {...common}>
          <path d="M20 6.5V11h-4.5" />
          <path d="M4 17.5V13h4.5" />
          <path d="M17.2 17A7 7 0 0 1 6.4 18.4L4 17.5" />
          <path d="M6.8 7A7 7 0 0 1 17.6 5.6L20 6.5" />
        </svg>
      );
    case "rocket_launch":
      return (
        <svg {...common}>
          <path d="M14.5 5.5c1.9-.5 3.7-.6 5-.5.1 1.3 0 3.1-.5 5l-4.5 4.5-4-4z" />
          <path d="m10 10-4.5 1.5L4 17l5.5-1.5" />
          <path d="m9.5 14.5-2 2" />
          <path d="m13 7.5 3.5 3.5" />
        </svg>
      );
    case "info":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 10.5v5" />
          <path d="M12 7.5h.01" />
        </svg>
      );
    case "more_vert":
      return (
        <svg viewBox="0 0 24 24" className={className} aria-hidden fill="currentColor">
          <circle cx="12" cy="5" r="1.8" />
          <circle cx="12" cy="12" r="1.8" />
          <circle cx="12" cy="19" r="1.8" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
  }
}
