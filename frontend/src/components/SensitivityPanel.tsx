"use client";

import type { SensitivityResult, Stability } from "@/types";

interface SensitivityPanelProps {
    sensitivity: SensitivityResult;
}

const STABILITY_CONFIG: Record<Stability, { label: string; color: string; bg: string; icon: string }> = {
    high: {
        label: "High Stability",
        color: "text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/30",
        icon: "🔒",
    },
    medium: {
        label: "Medium Stability",
        color: "text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/30",
        icon: "⚖️",
    },
    low: {
        label: "Low Stability",
        color: "text-red-400",
        bg: "bg-red-500/10 border-red-500/30",
        icon: "⚠️",
    },
};

export default function SensitivityPanel({ sensitivity }: SensitivityPanelProps) {
    const { stability, switch_conditions, budget_relaxation } = sensitivity;
    const stabilityConfig = STABILITY_CONFIG[stability];

    return (
        <div className="rounded-2xl border border-slate-700/50 bg-slate-800/30 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Decision Stability Analysis</h3>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${stabilityConfig.bg}`}>
                    <span>{stabilityConfig.icon}</span>
                    <span className={`text-sm font-medium ${stabilityConfig.color}`}>
                        {stabilityConfig.label}
                    </span>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Explanation */}
                <p className="text-sm text-slate-400">
                    {stability === "high" && "Your top recommendation is robust — it stays #1 across various preference changes."}
                    {stability === "medium" && "Your top recommendation is fairly stable, but could change with moderate shifts in priorities."}
                    {stability === "low" && "Your top recommendation is sensitive to preference changes — consider the alternatives carefully."}
                </p>

                {/* Weight Switch Conditions */}
                {switch_conditions.length > 0 && (
                    <div className="space-y-3">
                        <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                            <span>🎚️</span>
                            <span>If Priorities Change</span>
                        </h4>
                        <div className="space-y-2">
                            {switch_conditions.map((condition, i) => (
                                <div
                                    key={i}
                                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-700/30 border border-slate-700/50"
                                >
                                    <span className="text-lg">
                                        {condition.factor > 1 ? "📈" : "📉"}
                                    </span>
                                    <p className="text-sm text-slate-300">{condition.message}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Budget Relaxation */}
                {budget_relaxation.length > 0 && (
                    <div className="space-y-3">
                        <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                            <span>💵</span>
                            <span>If Budget Increases</span>
                        </h4>
                        <div className="space-y-2">
                            {budget_relaxation.map((relaxation, i) => (
                                <div
                                    key={i}
                                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-700/30 border border-slate-700/50"
                                >
                                    <span className="text-lg">
                                        {relaxation.new_winner_id ? "🔄" : "✅"}
                                    </span>
                                    <p className="text-sm text-slate-300">{relaxation.message}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* No changes detected */}
                {switch_conditions.length === 0 && budget_relaxation.length === 0 && (
                    <div className="flex items-center gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                        <span className="text-2xl">✨</span>
                        <div>
                            <p className="text-sm font-medium text-emerald-400">Very Stable Decision</p>
                            <p className="text-sm text-slate-400">
                                Your top pick remains #1 across all tested variations in weights and budget.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
