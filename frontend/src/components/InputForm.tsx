"use client";

import { useState } from "react";
import type { RecommendationRequest, WeightConfig, DeliveryPriority, RiskTolerance } from "@/types";

interface InputFormProps {
    onSubmit: (request: RecommendationRequest) => void;
    isLoading: boolean;
}

const DEFAULT_WEIGHTS: WeightConfig = {
    price: 0.25,
    delivery: 0.20,
    reliability: 0.25,
    warranty: 0.15,
    spec_match: 0.15,
};

const WEIGHT_LABELS: Record<keyof WeightConfig, string> = {
    price: "Price",
    delivery: "Delivery Speed",
    reliability: "Seller Reliability",
    warranty: "Warranty/Durability",
    spec_match: "Spec Match",
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

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {/* Query Input */}
            <div>
                <label htmlFor="query" className="block text-sm font-medium text-slate-300 mb-2">
                    What are you looking for?
                </label>
                <input
                    type="text"
                    id="query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl 
                     text-white placeholder-slate-500 focus:outline-none focus:ring-2 
                     focus:ring-cyan-500 focus:border-transparent transition-all"
                    placeholder="e.g., noise cancelling wireless headphones"
                    required
                />
            </div>

            {/* Budget Slider */}
            <div>
                <label htmlFor="budget" className="block text-sm font-medium text-slate-300 mb-2">
                    Maximum Budget: <span className="text-cyan-400 font-bold">${budgetMax}</span>
                </label>
                <input
                    type="range"
                    id="budget"
                    min="50"
                    max="1000"
                    step="25"
                    value={budgetMax}
                    onChange={(e) => setBudgetMax(Number(e.target.value))}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer
                     accent-cyan-500"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>$50</span>
                    <span>$500</span>
                    <span>$1000</span>
                </div>
            </div>

            {/* Condition Checkboxes */}
            <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                    Acceptable Conditions
                </label>
                <div className="flex gap-4">
                    {[
                        { key: "new", label: "New" },
                        { key: "refurb", label: "Refurbished" },
                        { key: "used", label: "Used" },
                    ].map(({ key, label }) => (
                        <label
                            key={key}
                            className="flex items-center gap-2 cursor-pointer group"
                        >
                            <input
                                type="checkbox"
                                checked={conditions[key as keyof typeof conditions]}
                                onChange={() => handleConditionChange(key as keyof typeof conditions)}
                                className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-cyan-500 
                           focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
                            />
                            <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
                                {label}
                            </span>
                        </label>
                    ))}
                </div>
            </div>

            {/* Priority Dropdowns */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label htmlFor="delivery" className="block text-sm font-medium text-slate-300 mb-2">
                        Delivery Priority
                    </label>
                    <select
                        id="delivery"
                        value={deliveryPriority}
                        onChange={(e) => setDeliveryPriority(e.target.value as DeliveryPriority)}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl 
                       text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 
                       focus:border-transparent cursor-pointer"
                    >
                        <option value="low">Low - I can wait</option>
                        <option value="medium">Medium - Within a week</option>
                        <option value="high">High - ASAP</option>
                    </select>
                </div>
                <div>
                    <label htmlFor="risk" className="block text-sm font-medium text-slate-300 mb-2">
                        Risk Tolerance
                    </label>
                    <select
                        id="risk"
                        value={riskTolerance}
                        onChange={(e) => setRiskTolerance(e.target.value as RiskTolerance)}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl 
                       text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 
                       focus:border-transparent cursor-pointer"
                    >
                        <option value="low">Low - Play it safe</option>
                        <option value="medium">Medium - Balanced</option>
                        <option value="high">High - I&apos;ll take chances</option>
                    </select>
                </div>
            </div>

            {/* Weight Sliders */}
            <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                    Importance Weights
                </label>
                <div className="space-y-4 bg-slate-800/30 rounded-xl p-4 border border-slate-700/50">
                    {(Object.keys(weights) as Array<keyof WeightConfig>).map((key) => (
                        <div key={key} className="flex items-center gap-4">
                            <span className="w-32 text-sm text-slate-400">{WEIGHT_LABELS[key]}</span>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.05"
                                value={weights[key]}
                                onChange={(e) => handleWeightChange(key, Number(e.target.value))}
                                className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer
                           accent-cyan-500"
                            />
                            <span className="w-12 text-sm text-cyan-400 font-mono text-right">
                                {(weights[key] * 100).toFixed(0)}%
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Submit Button */}
            <button
                type="submit"
                disabled={isLoading}
                className="w-full py-4 px-6 bg-gradient-to-r from-cyan-500 to-blue-600 
                   hover:from-cyan-400 hover:to-blue-500 disabled:from-slate-600 
                   disabled:to-slate-700 text-white font-semibold rounded-xl 
                   transition-all duration-300 transform hover:scale-[1.02] 
                   disabled:scale-100 disabled:cursor-not-allowed shadow-lg 
                   shadow-cyan-500/25 hover:shadow-cyan-500/40 disabled:shadow-none"
            >
                {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Finding best options...
                    </span>
                ) : (
                    "Find Best Options"
                )}
            </button>
        </form>
    );
}
