"""
Sensitivity analysis for decision stability.
"""
from ..models import (
    NormalizedListing,
    ScoredListing,
    DecisionSpec,
    WeightConfig,
    SensitivityResult,
    WeightSwitchCondition,
    BudgetRelaxation,
    Stability,
)
from .scoring import ScoringEngine


class SensitivityAnalyzer:
    """
    Analyzes how stable the recommendation is to changes in weights or constraints.
    """
    
    # Weight multipliers to test
    WEIGHT_FACTORS = [0.5, 0.75, 1.25, 1.5, 2.0]
    
    # Budget relaxation amounts to test
    BUDGET_INCREASES = [50, 100, 200]
    
    # Dimension display names
    DIMENSION_NAMES = {
        "price": "Price",
        "delivery": "Delivery Speed",
        "reliability": "Reliability",
        "warranty": "Warranty",
        "spec_match": "Spec Match",
    }
    
    def __init__(self, spec: DecisionSpec, all_listings: list[NormalizedListing]):
        self.spec = spec
        self.all_listings = all_listings
        self.engine = ScoringEngine(spec)
    
    def _get_winner_id(
        self, 
        listings: list[NormalizedListing],
        weights: WeightConfig
    ) -> str | None:
        """Get the ID of the top-scoring listing with given weights."""
        if not listings:
            return None
        
        scored = self.engine.score_all(listings, weights)
        if scored:
            return scored[0].listing.id
        return None
    
    def _create_modified_weights(
        self,
        dimension: str,
        factor: float
    ) -> WeightConfig:
        """Create weights with one dimension modified by factor."""
        base = self.spec.weights.normalized()
        
        modified = {
            "price": base.price,
            "delivery": base.delivery,
            "reliability": base.reliability,
            "warranty": base.warranty,
            "spec_match": base.spec_match,
        }
        
        # Modify the specified dimension
        modified[dimension] = modified[dimension] * factor
        
        return WeightConfig(**modified)
    
    def analyze_weight_sensitivity(
        self,
        filtered_listings: list[NormalizedListing],
        current_winner_id: str
    ) -> list[WeightSwitchCondition]:
        """
        Analyze how changes in each weight dimension affect the winner.
        
        Returns list of conditions where the winner would change.
        """
        switch_conditions: list[WeightSwitchCondition] = []
        
        dimensions = ["price", "delivery", "reliability", "warranty", "spec_match"]
        
        for dimension in dimensions:
            for factor in self.WEIGHT_FACTORS:
                if factor == 1.0:
                    continue  # Skip no-change case
                
                modified_weights = self._create_modified_weights(dimension, factor)
                new_winner_id = self._get_winner_id(filtered_listings, modified_weights)
                
                if new_winner_id and new_winner_id != current_winner_id:
                    # Found a switch condition
                    direction = "increases" if factor > 1 else "decreases"
                    percent_change = abs(factor - 1) * 100
                    
                    message = (
                        f"If {self.DIMENSION_NAMES[dimension]} importance "
                        f"{direction} ~{percent_change:.0f}%, a different option becomes #1"
                    )
                    
                    switch_conditions.append(WeightSwitchCondition(
                        dimension=dimension,
                        factor=factor,
                        new_winner_id=new_winner_id,
                        message=message,
                    ))
                    
                    # Only report the smallest change that causes a switch
                    break
        
        return switch_conditions
    
    def analyze_budget_relaxation(
        self,
        current_winner_id: str
    ) -> list[BudgetRelaxation]:
        """
        Analyze how relaxing the budget constraint affects the winner.
        """
        relaxations: list[BudgetRelaxation] = []
        
        for increase in self.BUDGET_INCREASES:
            new_budget = self.spec.budget_max + increase
            
            # Create modified spec with higher budget
            modified_spec = DecisionSpec(
                category=self.spec.category,
                query=self.spec.query,
                budget_max=new_budget,
                condition_allowed=self.spec.condition_allowed,
                delivery_priority=self.spec.delivery_priority,
                risk_tolerance=self.spec.risk_tolerance,
                weights=self.spec.weights,
            )
            
            # Re-filter and re-score with new budget
            modified_engine = ScoringEngine(modified_spec)
            new_filtered = modified_engine.filter_candidates(self.all_listings)
            
            if not new_filtered:
                continue
            
            scored = modified_engine.score_all(new_filtered)
            new_winner_id = scored[0].listing.id if scored else None
            
            if new_winner_id and new_winner_id != current_winner_id:
                # New option becomes available or changes ranking
                new_winner_listing = scored[0].listing
                message = (
                    f"With +${increase} budget (${new_budget:.0f} total), "
                    f"'{new_winner_listing.title[:50]}...' becomes the top pick"
                )
                
                relaxations.append(BudgetRelaxation(
                    budget=new_budget,
                    new_winner_id=new_winner_id,
                    message=message,
                ))
            else:
                # Winner stays the same
                relaxations.append(BudgetRelaxation(
                    budget=new_budget,
                    new_winner_id=None,
                    message=f"With +${increase} budget, the recommendation stays the same",
                ))
        
        return relaxations
    
    def _classify_stability(
        self,
        switch_conditions: list[WeightSwitchCondition],
        budget_relaxations: list[BudgetRelaxation]
    ) -> Stability:
        """
        Classify overall decision stability based on analysis results.
        """
        # Count how many ways the decision could change
        weight_switches = len(switch_conditions)
        budget_switches = sum(1 for r in budget_relaxations if r.new_winner_id is not None)
        
        total_switches = weight_switches + budget_switches
        
        if total_switches == 0:
            return Stability.HIGH
        elif total_switches <= 2:
            return Stability.MEDIUM
        else:
            return Stability.LOW
    
    def analyze(
        self,
        filtered_listings: list[NormalizedListing],
        current_winner_id: str
    ) -> SensitivityResult:
        """
        Perform full sensitivity analysis.
        
        Args:
            filtered_listings: Listings that pass constraints
            current_winner_id: ID of the current top recommendation
            
        Returns:
            SensitivityResult with stability classification and switch conditions
        """
        # Analyze weight sensitivity
        switch_conditions = self.analyze_weight_sensitivity(
            filtered_listings, 
            current_winner_id
        )
        
        # Analyze budget relaxation
        budget_relaxations = self.analyze_budget_relaxation(current_winner_id)
        
        # Classify stability
        stability = self._classify_stability(switch_conditions, budget_relaxations)
        
        return SensitivityResult(
            stability=stability,
            switch_conditions=switch_conditions[:4],  # Limit to most relevant
            budget_relaxation=budget_relaxations,
        )
