"use client";

import type { ComponentScores } from "@/types";

interface ScoreBreakdownProps {
  scores: ComponentScores;
  showLabels?: boolean;
}

const SCORE_CONFIG: Record<
  keyof ComponentScores,
  { label: string; barColor: string }
> = {
  price: { label: "Price", barColor: "bg-emerald-500/70" },
  delivery: { label: "Delivery", barColor: "bg-zinc-500" },
  reliability: { label: "Reliability", barColor: "bg-zinc-500" },
  warranty: { label: "Warranty", barColor: "bg-zinc-500" },
  spec_match: { label: "Specs", barColor: "bg-zinc-500" },
};

export default function ScoreBreakdown({ scores, showLabels = true }: ScoreBreakdownProps) {
  return (
    <div className="space-y-2">
      {(Object.keys(SCORE_CONFIG) as Array<keyof typeof SCORE_CONFIG>).map((key) => {
        const config = SCORE_CONFIG[key];
        const score = scores[key];
        const percentage = Math.round(score * 100);

        return (
          <div key={key} className="flex items-center gap-2">
            {showLabels && (
              <span className="w-16 text-[10px] text-zinc-500">{config.label}</span>
            )}
            <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${config.barColor} rounded-full transition-all duration-300`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="w-8 text-[10px] text-zinc-500 text-right font-mono">
              {percentage}
            </span>
          </div>
        );
      })}
    </div>
  );
}
