"""
Pydantic models for Agentic Buyer decision engine.
"""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class Condition(str, Enum):
    """Product condition types."""
    NEW = "new"
    REFURBISHED = "refurb"
    USED = "used"


class Source(str, Enum):
    """Data source identifiers."""
    BESTBUY = "bestbuy"
    EBAY = "ebay"


class RiskTolerance(str, Enum):
    """User risk tolerance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DeliveryPriority(str, Enum):
    """User delivery priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Stability(str, Enum):
    """Decision stability classification."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationLabel(str, Enum):
    """Labels for top-3 recommendations."""
    OVERALL = "overall"
    VALUE = "value"
    LOW_RISK = "low_risk"


# ============================================================================
# Request Models
# ============================================================================

class WeightConfig(BaseModel):
    """Weight configuration for scoring dimensions."""
    price: float = Field(default=0.25, ge=0, le=1)
    delivery: float = Field(default=0.20, ge=0, le=1)
    reliability: float = Field(default=0.25, ge=0, le=1)
    warranty: float = Field(default=0.15, ge=0, le=1)
    spec_match: float = Field(default=0.15, ge=0, le=1)
    
    def normalized(self) -> "WeightConfig":
        """Return a copy with weights normalized to sum to 1."""
        total = self.price + self.delivery + self.reliability + self.warranty + self.spec_match
        if total == 0:
            # Default equal weights if all zero
            return WeightConfig(
                price=0.2, delivery=0.2, reliability=0.2, warranty=0.2, spec_match=0.2
            )
        return WeightConfig(
            price=self.price / total,
            delivery=self.delivery / total,
            reliability=self.reliability / total,
            warranty=self.warranty / total,
            spec_match=self.spec_match / total,
        )


class HardConstraints(BaseModel):
    """Hard constraints that filter out candidates."""
    budget_max: float = Field(..., gt=0, description="Maximum budget in USD")
    condition_allowed: set[Condition] = Field(
        default={Condition.NEW, Condition.REFURBISHED},
        description="Allowed product conditions"
    )
    max_delivery_days: int | None = Field(
        default=None, ge=1, description="Maximum acceptable delivery days"
    )


class DecisionSpec(BaseModel):
    """
    Complete specification of user's decision criteria.
    This is the input to the recommendation engine.
    """
    category: str = Field(..., description="Product category (e.g., 'headphones')")
    query: str = Field(..., min_length=1, description="Search query text")
    budget_max: float = Field(..., gt=0, description="Maximum budget in USD")
    condition_allowed: list[str] = Field(
        default=["new", "refurb"],
        description="Allowed conditions"
    )
    delivery_priority: DeliveryPriority = Field(
        default=DeliveryPriority.MEDIUM,
        description="How important fast delivery is"
    )
    risk_tolerance: RiskTolerance = Field(
        default=RiskTolerance.MEDIUM,
        description="Tolerance for uncertainty/unknowns"
    )
    weights: WeightConfig = Field(
        default_factory=WeightConfig,
        description="Importance weights for each scoring dimension"
    )
    user_location_zip: str | None = Field(
        default=None,
        description="User ZIP code for shipping estimates"
    )
    
    @field_validator("condition_allowed", mode="before")
    @classmethod
    def parse_conditions(cls, v: Any) -> list[str]:
        """Convert condition strings to list."""
        if isinstance(v, set):
            return list(v)
        return v
    
    def get_hard_constraints(self) -> HardConstraints:
        """Extract hard constraints from spec."""
        conditions = {Condition(c) for c in self.condition_allowed}
        return HardConstraints(
            budget_max=self.budget_max,
            condition_allowed=conditions,
            max_delivery_days=None  # Could be derived from delivery_priority
        )


# ============================================================================
# Listing Models
# ============================================================================

class NormalizedListing(BaseModel):
    """
    Unified listing schema across all data sources.
    All fields normalized to common format for scoring.
    """
    id: str = Field(..., description="Source-specific unique ID")
    source: Source = Field(..., description="Data source")
    title: str = Field(..., description="Product title")
    url: str = Field(..., description="Product URL")
    image_url: str | None = Field(default=None, description="Product image URL")
    
    # Pricing
    price: float = Field(..., ge=0, description="Item price in USD")
    shipping_cost: float | None = Field(default=None, ge=0, description="Shipping cost")
    total_cost: float = Field(..., ge=0, description="Price + shipping")
    
    # Condition & Delivery
    condition: Condition | None = Field(default=None, description="Product condition")
    eta_min_days: int | None = Field(default=None, ge=0, description="Minimum ETA days")
    eta_max_days: int | None = Field(default=None, ge=0, description="Maximum ETA days")
    
    # Seller & Returns
    return_window_days: int | None = Field(default=None, ge=0, description="Return window")
    seller_rating: float | None = Field(default=None, ge=0, le=100, description="Seller rating %")
    seller_feedback_count: int | None = Field(default=None, ge=0, description="Feedback count")
    
    # Warranty
    warranty_months: int | None = Field(default=None, ge=0, description="Warranty in months")
    
    # Category-specific specs
    specs: dict[str, Any] = Field(default_factory=dict, description="Product specifications")
    
    # Debug
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw API response snippet")


class ComponentScores(BaseModel):
    """Individual dimension scores for a listing."""
    price: float = Field(..., ge=0, le=1, description="Price score (higher = cheaper)")
    delivery: float = Field(..., ge=0, le=1, description="Delivery score (higher = faster)")
    reliability: float = Field(..., ge=0, le=1, description="Reliability score")
    warranty: float = Field(..., ge=0, le=1, description="Warranty score")
    spec_match: float = Field(..., ge=0, le=1, description="Spec match score")


class ScoredListing(BaseModel):
    """A listing with computed scores."""
    listing: NormalizedListing
    scores: ComponentScores
    total_score: float = Field(..., ge=0, le=1, description="Weighted total score")


# ============================================================================
# Recommendation Models
# ============================================================================

class Recommendation(BaseModel):
    """A recommended listing with explanation."""
    label: RecommendationLabel
    listing: NormalizedListing
    scores: ComponentScores
    total_score: float
    why: list[str] = Field(..., description="2-3 reasons for this pick")
    tradeoff: str = Field(..., description="Main tradeoff of this pick")


class WeightSwitchCondition(BaseModel):
    """Describes when changing a weight would switch the winner."""
    type: str = "weight"
    dimension: str
    factor: float
    new_winner_id: str
    message: str


class BudgetRelaxation(BaseModel):
    """Describes what happens if budget is relaxed."""
    budget: float
    new_winner_id: str | None
    message: str


class SensitivityResult(BaseModel):
    """Results of sensitivity analysis."""
    stability: Stability
    switch_conditions: list[WeightSwitchCondition] = Field(default_factory=list)
    budget_relaxation: list[BudgetRelaxation] = Field(default_factory=list)


class DebugInfo(BaseModel):
    """Debug information for the response."""
    candidates_considered: int
    candidates_after_filter: int
    sources_used: list[str]
    errors: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """Complete API response for recommendations."""
    decision_spec: DecisionSpec
    top3: list[Recommendation]
    ranked_shortlist: list[ScoredListing] = Field(
        default_factory=list,
        description="Top 10 candidates with scores"
    )
    sensitivity: SensitivityResult
    debug: DebugInfo
