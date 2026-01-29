// Types matching the backend Pydantic models

export type Source = "bestbuy" | "ebay";
export type Condition = "new" | "refurb" | "used";
export type RiskTolerance = "low" | "medium" | "high";
export type DeliveryPriority = "low" | "medium" | "high";
export type Stability = "high" | "medium" | "low";
export type RecommendationLabel = "overall" | "value" | "low_risk";

export interface WeightConfig {
    price: number;
    delivery: number;
    reliability: number;
    warranty: number;
    spec_match: number;
}

export interface RecommendationRequest {
    category: string;
    query: string;
    budget_max: number;
    condition_allowed: string[];
    delivery_priority: DeliveryPriority;
    risk_tolerance: RiskTolerance;
    weights: WeightConfig;
    user_location_zip?: string;
}

export interface NormalizedListing {
    id: string;
    source: Source;
    title: string;
    url: string;
    image_url: string | null;
    price: number;
    shipping_cost: number | null;
    total_cost: number;
    condition: Condition | null;
    eta_min_days: number | null;
    eta_max_days: number | null;
    return_window_days: number | null;
    seller_rating: number | null;
    seller_feedback_count: number | null;
    warranty_months: number | null;
    specs: Record<string, unknown>;
    raw: Record<string, unknown>;
}

export interface ComponentScores {
    price: number;
    delivery: number;
    reliability: number;
    warranty: number;
    spec_match: number;
}

export interface Recommendation {
    label: RecommendationLabel;
    listing: NormalizedListing;
    scores: ComponentScores;
    total_score: number;
    why: string[];
    tradeoff: string;
}

export interface ScoredListing {
    listing: NormalizedListing;
    scores: ComponentScores;
    total_score: number;
}

export interface WeightSwitchCondition {
    type: string;
    dimension: string;
    factor: number;
    new_winner_id: string;
    message: string;
}

export interface BudgetRelaxation {
    budget: number;
    new_winner_id: string | null;
    message: string;
}

export interface SensitivityResult {
    stability: Stability;
    switch_conditions: WeightSwitchCondition[];
    budget_relaxation: BudgetRelaxation[];
}

export interface DebugInfo {
    candidates_considered: number;
    candidates_after_filter: number;
    sources_used: string[];
    errors: string[];
}

export interface DecisionSpec {
    category: string;
    query: string;
    budget_max: number;
    condition_allowed: string[];
    delivery_priority: DeliveryPriority;
    risk_tolerance: RiskTolerance;
    weights: WeightConfig;
    user_location_zip?: string;
}

export interface RecommendationResponse {
    decision_spec: DecisionSpec;
    top3: Recommendation[];
    ranked_shortlist: ScoredListing[];
    sensitivity: SensitivityResult;
    debug: DebugInfo;
}

export interface CategoryInfo {
    id: string;
    name: string;
    description: string;
}
