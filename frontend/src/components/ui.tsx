import type { ReactNode } from "react";
import type { Objective } from "../types";

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

const OBJECTIVE_STYLES: Record<Objective, string> = {
  Discovery: "bg-sky-50 text-sky-700 ring-sky-200",
  Trust: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  Conversion: "bg-amber-50 text-amber-700 ring-amber-200",
};

export function ObjectiveBadge({ objective }: { objective: Objective }) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset",
        OBJECTIVE_STYLES[objective],
      )}
    >
      {objective}
    </span>
  );
}

export function Chip({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: "slate" | "indigo" | "rose";
}) {
  const tones: Record<string, string> = {
    slate: "bg-slate-100 text-slate-600",
    indigo: "bg-brand-50 text-brand-700",
    rose: "bg-rose-50 text-rose-600",
  };
  return (
    <span className={cx("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", tones[tone])}>
      {children}
    </span>
  );
}

export function ConfidenceChip({ score, maxScore }: { score: number; maxScore: number }) {
  // Confidence is relative to this week's top-ranked opportunity, so it stays
  // meaningful regardless of the absolute weight scale the user has set.
  const denom = maxScore > 0 ? maxScore : 1;
  const pct = Math.max(4, Math.min(99, Math.round((score / denom) * 99)));
  const tone =
    pct >= 78 ? "bg-emerald-500" : pct >= 55 ? "bg-brand-500" : "bg-slate-400";
  return (
    <div className="flex shrink-0 items-center gap-2">
      <div className="h-1.5 w-14 overflow-hidden rounded-full bg-slate-200">
        <div className={cx("h-full rounded-full", tone)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-500">{pct}% fit</span>
    </div>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  className,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost" | "soft";
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit";
}) {
  const variants: Record<string, string> = {
    primary:
      "bg-brand-600 text-white hover:bg-brand-700 shadow-sm disabled:opacity-50",
    ghost: "text-slate-600 hover:bg-slate-100",
    soft: "bg-brand-50 text-brand-700 hover:bg-brand-100",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cx(
        "inline-flex items-center justify-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed",
        variants[variant],
        className,
      )}
    >
      {children}
    </button>
  );
}

export function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
  );
}

export function platformLabel(p: string): string {
  return p === "tiktok" ? "TikTok" : "Instagram";
}
