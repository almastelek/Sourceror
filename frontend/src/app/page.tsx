"use client";

import { useState } from "react";
import InputForm from "@/components/InputForm";
import RecommendationCard from "@/components/RecommendationCard";
import SensitivityPanel from "@/components/SensitivityPanel";
import { getRecommendations } from "@/lib/api";
import type { RecommendationRequest, RecommendationResponse } from "@/types";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (request: RecommendationRequest) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await getRecommendations(request);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-radial from-cyan-500/5 to-transparent rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-radial from-blue-500/5 to-transparent rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-slate-800/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🎯</span>
                <div>
                  <h1 className="text-xl font-bold text-white">Agentic Buyer</h1>
                  <p className="text-xs text-slate-400">Electronics Decision Engine</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="px-2 py-1 rounded bg-slate-800">Headphones</span>
                <span className="text-slate-700">|</span>
                <span className="px-2 py-1 rounded bg-cyan-500/10 text-cyan-400">MVP</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid lg:grid-cols-[400px_1fr] gap-8">
            {/* Input Panel */}
            <aside className="lg:sticky lg:top-8 lg:self-start">
              <div className="rounded-2xl border border-slate-700/50 bg-slate-800/30 backdrop-blur-sm p-6">
                <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                  <span>⚙️</span>
                  <span>Configure Search</span>
                </h2>
                <InputForm onSubmit={handleSubmit} isLoading={isLoading} />
              </div>
            </aside>

            {/* Results Panel */}
            <section className="space-y-8">
              {/* Initial State */}
              {!isLoading && !response && !error && (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <span className="text-6xl mb-4">🎧</span>
                  <h2 className="text-2xl font-semibold text-white mb-2">
                    Find Your Perfect Headphones
                  </h2>
                  <p className="text-slate-400 max-w-md">
                    Configure your preferences on the left, then click &quot;Find Best Options&quot;
                    to get personalized recommendations from Best Buy and eBay.
                  </p>
                </div>
              )}

              {/* Loading State */}
              {isLoading && (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="relative mb-6">
                    <div className="w-16 h-16 border-4 border-slate-700 rounded-full" />
                    <div className="absolute inset-0 w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <h2 className="text-xl font-semibold text-white mb-2">
                    Analyzing Options...
                  </h2>
                  <p className="text-slate-400 text-sm">
                    Searching Best Buy and eBay, scoring products, running sensitivity analysis
                  </p>
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
                  <div className="flex items-start gap-4">
                    <span className="text-3xl">❌</span>
                    <div>
                      <h3 className="text-lg font-semibold text-red-400 mb-1">
                        Something went wrong
                      </h3>
                      <p className="text-sm text-slate-300">{error}</p>
                      <p className="text-sm text-slate-400 mt-2">
                        Make sure the backend is running at localhost:8000
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Results */}
              {response && (
                <>
                  {/* Debug Info */}
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <span>
                      📊 {response.debug.candidates_considered} products found
                    </span>
                    <span className="text-slate-600">•</span>
                    <span>
                      ✅ {response.debug.candidates_after_filter} match your criteria
                    </span>
                    <span className="text-slate-600">•</span>
                    <span>
                      🔌 Sources: {response.debug.sources_used.join(", ") || "None"}
                    </span>
                  </div>

                  {/* No Results */}
                  {response.top3.length === 0 && (
                    <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6">
                      <div className="flex items-start gap-4">
                        <span className="text-3xl">🔍</span>
                        <div>
                          <h3 className="text-lg font-semibold text-amber-400 mb-1">
                            No matching products found
                          </h3>
                          <p className="text-sm text-slate-300">
                            Try increasing your budget, broadening your search terms,
                            or allowing more conditions (refurbished/used).
                          </p>
                          {response.debug.errors.length > 0 && (
                            <div className="mt-3 text-xs text-slate-500">
                              API Notes: {response.debug.errors.join(", ")}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Top 3 Cards */}
                  {response.top3.length > 0 && (
                    <div>
                      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                        <span>🏆</span>
                        <span>Top Recommendations</span>
                      </h2>
                      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {response.top3.map((rec) => (
                          <RecommendationCard key={rec.listing.id} recommendation={rec} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sensitivity Analysis */}
                  {response.top3.length > 0 && (
                    <SensitivityPanel sensitivity={response.sensitivity} />
                  )}

                  {/* Shortlist */}
                  {response.ranked_shortlist.length > 3 && (
                    <div>
                      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <span>📋</span>
                        <span>Other Options</span>
                      </h2>
                      <div className="rounded-2xl border border-slate-700/50 bg-slate-800/30 overflow-hidden">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-700/50">
                              <th className="px-4 py-3 text-left text-slate-400 font-medium">Product</th>
                              <th className="px-4 py-3 text-left text-slate-400 font-medium">Source</th>
                              <th className="px-4 py-3 text-right text-slate-400 font-medium">Price</th>
                              <th className="px-4 py-3 text-right text-slate-400 font-medium">Score</th>
                            </tr>
                          </thead>
                          <tbody>
                            {response.ranked_shortlist.slice(3).map((item) => (
                              <tr
                                key={item.listing.id}
                                className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                              >
                                <td className="px-4 py-3 text-white">
                                  <a
                                    href={item.listing.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:text-cyan-400 transition-colors"
                                  >
                                    {item.listing.title.length > 60
                                      ? item.listing.title.slice(0, 60) + "..."
                                      : item.listing.title}
                                  </a>
                                </td>
                                <td className="px-4 py-3 text-slate-400 capitalize">
                                  {item.listing.source}
                                </td>
                                <td className="px-4 py-3 text-right text-white font-mono">
                                  ${item.listing.total_cost.toFixed(2)}
                                </td>
                                <td className="px-4 py-3 text-right text-cyan-400 font-mono">
                                  {Math.round(item.total_score * 100)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </section>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/50 mt-12">
          <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-slate-500">
            <p>
              Agentic Buyer — Deterministic decision engine for electronics purchases.
              Data from Best Buy and eBay APIs.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
