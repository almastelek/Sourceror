"""
Unit tests for sensitivity analysis.
"""
import pytest
from app.models import (
    NormalizedListing,
    DecisionSpec,
    WeightConfig,
    Source,
    Condition,
    RiskTolerance,
    DeliveryPriority,
    Stability,
)
from app.services.sensitivity import SensitivityAnalyzer


@pytest.fixture
def sample_spec() -> DecisionSpec:
    """Create a sample DecisionSpec for testing."""
    return DecisionSpec(
        category="headphones",
        query="noise cancelling wireless headphones",
        budget_max=250.0,
        condition_allowed=["new", "refurb"],
        delivery_priority=DeliveryPriority.MEDIUM,
        risk_tolerance=RiskTolerance.MEDIUM,
        weights=WeightConfig(
            price=0.25,
            delivery=0.20,
            reliability=0.25,
            warranty=0.15,
            spec_match=0.15,
        ),
    )


@pytest.fixture
def close_competitors() -> list[NormalizedListing]:
    """Create listings that are close in score - sensitive to weight changes."""
    return [
        NormalizedListing(
            id="item-a",
            source=Source.BESTBUY,
            title="Product A - Balanced",
            url="https://example.com/a",
            price=200.0,
            shipping_cost=0.0,
            total_cost=200.0,
            condition=Condition.NEW,
            eta_min_days=3,
            eta_max_days=5,
            return_window_days=15,
            seller_rating=95.0,
            seller_feedback_count=5000,
            warranty_months=12,
            specs={"wireless": True, "noise_canceling": True},
        ),
        NormalizedListing(
            id="item-b",
            source=Source.EBAY,
            title="Product B - Cheaper",
            url="https://example.com/b",
            price=150.0,
            shipping_cost=10.0,
            total_cost=160.0,
            condition=Condition.NEW,
            eta_min_days=5,
            eta_max_days=7,
            return_window_days=14,
            seller_rating=90.0,
            seller_feedback_count=200,
            warranty_months=6,
            specs={"wireless": True, "noise_canceling": True},
        ),
    ]


@pytest.fixture
def wide_gap_listings() -> list[NormalizedListing]:
    """Create listings with clear winner - stable to weight changes."""
    return [
        NormalizedListing(
            id="clear-winner",
            source=Source.BESTBUY,
            title="Clear Winner Product",
            url="https://example.com/winner",
            price=150.0,
            shipping_cost=0.0,
            total_cost=150.0,
            condition=Condition.NEW,
            eta_min_days=1,
            eta_max_days=2,
            return_window_days=30,
            seller_rating=99.0,
            seller_feedback_count=50000,
            warranty_months=24,
            specs={"wireless": True, "noise_canceling": True},
        ),
        NormalizedListing(
            id="clear-loser",
            source=Source.EBAY,
            title="Clear Loser Product",
            url="https://example.com/loser",
            price=200.0,
            shipping_cost=20.0,
            total_cost=220.0,
            condition=Condition.REFURBISHED,
            eta_min_days=10,
            eta_max_days=14,
            return_window_days=7,
            seller_rating=80.0,
            seller_feedback_count=10,
            warranty_months=None,
            specs={"wireless": False, "noise_canceling": False},
        ),
    ]


class TestWeightSensitivity:
    """Tests for weight sweep analysis."""
    
    def test_detects_switch_with_close_competitors(
        self, sample_spec: DecisionSpec, close_competitors: list[NormalizedListing]
    ):
        """Should detect when weight changes cause winner switch."""
        analyzer = SensitivityAnalyzer(sample_spec, close_competitors)
        
        # Item A should be initial winner (Best Buy, better reliability)
        current_winner = "item-a"
        
        switch_conditions = analyzer.analyze_weight_sensitivity(
            close_competitors, current_winner
        )
        
        # With close competitors, we expect some switch conditions
        # Boosting price should favor item-b (cheaper)
        price_switches = [s for s in switch_conditions if s.dimension == "price"]
        
        # There should be at least one way to make item-b win
        assert any(s.new_winner_id == "item-b" for s in switch_conditions)
    
    def test_stable_with_clear_winner(
        self, sample_spec: DecisionSpec, wide_gap_listings: list[NormalizedListing]
    ):
        """Clear winner should have few or no switch conditions."""
        analyzer = SensitivityAnalyzer(sample_spec, wide_gap_listings)
        
        current_winner = "clear-winner"
        
        switch_conditions = analyzer.analyze_weight_sensitivity(
            wide_gap_listings, current_winner
        )
        
        # With a clear winner, there should be fewer switch conditions
        # The gap is so large that most weight changes won't flip the result
        assert len(switch_conditions) <= 2


class TestBudgetRelaxation:
    """Tests for budget relaxation analysis."""
    
    def test_detects_new_option_with_higher_budget(self, sample_spec: DecisionSpec):
        """Should detect when higher budget enables better options."""
        # Create listings where one is just over budget
        listings = [
            NormalizedListing(
                id="under-budget",
                source=Source.BESTBUY,
                title="Under Budget Product",
                url="https://example.com/under",
                price=200.0,
                shipping_cost=0.0,
                total_cost=200.0,
                condition=Condition.NEW,
                eta_min_days=3,
                eta_max_days=5,
                seller_rating=90.0,
                seller_feedback_count=1000,
                warranty_months=12,
                specs={"wireless": True},
            ),
            NormalizedListing(
                id="over-budget",
                source=Source.BESTBUY,
                title="Premium Over Budget Product",
                url="https://example.com/over",
                price=280.0,
                shipping_cost=0.0,
                total_cost=280.0,
                condition=Condition.NEW,
                eta_min_days=1,
                eta_max_days=2,
                seller_rating=99.0,
                seller_feedback_count=50000,
                warranty_months=24,
                specs={"wireless": True, "noise_canceling": True},
            ),
        ]
        
        analyzer = SensitivityAnalyzer(sample_spec, listings)
        relaxations = analyzer.analyze_budget_relaxation("under-budget")
        
        # At +$50 ($300), the premium product should become available
        budget_300 = next((r for r in relaxations if r.budget == 300), None)
        assert budget_300 is not None
        assert budget_300.new_winner_id == "over-budget"
    
    def test_no_change_when_budget_doesnt_help(self, sample_spec: DecisionSpec):
        """Should show no change if higher budget doesn't help."""
        listings = [
            NormalizedListing(
                id="only-option",
                source=Source.BESTBUY,
                title="Only Option",
                url="https://example.com/only",
                price=100.0,
                shipping_cost=0.0,
                total_cost=100.0,
                condition=Condition.NEW,
                eta_min_days=2,
                eta_max_days=4,
                seller_rating=95.0,
                seller_feedback_count=1000,
                warranty_months=12,
                specs={},
            ),
        ]
        
        analyzer = SensitivityAnalyzer(sample_spec, listings)
        relaxations = analyzer.analyze_budget_relaxation("only-option")
        
        # All relaxations should show no change
        for r in relaxations:
            assert r.new_winner_id is None or r.new_winner_id == "only-option"


class TestStabilityClassification:
    """Tests for overall stability classification."""
    
    def test_high_stability_with_no_switches(
        self, sample_spec: DecisionSpec, wide_gap_listings: list[NormalizedListing]
    ):
        """Clear winner should result in high stability."""
        analyzer = SensitivityAnalyzer(sample_spec, wide_gap_listings)
        result = analyzer.analyze(wide_gap_listings, "clear-winner")
        
        # With a clear winner, stability should be high
        assert result.stability in [Stability.HIGH, Stability.MEDIUM]
    
    def test_deterministic_output(
        self, sample_spec: DecisionSpec, close_competitors: list[NormalizedListing]
    ):
        """Same inputs should always produce same outputs."""
        analyzer = SensitivityAnalyzer(sample_spec, close_competitors)
        
        result1 = analyzer.analyze(close_competitors, "item-a")
        result2 = analyzer.analyze(close_competitors, "item-a")
        
        assert result1.stability == result2.stability
        assert len(result1.switch_conditions) == len(result2.switch_conditions)
        assert len(result1.budget_relaxation) == len(result2.budget_relaxation)
