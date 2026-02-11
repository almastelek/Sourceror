"use client";

import type { SensitivityResult, Stability } from "@/types";

interface SensitivityPanelProps {
  sensitivity: SensitivityResult;
}

const STABILITY_CONFIG: Record<
  Stability,
  { label: string; color: string; border: string }
> = {
  high: {
    label: "High stability",
    color: "text-zinc-300",
    border: "border-zinc-600/50",
  },
  medium: {
    label: "Medium stability",
    color: "text-emerald-400",
    border: "border-emerald-900/40",
  },
  low: {
    label: "Low stability",
    color: "text-red-400/90",
    border: "border-red-900/40",
  },
};

export default function SensitivityPanel({ sensitivity }: SensitivityPanelProps) {
  const { stability, switch_conditions, budget_relaxation } = sensitivity;
  const config = STABILITY_CONFIG[stability];

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden">
      <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-300">
          Decision stability
        </h3>
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-md border ${config.border} ${config.color}`}
        >
          {config.label}
        </span>
      </div>

      <div className="p-5 space-y-5">
        <p className="text-xs text-zinc-500 leading-relaxed">
          {stability === "high" &&
            "Your top pick stays #1 across preference changes."}
          {stability === "medium" &&
            "Top pick is fairly stable; it could change with bigger priority shifts."}
          {stability === "low" &&
            "Top pick is sensitive to preferences — review alternatives."}
        </p>

        {switch_conditions.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">
              If priorities change
            </h4>
            <div className="space-y-2">
              {switch_conditions.map((condition, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-zinc-800/40 border border-zinc-800 text-xs text-zinc-400"
                >
                  {condition.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {budget_relaxation.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">
              If budget increases
            </h4>
            <div className="space-y-2">
              {budget_relaxation.map((relaxation, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-zinc-800/40 border border-zinc-800 text-xs text-zinc-400"
                >
                  {relaxation.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {switch_conditions.length === 0 && budget_relaxation.length === 0 && (
          <div className="p-4 rounded-lg bg-zinc-800/40 border border-zinc-700/50">
            <p className="text-xs font-medium text-zinc-300">Very stable</p>
            <p className="text-xs text-zinc-500 mt-0.5">
              Top pick stays #1 across weight and budget variations.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
