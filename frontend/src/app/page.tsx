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
    <div className="min-h-screen bg-zinc-950">
      <div className="relative z-10">
        <header className="border-b border-zinc-800/80">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
                  Sourceror
                </h1>
                <p className="text-xs text-zinc-500 mt-0.5">
                  No more digging through listings — we surface the best options.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <span className="px-2 py-1 rounded-md bg-zinc-800/80 text-zinc-400">
                  Headphones
                </span>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid lg:grid-cols-[380px_1fr] gap-8">
            <aside className="lg:sticky lg:top-8 lg:self-start">
              <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-6">
                <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-6">
                  Configure search
                </h2>
                <InputForm onSubmit={handleSubmit} isLoading={isLoading} />
              </div>
            </aside>

            <section className="space-y-8">
              {!isLoading && !response && !error && (
                <div className="flex flex-col items-center justify-center py-24 text-center max-w-md mx-auto">
                  <h2 className="text-xl font-semibold text-zinc-200 mb-2">
                    Get ranked recommendations
                  </h2>
                  <p className="text-sm text-zinc-500 leading-relaxed">
                    Set your preferences and budget. We pull from Best Buy and eBay,
                    score every match, and show you the top picks — no scrolling required.
                  </p>
                </div>
              )}

              {isLoading && (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <div className="relative mb-6">
                    <div className="w-10 h-10 border-2 border-zinc-700 rounded-full" />
                    <div className="absolute inset-0 w-10 h-10 border-2 border-amber-500/80 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <h2 className="text-sm font-medium text-zinc-400">
                    Analyzing options
                  </h2>
                  <p className="text-xs text-zinc-600 mt-1">
                    Fetching, scoring, and running sensitivity analysis
                  </p>
                </div>
              )}

              {error && (
                <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6">
                  <h3 className="text-sm font-medium text-red-400 mb-1">
                    Something went wrong
                  </h3>
                  <p className="text-sm text-zinc-400">{error}</p>
                  <p className="text-xs text-zinc-500 mt-2">
                    Ensure the backend is running at localhost:8000
                  </p>
                </div>
              )}

              {response && (
                <>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-500">
                    <span>{response.debug.candidates_considered} products found</span>
                    <span className="text-zinc-700">·</span>
                    <span>{response.debug.candidates_after_filter} match criteria</span>
                    <span className="text-zinc-700">·</span>
                    <span>Sources: {response.debug.sources_used.join(", ") || "—"}</span>
                  </div>

                  {response.top3.length === 0 && (
                    <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-6">
                      <h3 className="text-sm font-medium text-amber-200/90 mb-1">
                        No matching products
                      </h3>
                      <p className="text-sm text-zinc-400">
                        Try a higher budget, broader search terms, or allow refurbished/used.
                      </p>
                      {response.debug.errors.length > 0 && (
                        <p className="mt-3 text-xs text-zinc-500">
                          API: {response.debug.errors.join(", ")}
                        </p>
                      )}
                    </div>
                  )}

                  {response.top3.length > 0 && (
                    <div>
                      <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4">
                        Top recommendations
                      </h2>
                      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {response.top3.map((rec) => (
                          <RecommendationCard key={rec.listing.id} recommendation={rec} />
                        ))}
                      </div>
                    </div>
                  )}

                  {response.top3.length > 0 && (
                    <SensitivityPanel sensitivity={response.sensitivity} />
                  )}

                  {response.ranked_shortlist.length > 3 && (
                    <div>
                      <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4">
                        Rest of shortlist
                      </h2>
                      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-zinc-800">
                              <th className="px-4 py-3 text-left text-zinc-500 font-medium">Product</th>
                              <th className="px-4 py-3 text-left text-zinc-500 font-medium">Source</th>
                              <th className="px-4 py-3 text-right text-zinc-500 font-medium">Price</th>
                              <th className="px-4 py-3 text-right text-zinc-500 font-medium">Score</th>
                            </tr>
                          </thead>
                          <tbody>
                            {response.ranked_shortlist.slice(3).map((item) => (
                              <tr
                                key={item.listing.id}
                                className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors"
                              >
                                <td className="px-4 py-3 text-zinc-200">
                                  <a
                                    href={item.listing.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:text-amber-400/90 transition-colors"
                                  >
                                    {item.listing.title.length > 60
                                      ? item.listing.title.slice(0, 60) + "…"
                                      : item.listing.title}
                                  </a>
                                </td>
                                <td className="px-4 py-3 text-zinc-500 capitalize">
                                  {item.listing.source}
                                </td>
                                <td className="px-4 py-3 text-right text-zinc-200 font-mono">
                                  ${item.listing.total_cost.toFixed(2)}
                                </td>
                                <td className="px-4 py-3 text-right text-amber-400/90 font-mono">
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

        <footer className="border-t border-zinc-800/80 mt-12">
          <div className="max-w-7xl mx-auto px-6 py-6 text-center text-xs text-zinc-600">
            Sourceror — Deterministic decision engine. Data from Best Buy and eBay.
          </div>
        </footer>
      </div>
    </div>
  );
}
