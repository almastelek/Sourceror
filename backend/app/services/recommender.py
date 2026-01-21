"""
Main recommender service - orchestrates the full recommendation pipeline.
"""
from ..models import (
    DecisionSpec,
    NormalizedListing,
    ScoredListing,
    Recommendation,
    RecommendationLabel,
    RecommendationResponse,
    SensitivityResult,
    DebugInfo,
    Stability,
    Source,
)
from .candidate_service import CandidateService
from .scoring import ScoringEngine
from .sensitivity import SensitivityAnalyzer


class Recommender:
    """
    Main orchestrator for the recommendation engine.
    
    Combines candidate fetching, scoring, top-3 selection, 
    and sensitivity analysis into a single cohesive pipeline.
    """
    
    def __init__(self):
        self.candidate_service = CandidateService()
    
    def _generate_explanation(
        self,
        scored: ScoredListing,
        label: RecommendationLabel,
        all_scored: list[ScoredListing]
    ) -> tuple[list[str], str]:
        """
        Generate "why this pick" bullets and main tradeoff.
        
        Returns:
            Tuple of (why_bullets, tradeoff)
        """
        listing = scored.listing
        scores = scored.scores
        why: list[str] = []
        tradeoff = ""
        
        # Find strengths (scores > 0.7)
        if scores.price >= 0.7:
            why.append(f"Competitive price at ${listing.total_cost:.2f}")
        if scores.delivery >= 0.7:
            if listing.eta_max_days:
                why.append(f"Fast delivery ({listing.eta_min_days or listing.eta_max_days}-{listing.eta_max_days} days)")
            else:
                why.append("Reliable delivery")
        if scores.reliability >= 0.75:
            if listing.source == Source.BESTBUY:
                why.append("Best Buy's trusted retail experience")
            elif listing.seller_rating and listing.seller_rating >= 95:
                why.append(f"Highly rated seller ({listing.seller_rating:.1f}% positive)")
        if scores.warranty >= 0.7:
            if listing.warranty_months:
                why.append(f"{listing.warranty_months}-month warranty included")
        if scores.spec_match >= 0.7:
            why.append("Matches your specifications well")
        
        # If we don't have enough reasons, add generic ones
        if len(why) < 2:
            if listing.source == Source.BESTBUY:
                why.append("Backed by Best Buy's return policy")
            if listing.return_window_days and listing.return_window_days >= 15:
                why.append(f"{listing.return_window_days}-day return window")
        
        # Limit to 3 reasons
        why = why[:3]
        
        # If still empty, add a generic reason
        if not why:
            why.append("Balanced option across all criteria")
        
        # Find the main tradeoff (lowest score dimension)
        score_map = {
            "price": (scores.price, f"Higher price (${listing.total_cost:.2f})"),
            "delivery": (scores.delivery, "Slower delivery estimate"),
            "reliability": (scores.reliability, "Less seller data available"),
            "warranty": (scores.warranty, "Limited warranty information"),
            "spec_match": (scores.spec_match, "May not match all preferences"),
        }
        
        # Find lowest score
        min_score = 1.0
        for dim, (score, msg) in score_map.items():
            if score < min_score:
                min_score = score
                tradeoff = msg
        
        # Customize tradeoff by label
        if label == RecommendationLabel.VALUE:
            # Value pick trades off reliability/warranty for price
            if scores.reliability < 0.7:
                tradeoff = "May have less seller/return protection than premium options"
        elif label == RecommendationLabel.LOW_RISK:
            # Low risk trades off price for safety
            if scores.price < 0.7:
                tradeoff = "Premium price for added peace of mind"
        
        if not tradeoff:
            tradeoff = "Well-balanced with no major compromises"
        
        return why, tradeoff
    
    def _select_top3(
        self,
        filtered_listings: list[NormalizedListing],
        engine: ScoringEngine
    ) -> list[Recommendation]:
        """
        Select the top 3 recommendations with different optimization profiles.
        
        1. Overall: Best by user's weights
        2. Value: Best with price weight boosted
        3. Low Risk: Best with reliability/warranty boosted
        """
        if not filtered_listings:
            return []
        
        recommendations: list[Recommendation] = []
        used_ids: set[str] = set()
        
        # 1. Overall pick (user weights)
        overall_scored = engine.score_all(filtered_listings)
        if overall_scored:
            winner = overall_scored[0]
            used_ids.add(winner.listing.id)
            why, tradeoff = self._generate_explanation(
                winner, RecommendationLabel.OVERALL, overall_scored
            )
            recommendations.append(Recommendation(
                label=RecommendationLabel.OVERALL,
                listing=winner.listing,
                scores=winner.scores,
                total_score=winner.total_score,
                why=why,
                tradeoff=tradeoff,
            ))
        
        # 2. Value pick (price-focused)
        value_weights = engine.get_value_weights()
        value_scored = engine.score_all(filtered_listings, value_weights)
        for scored in value_scored:
            if scored.listing.id not in used_ids:
                used_ids.add(scored.listing.id)
                why, tradeoff = self._generate_explanation(
                    scored, RecommendationLabel.VALUE, value_scored
                )
                recommendations.append(Recommendation(
                    label=RecommendationLabel.VALUE,
                    listing=scored.listing,
                    scores=scored.scores,
                    total_score=scored.total_score,
                    why=why,
                    tradeoff=tradeoff,
                ))
                break
        
        # 3. Low Risk pick (reliability/warranty focused)
        risk_weights = engine.get_low_risk_weights()
        risk_scored = engine.score_all(filtered_listings, risk_weights)
        for scored in risk_scored:
            if scored.listing.id not in used_ids:
                used_ids.add(scored.listing.id)
                why, tradeoff = self._generate_explanation(
                    scored, RecommendationLabel.LOW_RISK, risk_scored
                )
                recommendations.append(Recommendation(
                    label=RecommendationLabel.LOW_RISK,
                    listing=scored.listing,
                    scores=scored.scores,
                    total_score=scored.total_score,
                    why=why,
                    tradeoff=tradeoff,
                ))
                break
        
        return recommendations
    
    async def get_recommendations(
        self,
        spec: DecisionSpec
    ) -> RecommendationResponse:
        """
        Execute the full recommendation pipeline.
        
        Args:
            spec: User's decision specification
            
        Returns:
            Complete recommendation response with top-3, sensitivity analysis, etc.
        """
        errors: list[str] = []
        
        # 1. Fetch candidates from all sources
        all_listings, sources_used, fetch_errors = await self.candidate_service.fetch_candidates(spec)
        errors.extend(fetch_errors)
        
        candidates_considered = len(all_listings)
        
        # 2. Deduplicate listings
        all_listings = self.candidate_service.deduplicate(all_listings)
        
        # 3. Initialize scoring engine and filter by constraints
        engine = ScoringEngine(spec)
        filtered_listings = engine.filter_candidates(all_listings)
        candidates_after_filter = len(filtered_listings)
        
        # 4. Handle empty results
        if not filtered_listings:
            return RecommendationResponse(
                decision_spec=spec,
                top3=[],
                ranked_shortlist=[],
                sensitivity=SensitivityResult(
                    stability=Stability.HIGH,
                    switch_conditions=[],
                    budget_relaxation=[],
                ),
                debug=DebugInfo(
                    candidates_considered=candidates_considered,
                    candidates_after_filter=0,
                    sources_used=sources_used,
                    errors=errors + ["No products found matching your criteria. Try increasing budget or broadening search."],
                ),
            )
        
        # 5. Score all listings and get shortlist
        scored_listings = engine.score_all(filtered_listings)
        shortlist = scored_listings[:10]  # Top 10 for display
        
        # 6. Select top 3 recommendations
        top3 = self._select_top3(filtered_listings, engine)
        
        # 7. Run sensitivity analysis
        current_winner_id = top3[0].listing.id if top3 else ""
        analyzer = SensitivityAnalyzer(spec, all_listings)
        sensitivity = analyzer.analyze(filtered_listings, current_winner_id)
        
        # 8. Build response
        return RecommendationResponse(
            decision_spec=spec,
            top3=top3,
            ranked_shortlist=shortlist,
            sensitivity=sensitivity,
            debug=DebugInfo(
                candidates_considered=candidates_considered,
                candidates_after_filter=candidates_after_filter,
                sources_used=sources_used,
                errors=errors,
            ),
        )
