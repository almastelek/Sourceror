// API client for Agentic Buyer backend

import type { RecommendationRequest, RecommendationResponse, CategoryInfo } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getRecommendations(
    request: RecommendationRequest
): Promise<RecommendationResponse> {
    const response = await fetch(`${API_BASE}/api/recommendations`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

export async function getCategories(): Promise<CategoryInfo[]> {
    const response = await fetch(`${API_BASE}/api/categories`);

    if (!response.ok) {
        throw new Error(`Failed to fetch categories: ${response.status}`);
    }

    const data = await response.json();
    return data.categories;
}

export async function healthCheck(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        return response.ok;
    } catch {
        return false;
    }
}
