"""
Deterministic scoring engine for product listings.
"""
from typing import Any
from ..models import (
    NormalizedListing, 
    ScoredListing,
    ComponentScores,
    DecisionSpec,
    Condition,
    RiskTolerance,
    Source,
    WeightConfig,
)


class ScoringEngine:
    """
    Deterministic scoring engine for ranking product listings.
    
    All scoring logic is transparent and reproducible given the same inputs.
    """
    
    # Penalties for unknown/missing values based on risk tolerance
    UNKNOWN_PENALTIES = {
        RiskTolerance.LOW: 0.3,     # Heavy penalty for unknowns
        RiskTolerance.MEDIUM: 0.15,  # Moderate penalty
        RiskTolerance.HIGH: 0.05,    # Light penalty - willing to take risks
    }
    
    # Baseline reliability scores by source
    SOURCE_RELIABILITY_BASELINE = {
        Source.BESTBUY: 0.85,  # Large retailer, high trust
        Source.EBAY: 0.50,     # Varies by seller, start lower
    }
    
    def __init__(self, spec: DecisionSpec):
        self.spec = spec
        self.unknown_penalty = self.UNKNOWN_PENALTIES[spec.risk_tolerance]
    
    def passes_constraints(self, listing: NormalizedListing) -> bool:
        """Check if listing meets hard constraints."""
        constraints = self.spec.get_hard_constraints()
        
        # Budget constraint
        if listing.total_cost > constraints.budget_max:
            return False
        
        # Condition constraint
        if listing.condition is not None:
            if listing.condition not in constraints.condition_allowed:
                return False
        
        # Max delivery days constraint (if specified)
        if constraints.max_delivery_days is not None:
            if listing.eta_max_days is not None:
                if listing.eta_max_days > constraints.max_delivery_days:
                    return False
        
        return True
    
    def filter_candidates(
        self, 
        listings: list[NormalizedListing]
    ) -> list[NormalizedListing]:
        """Filter listings that don't meet hard constraints."""
        return [l for l in listings if self.passes_constraints(l)]
    
    def _score_price(
        self, 
        listing: NormalizedListing, 
        all_listings: list[NormalizedListing]
    ) -> float:
        """
        Score price: 0 = most expensive, 1 = cheapest.
        Uses min-max normalization across candidate set.
        """
        if not all_listings:
            return 0.5
        
        prices = [l.total_cost for l in all_listings]
        min_price = min(prices)
        max_price = max(prices)
        
        if max_price == min_price:
            return 1.0  # All same price, all get perfect score
        
        # Invert so cheaper = higher score
        return 1.0 - (listing.total_cost - min_price) / (max_price - min_price)
    
    def _score_delivery(self, listing: NormalizedListing) -> float:
        """
        Score delivery speed: 0 = slow/unknown, 1 = fast.
        """
        if listing.eta_max_days is None:
            # Unknown delivery - apply penalty based on risk tolerance
            return 0.5 - self.unknown_penalty
        
        # Score based on ETA (using average of min/max)
        avg_eta = listing.eta_max_days
        if listing.eta_min_days is not None:
            avg_eta = (listing.eta_min_days + listing.eta_max_days) / 2
        
        # 1-2 days = excellent, 3-5 = good, 7+ = poor
        if avg_eta <= 2:
            return 1.0
        elif avg_eta <= 5:
            return 0.8
        elif avg_eta <= 7:
            return 0.6
        elif avg_eta <= 14:
            return 0.4
        else:
            return 0.2
    
    def _score_reliability(self, listing: NormalizedListing) -> float:
        """
        Score seller reliability: combines seller rating, feedback count, returns.
        """
        baseline = self.SOURCE_RELIABILITY_BASELINE[listing.source]
        score = baseline
        
        # Adjust based on seller rating (if available)
        if listing.seller_rating is not None:
            # Rating is 0-100, normalize to contribution
            rating_contribution = (listing.seller_rating / 100) * 0.3
            score = baseline * 0.7 + rating_contribution
        
        # Adjust based on feedback count (diminishing returns)
        if listing.seller_feedback_count is not None:
            if listing.seller_feedback_count >= 10000:
                feedback_bonus = 0.10
            elif listing.seller_feedback_count >= 1000:
                feedback_bonus = 0.07
            elif listing.seller_feedback_count >= 100:
                feedback_bonus = 0.04
            elif listing.seller_feedback_count >= 10:
                feedback_bonus = 0.02
            else:
                feedback_bonus = 0.0
            score = min(1.0, score + feedback_bonus)
        
        # Adjust based on return policy
        if listing.return_window_days is not None:
            if listing.return_window_days >= 30:
                score = min(1.0, score + 0.05)
            elif listing.return_window_days >= 15:
                score = min(1.0, score + 0.02)
        
        return min(1.0, max(0.0, score))
    
    def _score_warranty(self, listing: NormalizedListing) -> float:
        """
        Score warranty: longer is better.
        """
        if listing.warranty_months is None:
            # Unknown warranty - treat based on source
            if listing.source == Source.BESTBUY:
                # Best Buy items typically have manufacturer warranty
                return 0.6
            else:
                # eBay items often have no warranty
                return 0.3 - self.unknown_penalty
        
        # Score based on warranty length
        if listing.warranty_months >= 24:
            return 1.0
        elif listing.warranty_months >= 12:
            return 0.8
        elif listing.warranty_months >= 6:
            return 0.6
        elif listing.warranty_months >= 3:
            return 0.4
        else:
            return 0.2
    
    def _score_spec_match(
        self, 
        listing: NormalizedListing,
        category: str
    ) -> float:
        """
        Score how well specs match the query/category.
        Category-specific heuristics.
        """
        query_lower = self.spec.query.lower()
        specs = listing.specs
        
        if category == "headphones":
            score = 0.5  # Baseline
            
            # Check if wireless matches query
            wants_wireless = "wireless" in query_lower or "bluetooth" in query_lower
            is_wireless = specs.get("wireless", False)
            if wants_wireless and is_wireless:
                score += 0.2
            elif wants_wireless and not is_wireless:
                score -= 0.2
            
            # Check if noise canceling matches query
            wants_anc = any(w in query_lower for w in [
                "noise cancel", "noise-cancel", "anc", "noise cancelling"
            ])
            has_anc = specs.get("noise_canceling", False)
            if wants_anc and has_anc:
                score += 0.2
            elif wants_anc and not has_anc:
                score -= 0.2
            
            # Check form factor
            wants_over_ear = "over-ear" in query_lower or "over ear" in query_lower
            wants_in_ear = "earbud" in query_lower or "in-ear" in query_lower
            is_over_ear = specs.get("over_ear", False)
            is_in_ear = specs.get("in_ear", False)
            
            if wants_over_ear and is_over_ear:
                score += 0.1
            elif wants_in_ear and is_in_ear:
                score += 0.1
            
            return min(1.0, max(0.0, score))
        
        elif category == "monitors":
            score = 0.5  # Baseline for monitors
            # Would check resolution, size, refresh rate etc.
            return score
        
        return 0.5  # Default neutral score
    
    def score_listing(
        self,
        listing: NormalizedListing,
        all_listings: list[NormalizedListing],
        weights: WeightConfig | None = None
    ) -> ScoredListing:
        """
        Compute all dimension scores and weighted total for a listing.
        
        Args:
            listing: The listing to score
            all_listings: All listings (for relative scoring like price)
            weights: Optional override weights (defaults to spec weights)
            
        Returns:
            ScoredListing with component and total scores
        """
        if weights is None:
            weights = self.spec.weights.normalized()
        else:
            weights = weights.normalized()
        
        # Compute component scores
        scores = ComponentScores(
            price=self._score_price(listing, all_listings),
            delivery=self._score_delivery(listing),
            reliability=self._score_reliability(listing),
            warranty=self._score_warranty(listing),
            spec_match=self._score_spec_match(listing, self.spec.category),
        )
        
        # Compute weighted total
        total = (
            weights.price * scores.price +
            weights.delivery * scores.delivery +
            weights.reliability * scores.reliability +
            weights.warranty * scores.warranty +
            weights.spec_match * scores.spec_match
        )
        
        return ScoredListing(
            listing=listing,
            scores=scores,
            total_score=total
        )
    
    def score_all(
        self,
        listings: list[NormalizedListing],
        weights: WeightConfig | None = None
    ) -> list[ScoredListing]:
        """Score all listings and return sorted by total score (descending)."""
        scored = [
            self.score_listing(l, listings, weights) 
            for l in listings
        ]
        return sorted(scored, key=lambda x: x.total_score, reverse=True)
    
    def get_value_weights(self) -> WeightConfig:
        """Get weights optimized for value (price-focused)."""
        base = self.spec.weights.normalized()
        return WeightConfig(
            price=base.price * 1.5,
            delivery=base.delivery * 0.9,
            reliability=base.reliability * 0.9,
            warranty=base.warranty * 0.9,
            spec_match=base.spec_match * 0.9,
        )
    
    def get_low_risk_weights(self) -> WeightConfig:
        """Get weights optimized for low risk (reliability/warranty focused)."""
        base = self.spec.weights.normalized()
        return WeightConfig(
            price=base.price * 0.7,
            delivery=base.delivery * 0.8,
            reliability=base.reliability * 1.5,
            warranty=base.warranty * 1.5,
            spec_match=base.spec_match * 0.8,
        )
