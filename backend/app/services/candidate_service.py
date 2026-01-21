"""
Candidate service - fetches and aggregates listings from all sources.
"""
import asyncio
from ..connectors import BestBuyConnector, EbayConnector
from ..models import NormalizedListing, DecisionSpec


class CandidateService:
    """Service for fetching and aggregating product listings from all sources."""
    
    def __init__(self):
        self.bestbuy = BestBuyConnector()
        self.ebay = EbayConnector()
    
    async def fetch_candidates(
        self,
        spec: DecisionSpec,
        max_per_source: int = 25
    ) -> tuple[list[NormalizedListing], list[str], list[str]]:
        """
        Fetch listings from all sources concurrently.
        
        Args:
            spec: Decision specification with query and category
            max_per_source: Maximum results per source
            
        Returns:
            Tuple of (listings, sources_used, errors)
        """
        errors: list[str] = []
        sources_used: list[str] = []
        all_listings: list[NormalizedListing] = []
        
        # Fetch from both sources concurrently
        bestbuy_task = self.bestbuy.search(
            query=spec.query,
            category=spec.category,
            max_results=max_per_source
        )
        ebay_task = self.ebay.search(
            query=spec.query,
            category=spec.category,
            max_results=max_per_source
        )
        
        results = await asyncio.gather(
            bestbuy_task,
            ebay_task,
            return_exceptions=True
        )
        
        # Process Best Buy results
        if isinstance(results[0], Exception):
            errors.append(f"Best Buy error: {str(results[0])}")
        elif results[0]:
            all_listings.extend(results[0])
            sources_used.append("bestbuy")
        
        # Process eBay results
        if isinstance(results[1], Exception):
            errors.append(f"eBay error: {str(results[1])}")
        elif results[1]:
            all_listings.extend(results[1])
            sources_used.append("ebay")
        
        return all_listings, sources_used, errors
    
    def deduplicate(
        self, 
        listings: list[NormalizedListing]
    ) -> list[NormalizedListing]:
        """
        Remove duplicate listings based on title similarity.
        Keeps the first occurrence (preserves source priority).
        
        For MVP, uses simple title matching. 
        Could be enhanced with fuzzy matching.
        """
        seen_titles: set[str] = set()
        unique: list[NormalizedListing] = []
        
        for listing in listings:
            # Normalize title for comparison
            normalized_title = listing.title.lower().strip()
            # Remove common variations
            for word in ["refurbished", "renewed", "certified", "pre-owned"]:
                normalized_title = normalized_title.replace(word, "")
            normalized_title = " ".join(normalized_title.split())  # Normalize whitespace
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique.append(listing)
        
        return unique
