"use client";

import type { Recommendation, RecommendationLabel } from "@/types";
import ScoreBreakdown from "./ScoreBreakdown";
import Image from "next/image";

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const LABEL_CONFIG: Record<
  RecommendationLabel,
  { title: string; color: string; borderColor: string }
> = {
  overall: {
    title: "Best overall",
    color: "text-amber-400/90",
    borderColor: "border-amber-500/20",
  },
  value: {
    title: "Best value",
    color: "text-zinc-300",
    borderColor: "border-zinc-600/50",
  },
  low_risk: {
    title: "Lowest risk",
    color: "text-zinc-400",
    borderColor: "border-zinc-600/50",
  },
};

const SOURCE_CONFIG = {
  bestbuy: { name: "Best Buy", pill: "bg-zinc-700/50 text-zinc-400" },
  ebay: { name: "eBay", pill: "bg-zinc-700/50 text-zinc-400" },
};

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const { label, listing, scores, total_score, why, tradeoff } = recommendation;
  const labelConfig = LABEL_CONFIG[label];
  const sourceConfig = SOURCE_CONFIG[listing.source];

  return (
    <div
      className={`rounded-xl border ${labelConfig.borderColor} bg-zinc-900/60 overflow-hidden hover:border-zinc-600/50 transition-colors`}
    >
      <div className="flex items-start justify-between gap-3 px-4 pt-4 pb-2">
        <span
          className={`text-xs font-medium ${labelConfig.color}`}
        >
          {labelConfig.title}
        </span>
        <div className="text-right">
          <span className="text-lg font-semibold text-zinc-100 tabular-nums">
            {Math.round(total_score * 100)}
          </span>
          <span className="text-xs text-zinc-500">/100</span>
        </div>
      </div>

      <div className="h-40 bg-zinc-800/40 flex items-center justify-center overflow-hidden">
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
          <div className="w-12 h-12 rounded-full bg-zinc-700/50" aria-hidden />
        )}
      </div>

      <div className="p-4 space-y-4">
        <div>
          <span
            className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide ${sourceConfig.pill} mb-2`}
          >
            {sourceConfig.name}
          </span>
          <h3 className="text-sm font-medium text-zinc-200 line-clamp-2 leading-snug">
            {listing.title}
          </h3>
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-xl font-semibold text-zinc-100 tabular-nums">
            ${listing.total_cost.toFixed(2)}
          </span>
          {listing.shipping_cost !== null && listing.shipping_cost > 0 && (
            <span className="text-xs text-zinc-500">
              + ${listing.shipping_cost.toFixed(2)} ship
            </span>
          )}
          {listing.shipping_cost === 0 && (
            <span className="text-xs text-zinc-500">Free shipping</span>
          )}
        </div>

        <div className="flex flex-wrap gap-2 text-xs text-zinc-500">
          {listing.condition && (
            <span className="px-2 py-0.5 rounded bg-zinc-800 capitalize">
              {listing.condition}
            </span>
          )}
          {listing.eta_max_days != null && (
            <span className="px-2 py-0.5 rounded bg-zinc-800">
              {listing.eta_min_days ?? listing.eta_max_days}–{listing.eta_max_days} days
            </span>
          )}
          {listing.seller_rating != null && (
            <span className="px-2 py-0.5 rounded bg-zinc-800">
              {listing.seller_rating.toFixed(0)}% seller
            </span>
          )}
          {listing.warranty_months != null && (
            <span className="px-2 py-0.5 rounded bg-zinc-800">
              {listing.warranty_months}mo warranty
            </span>
          )}
          {listing.return_window_days != null && (
            <span className="px-2 py-0.5 rounded bg-zinc-800">
              {listing.return_window_days}d returns
            </span>
          )}
        </div>

        <div className="pt-3 border-t border-zinc-800">
          <ScoreBreakdown scores={scores} />
        </div>

        <div className="space-y-1.5">
          <h4 className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">
            Why this pick
          </h4>
          <ul className="space-y-1">
            {why.map((reason, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-zinc-400">
                <span className="text-amber-500/80 mt-0.5 shrink-0">·</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-900/30">
          <p className="text-xs text-amber-200/80">{tradeoff}</p>
        </div>

        <a
          href={listing.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-2 text-center text-xs font-medium text-zinc-200 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
        >
          View on {sourceConfig.name}
        </a>
      </div>
    </div>
  );
}
