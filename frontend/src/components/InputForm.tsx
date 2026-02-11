"use client";

import { useState } from "react";
import type { RecommendationRequest, WeightConfig, DeliveryPriority, RiskTolerance } from "@/types";

interface InputFormProps {
  onSubmit: (request: RecommendationRequest) => void;
  isLoading: boolean;
}

const DEFAULT_WEIGHTS: WeightConfig = {
  price: 0.25,
  delivery: 0.2,
  reliability: 0.25,
  warranty: 0.15,
  spec_match: 0.15,
};

const WEIGHT_LABELS: Record<keyof WeightConfig, string> = {
  price: "Price",
  delivery: "Delivery speed",
  reliability: "Seller reliability",
  warranty: "Warranty / durability",
  spec_match: "Spec match",
};

export default function InputForm({ onSubmit, isLoading }: InputFormProps) {
  const [query, setQuery] = useState("noise cancelling wireless headphones");
  const [budgetMax, setBudgetMax] = useState(250);
  const [conditions, setConditions] = useState({
    new: true,
    refurb: true,
    used: false,
  });
  const [deliveryPriority, setDeliveryPriority] = useState<DeliveryPriority>("medium");
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance>("low");
  const [weights, setWeights] = useState<WeightConfig>(DEFAULT_WEIGHTS);

  const handleConditionChange = (condition: keyof typeof conditions) => {
    setConditions((prev) => ({ ...prev, [condition]: !prev[condition] }));
  };

  const handleWeightChange = (key: keyof WeightConfig, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const conditionAllowed: string[] = [];
    if (conditions.new) conditionAllowed.push("new");
    if (conditions.refurb) conditionAllowed.push("refurb");
    if (conditions.used) conditionAllowed.push("used");
    onSubmit({
      category: "headphones",
      query,
      budget_max: budgetMax,
      condition_allowed: conditionAllowed,
      delivery_priority: deliveryPriority,
      risk_tolerance: riskTolerance,
      weights,
    });
  };

  const inputClass =
    "w-full px-3 py-2.5 bg-zinc-800/50 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-colors";
  const labelClass = "block text-xs font-medium text-zinc-500 mb-1.5";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="query" className={labelClass}>
          Search
        </label>
        <input
          type="text"
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className={inputClass}
          placeholder="e.g. noise cancelling wireless headphones"
          required
        />
      </div>

      <div>
        <label htmlFor="budget" className={labelClass}>
          Max budget <span className="text-emerald-400 font-mono">${budgetMax}</span>
        </label>
        <input
          type="range"
          id="budget"
          min="50"
          max="1000"
          step="25"
          value={budgetMax}
          onChange={(e) => setBudgetMax(Number(e.target.value))}
          className="w-full h-1.5 bg-zinc-700 rounded-full appearance-none cursor-pointer accent-emerald-500"
        />
        <div className="flex justify-between text-[10px] text-zinc-600 mt-1">
          <span>$50</span>
          <span>$1000</span>
        </div>
      </div>

      <div>
        <label className={labelClass}>Condition</label>
        <div className="flex gap-4">
          {[
            { key: "new", label: "New" },
            { key: "refurb", label: "Refurbished" },
            { key: "used", label: "Used" },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={conditions[key as keyof typeof conditions]}
                onChange={() => handleConditionChange(key as keyof typeof conditions)}
                className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/50 focus:ring-offset-0 cursor-pointer"
              />
              <span className="text-xs text-zinc-400">{label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="delivery" className={labelClass}>
            Delivery
          </label>
          <select
            id="delivery"
            value={deliveryPriority}
            onChange={(e) => setDeliveryPriority(e.target.value as DeliveryPriority)}
            className={inputClass + " cursor-pointer"}
          >
            <option value="low">Low — I can wait</option>
            <option value="medium">Medium — Within a week</option>
            <option value="high">High — ASAP</option>
          </select>
        </div>
        <div>
          <label htmlFor="risk" className={labelClass}>
            Risk tolerance
          </label>
          <select
            id="risk"
            value={riskTolerance}
            onChange={(e) => setRiskTolerance(e.target.value as RiskTolerance)}
            className={inputClass + " cursor-pointer"}
          >
            <option value="low">Low — Play it safe</option>
            <option value="medium">Medium — Balanced</option>
            <option value="high">High — Take chances</option>
          </select>
        </div>
      </div>

      <div>
        <label className={labelClass}>Importance weights</label>
        <div className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-800/30 p-3">
          {(Object.keys(weights) as Array<keyof WeightConfig>).map((key) => (
            <div key={key} className="flex items-center gap-3">
              <span className="w-28 text-xs text-zinc-500">{WEIGHT_LABELS[key]}</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights[key]}
                onChange={(e) => handleWeightChange(key, Number(e.target.value))}
                className="flex-1 h-1.5 bg-zinc-700 rounded-full appearance-none cursor-pointer accent-emerald-500"
              />
              <span className="w-8 text-xs text-zinc-500 font-mono text-right">
                {(weights[key] * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-400 disabled:bg-zinc-700 disabled:text-zinc-500 text-zinc-950 text-sm font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Analyzing…
          </span>
        ) : (
          "Find best options"
        )}
      </button>
    </form>
  );
}
