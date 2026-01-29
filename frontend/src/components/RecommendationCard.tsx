"use client";

import type { Recommendation, RecommendationLabel } from "@/types";
import ScoreBreakdown from "./ScoreBreakdown";
import Image from "next/image";

interface RecommendationCardProps {
    recommendation: Recommendation;
}

const LABEL_CONFIG: Record<RecommendationLabel, { title: string; color: string; gradient: string; icon: string }> = {
    overall: {
        title: "Best Overall",
        color: "text-cyan-400",
        gradient: "from-cyan-500/20 to-blue-500/20",
        icon: "🏆",
    },
    value: {
        title: "Best Value",
        color: "text-emerald-400",
        gradient: "from-emerald-500/20 to-green-500/20",
        icon: "💎",
    },
    low_risk: {
        title: "Lowest Risk",
        color: "text-purple-400",
        gradient: "from-purple-500/20 to-pink-500/20",
        icon: "🛡️",
    },
};

const SOURCE_CONFIG = {
    bestbuy: { name: "Best Buy", color: "text-yellow-400", bg: "bg-yellow-500/10" },
    ebay: { name: "eBay", color: "text-blue-400", bg: "bg-blue-500/10" },
};

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
    const { label, listing, scores, total_score, why, tradeoff } = recommendation;
    const labelConfig = LABEL_CONFIG[label];
    const sourceConfig = SOURCE_CONFIG[listing.source];

    return (
        <div
            className={`relative rounded-2xl border border-slate-700/50 bg-gradient-to-br ${labelConfig.gradient} 
                  backdrop-blur-sm overflow-hidden hover:border-slate-600 transition-all duration-300
                  hover:shadow-lg hover:shadow-slate-900/50`}
        >
            {/* Label Badge */}
            <div className="absolute top-4 left-4 z-10">
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-sm`}>
                    <span>{labelConfig.icon}</span>
                    <span className={`text-sm font-semibold ${labelConfig.color}`}>{labelConfig.title}</span>
                </div>
            </div>

            {/* Total Score Badge */}
            <div className="absolute top-4 right-4 z-10">
                <div className="px-3 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-sm">
                    <span className="text-lg font-bold text-white">{Math.round(total_score * 100)}</span>
                    <span className="text-xs text-slate-400">/100</span>
                </div>
            </div>

            {/* Product Image */}
            <div className="h-48 bg-slate-800/50 flex items-center justify-center overflow-hidden">
                {listing.image_url ? (
                    <Image
                        src={listing.image_url}
                        alt={listing.title}
                        width={200}
                        height={200}
                        className="max-h-full w-auto object-contain"
                        unoptimized
                    />
                ) : (
                    <div className="text-6xl opacity-30">🎧</div>
                )}
            </div>

            {/* Content */}
            <div className="p-5 space-y-4">
                {/* Title & Source */}
                <div>
                    <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${sourceConfig.bg} ${sourceConfig.color} mb-2`}>
                        {sourceConfig.name}
                    </div>
                    <h3 className="text-lg font-semibold text-white line-clamp-2 leading-snug">
                        {listing.title}
                    </h3>
                </div>

                {/* Price & Shipping */}
                <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-white">${listing.total_cost.toFixed(2)}</span>
                    {listing.shipping_cost !== null && listing.shipping_cost > 0 && (
                        <span className="text-sm text-slate-400">
                            (${listing.price.toFixed(2)} + ${listing.shipping_cost.toFixed(2)} shipping)
                        </span>
                    )}
                    {listing.shipping_cost === 0 && (
                        <span className="text-sm text-emerald-400">Free shipping</span>
                    )}
                </div>

                {/* Details Row */}
                <div className="flex flex-wrap gap-3 text-sm">
                    {listing.condition && (
                        <span className="px-2 py-1 rounded bg-slate-700/50 text-slate-300 capitalize">
                            {listing.condition}
                        </span>
                    )}
                    {listing.eta_max_days && (
                        <span className="px-2 py-1 rounded bg-slate-700/50 text-slate-300">
                            📦 {listing.eta_min_days || listing.eta_max_days}-{listing.eta_max_days} days
                        </span>
                    )}
                    {listing.seller_rating && (
                        <span className="px-2 py-1 rounded bg-slate-700/50 text-slate-300">
                            ⭐ {listing.seller_rating.toFixed(1)}%
                        </span>
                    )}
                    {listing.warranty_months && (
                        <span className="px-2 py-1 rounded bg-slate-700/50 text-slate-300">
                            🛡️ {listing.warranty_months}mo warranty
                        </span>
                    )}
                    {listing.return_window_days && (
                        <span className="px-2 py-1 rounded bg-slate-700/50 text-slate-300">
                            ↩️ {listing.return_window_days}d returns
                        </span>
                    )}
                </div>

                {/* Score Breakdown */}
                <div className="pt-2 border-t border-slate-700/50">
                    <ScoreBreakdown scores={scores} />
                </div>

                {/* Why This Pick */}
                <div className="space-y-2">
                    <h4 className="text-sm font-medium text-slate-300">Why this pick:</h4>
                    <ul className="space-y-1">
                        {why.map((reason, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                                <span className="text-emerald-400">✓</span>
                                <span>{reason}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Tradeoff */}
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-start gap-2 text-sm">
                        <span className="text-amber-400">⚠️</span>
                        <span className="text-amber-200">{tradeoff}</span>
                    </div>
                </div>

                {/* View Link */}
                <a
                    href={listing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full py-2.5 text-center text-sm font-medium text-white 
                     bg-slate-700/50 hover:bg-slate-600/50 rounded-lg transition-colors"
                >
                    View on {sourceConfig.name} →
                </a>
            </div>
        </div>
    );
}
