"use client";

import type { ComponentScores } from "@/types";

interface ScoreBreakdownProps {
    scores: ComponentScores;
    showLabels?: boolean;
}

const SCORE_CONFIG = {
    price: { label: "Price", color: "bg-emerald-500", icon: "" },
    delivery: { label: "Delivery", color: "bg-blue-500", icon: "" },
    reliability: { label: "Reliability", color: "bg-purple-500", icon: "" },
    warranty: { label: "Warranty", color: "bg-orange-500", icon: "" },
    spec_match: { label: "Specs", color: "bg-pink-500", icon: "" },
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
                            <span className="w-20 text-xs text-slate-400 flex items-center gap-1">
                                <span>{config.icon}</span>
                                <span>{config.label}</span>
                            </span>
                        )}
                        <div className="flex-1 h-2 bg-slate-700/50 rounded-full overflow-hidden">
                            <div
                                className={`h-full ${config.color} rounded-full transition-all duration-500`}
                                style={{ width: `${percentage}%` }}
                            />
                        </div>
                        <span className="w-10 text-xs text-slate-400 text-right font-mono">
                            {percentage}%
                        </span>
                    </div>
                );
            })}
        </div>
    );
}
