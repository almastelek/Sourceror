"""
Abstract base class for data source connectors.
"""
from abc import ABC, abstractmethod
from ..models import NormalizedListing


class BaseConnector(ABC):
    """Abstract interface for product data connectors."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the source identifier."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        category: str,
        max_results: int = 25
    ) -> list[NormalizedListing]:
        """
        Search for products matching the query.
        
        Args:
            query: Search text
            category: Product category (e.g., 'headphones')
            max_results: Maximum number of results to return
            
        Returns:
            List of normalized listings
        """
        pass
    
    @abstractmethod
    async def get_details(self, product_id: str) -> NormalizedListing | None:
        """
        Fetch detailed information for a specific product.
        
        Args:
            product_id: Source-specific product identifier
            
        Returns:
            NormalizedListing with full details, or None if not found
        """
        pass
