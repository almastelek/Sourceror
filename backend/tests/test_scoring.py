"""
Unit tests for the scoring engine.
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
)
from app.services.scoring import ScoringEngine


# Test fixtures
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
def sample_listings() -> list[NormalizedListing]:
    """Create sample listings for testing."""
    return [
        NormalizedListing(
            id="bb-001",
            source=Source.BESTBUY,
            title="Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            url="https://bestbuy.com/product/001",
            price=280.0,
            shipping_cost=0.0,
            total_cost=280.0,
            condition=Condition.NEW,
            eta_min_days=2,
            eta_max_days=4,
            return_window_days=15,
            seller_rating=98.0,
            seller_feedback_count=100000,
            warranty_months=12,
            specs={"wireless": True, "noise_canceling": True},
        ),
        NormalizedListing(
            id="bb-002",
            source=Source.BESTBUY,
            title="Bose QuietComfort 45 Headphones",
            url="https://bestbuy.com/product/002",
            price=200.0,
            shipping_cost=0.0,
            total_cost=200.0,
            condition=Condition.NEW,
            eta_min_days=2,
            eta_max_days=5,
            return_window_days=15,
            seller_rating=98.0,
            seller_feedback_count=100000,
            warranty_months=12,
            specs={"wireless": True, "noise_canceling": True},
        ),
        NormalizedListing(
            id="ebay-001",
            source=Source.EBAY,
            title="Sony WH-1000XM4 Refurbished",
            url="https://ebay.com/item/001",
            price=150.0,
            shipping_cost=10.0,
            total_cost=160.0,
            condition=Condition.REFURBISHED,
            eta_min_days=3,
            eta_max_days=7,
            return_window_days=30,
            seller_rating=95.0,
            seller_feedback_count=500,
            warranty_months=None,
            specs={"wireless": True, "noise_canceling": True},
        ),
        NormalizedListing(
            id="ebay-002",
            source=Source.EBAY,
            title="Generic Wireless Headphones",
            url="https://ebay.com/item/002",
            price=50.0,
            shipping_cost=5.0,
            total_cost=55.0,
            condition=Condition.NEW,
            eta_min_days=5,
            eta_max_days=10,
            return_window_days=14,
            seller_rating=85.0,
            seller_feedback_count=50,
            warranty_months=3,
            specs={"wireless": True, "noise_canceling": False},
        ),
    ]


class TestConstraintGating:
    """Tests for constraint filtering."""
    
    def test_budget_constraint_filters_over_budget(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """Items over budget should be filtered out."""
        engine = ScoringEngine(sample_spec)
        filtered = engine.filter_candidates(sample_listings)
        
        # Sony WH-1000XM5 at $280 should be filtered (budget is $250)
        ids = [l.id for l in filtered]
        assert "bb-001" not in ids
        assert "bb-002" in ids  # $200 should pass
        assert "ebay-001" in ids  # $160 should pass
        assert "ebay-002" in ids  # $55 should pass
    
    def test_condition_constraint_filters_disallowed(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """Items with disallowed conditions should be filtered."""
        # Modify spec to only allow new
        spec = DecisionSpec(
            category="headphones",
            query="headphones",
            budget_max=500.0,
            condition_allowed=["new"],
            delivery_priority=DeliveryPriority.MEDIUM,
            risk_tolerance=RiskTolerance.MEDIUM,
            weights=sample_spec.weights,
        )
        engine = ScoringEngine(spec)
        filtered = engine.filter_candidates(sample_listings)
        
        # Refurbished items should be filtered
        ids = [l.id for l in filtered]
        assert "ebay-001" not in ids  # Refurbished
        assert "bb-001" in ids  # New
        assert "ebay-002" in ids  # New


class TestPriceScoring:
    """Tests for price score calculation."""
    
    def test_cheapest_gets_highest_score(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """The cheapest item should get a price score of 1.0."""
        engine = ScoringEngine(sample_spec)
        
        # Get price scores for all
        scored = engine.score_all(sample_listings)
        
        # Find the cheapest item (ebay-002 at $55)
        cheapest = next(s for s in scored if s.listing.id == "ebay-002")
        assert cheapest.scores.price == 1.0
    
    def test_most_expensive_gets_lowest_score(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """The most expensive item should get a price score of 0.0."""
        engine = ScoringEngine(sample_spec)
        scored = engine.score_all(sample_listings)
        
        # Find the most expensive (bb-001 at $280)
        expensive = next(s for s in scored if s.listing.id == "bb-001")
        assert expensive.scores.price == 0.0


class TestDeliveryScoring:
    """Tests for delivery score calculation."""
    
    def test_fast_delivery_gets_high_score(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """Items with 1-2 day delivery should get score of 1.0."""
        engine = ScoringEngine(sample_spec)
        
        # Create a fast delivery listing
        fast = NormalizedListing(
            id="fast-001",
            source=Source.BESTBUY,
            title="Fast Delivery Headphones",
            url="https://example.com",
            price=100.0,
            shipping_cost=0.0,
            total_cost=100.0,
            condition=Condition.NEW,
            eta_min_days=1,
            eta_max_days=2,
            return_window_days=15,
            seller_rating=98.0,
            seller_feedback_count=1000,
            warranty_months=12,
            specs={},
        )
        
        scored = engine.score_listing(fast, [fast])
        assert scored.scores.delivery == 1.0
    
    def test_slow_delivery_gets_low_score(
        self, sample_spec: DecisionSpec
    ):
        """Items with slow delivery should get lower scores."""
        engine = ScoringEngine(sample_spec)
        
        slow = NormalizedListing(
            id="slow-001",
            source=Source.EBAY,
            title="Slow Delivery Headphones",
            url="https://example.com",
            price=100.0,
            shipping_cost=0.0,
            total_cost=100.0,
            condition=Condition.NEW,
            eta_min_days=14,
            eta_max_days=21,
            return_window_days=15,
            seller_rating=98.0,
            seller_feedback_count=1000,
            warranty_months=12,
            specs={},
        )
        
        scored = engine.score_listing(slow, [slow])
        assert scored.scores.delivery < 0.5


class TestReliabilityScoring:
    """Tests for reliability score calculation."""
    
    def test_bestbuy_has_higher_baseline(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """Best Buy items should have higher baseline reliability."""
        engine = ScoringEngine(sample_spec)
        
        bb_listing = sample_listings[0]  # Best Buy
        ebay_listing = sample_listings[2]  # eBay with good rating
        
        bb_scored = engine.score_listing(bb_listing, sample_listings)
        ebay_scored = engine.score_listing(ebay_listing, sample_listings)
        
        # Best Buy should generally score higher
        assert bb_scored.scores.reliability >= ebay_scored.scores.reliability


class TestWeightedTotal:
    """Tests for weighted total score calculation."""
    
    def test_weighted_total_sums_correctly(self, sample_spec: DecisionSpec):
        """Weighted total should equal sum of weight * score for each dimension."""
        engine = ScoringEngine(sample_spec)
        
        listing = NormalizedListing(
            id="test-001",
            source=Source.BESTBUY,
            title="Test Headphones",
            url="https://example.com",
            price=100.0,
            shipping_cost=0.0,
            total_cost=100.0,
            condition=Condition.NEW,
            eta_min_days=2,
            eta_max_days=3,
            return_window_days=15,
            seller_rating=98.0,
            seller_feedback_count=1000,
            warranty_months=12,
            specs={"wireless": True, "noise_canceling": True},
        )
        
        scored = engine.score_listing(listing, [listing])
        weights = sample_spec.weights.normalized()
        
        expected = (
            weights.price * scored.scores.price +
            weights.delivery * scored.scores.delivery +
            weights.reliability * scored.scores.reliability +
            weights.warranty * scored.scores.warranty +
            weights.spec_match * scored.scores.spec_match
        )
        
        assert abs(scored.total_score - expected) < 0.001
    
    def test_custom_weights_affect_ranking(
        self, sample_spec: DecisionSpec, sample_listings: list[NormalizedListing]
    ):
        """Different weights should produce different rankings."""
        engine = ScoringEngine(sample_spec)
        
        # Score with default weights
        default_scored = engine.score_all(sample_listings)
        default_winner = default_scored[0].listing.id
        
        # Score with price-heavy weights
        price_weights = WeightConfig(
            price=0.8, delivery=0.05, reliability=0.05, warranty=0.05, spec_match=0.05
        )
        price_scored = engine.score_all(sample_listings, price_weights)
        price_winner = price_scored[0].listing.id
        
        # With price-heavy weights, the cheapest item should win
        assert price_winner == "ebay-002"  # The $55 item


class TestSpecMatchScoring:
    """Tests for spec match scoring."""
    
    def test_matching_specs_get_higher_score(self, sample_spec: DecisionSpec):
        """Items matching query specs should score higher."""
        engine = ScoringEngine(sample_spec)
        
        matching = NormalizedListing(
            id="match-001",
            source=Source.BESTBUY,
            title="Wireless Noise Canceling Headphones",
            url="https://example.com",
            price=100.0,
            shipping_cost=0.0,
            total_cost=100.0,
            condition=Condition.NEW,
            specs={"wireless": True, "noise_canceling": True},
        )
        
        non_matching = NormalizedListing(
            id="nomatch-001",
            source=Source.BESTBUY,
            title="Wired Headphones",
            url="https://example.com",
            price=100.0,
            shipping_cost=0.0,
            total_cost=100.0,
            condition=Condition.NEW,
            specs={"wireless": False, "noise_canceling": False},
        )
        
        listings = [matching, non_matching]
        match_scored = engine.score_listing(matching, listings)
        nomatch_scored = engine.score_listing(non_matching, listings)
        
        assert match_scored.scores.spec_match > nomatch_scored.scores.spec_match
