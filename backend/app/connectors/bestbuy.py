"""
Best Buy Products API connector.

API Documentation: https://developer.bestbuy.com/documentation/products-api
"""
import httpx
from typing import Any
from .base import BaseConnector
from ..models import NormalizedListing, Source, Condition
from ..config import get_settings
from ..cache import get_cache


class BestBuyConnector(BaseConnector):
    """Connector for Best Buy Products API."""
    
    BASE_URL = "https://api.bestbuy.com/v1"
    
    # Category mapping for Best Buy API
    CATEGORY_FILTERS = {
        "headphones": "(categoryPath.id=abcat0204000)",  # Headphones category
        "monitors": "(categoryPath.id=abcat0509000)",    # Monitors category
        "laptops": "(categoryPath.id=abcat0502000)",     # Laptops category
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.cache = get_cache()
    
    @property
    def source_name(self) -> str:
        return "bestbuy"
    
    def _get_category_filter(self, category: str) -> str:
        """Get Best Buy category filter for the given category."""
        return self.CATEGORY_FILTERS.get(
            category.lower(), 
            self.CATEGORY_FILTERS["headphones"]
        )
    
    def _parse_condition(self, product: dict[str, Any]) -> Condition:
        """Parse condition from Best Buy product data."""
        # Best Buy primarily sells new products
        # Check for refurbished indicators
        name = product.get("name", "").lower()
        if "refurbished" in name or "renewed" in name:
            return Condition.REFURBISHED
        if "open-box" in name or "pre-owned" in name:
            return Condition.USED
        return Condition.NEW
    
    def _parse_specs(self, product: dict[str, Any], category: str) -> dict[str, Any]:
        """Extract category-specific specs from product."""
        specs: dict[str, Any] = {}
        
        if category == "headphones":
            # Headphone-specific specs
            name = product.get("name", "").lower()
            description = product.get("shortDescription", "").lower()
            combined = f"{name} {description}"
            
            specs["wireless"] = any(w in combined for w in ["wireless", "bluetooth"])
            specs["noise_canceling"] = any(w in combined for w in [
                "noise cancel", "noise-cancel", "anc", "active noise"
            ])
            specs["over_ear"] = "over-ear" in combined or "over ear" in combined
            specs["in_ear"] = "in-ear" in combined or "earbud" in combined
            
            # Extract brand from name (first word usually)
            name_parts = product.get("name", "").split()
            if name_parts:
                specs["brand"] = name_parts[0]
                
        elif category == "monitors":
            name = product.get("name", "").lower()
            specs["size_inches"] = product.get("screenSizeIn")
            specs["resolution"] = None  # Would need detail API
            specs["refresh_rate"] = None
            specs["panel_type"] = None
            
        return specs
    
    def _normalize_listing(
        self, 
        product: dict[str, Any], 
        category: str
    ) -> NormalizedListing:
        """Convert Best Buy product to NormalizedListing."""
        price = product.get("salePrice") or product.get("regularPrice", 0)
        shipping = 0.0 if product.get("freeShipping", False) else product.get("shippingCost", 0)
        if shipping is None:
            shipping = 0.0
            
        # Best Buy typically has standardized return/warranty
        return_days = 15  # Standard Best Buy return policy
        warranty_months = 12  # Manufacturer warranty (1 year typical)
        
        # Estimate delivery based on availability
        availability = product.get("onlineAvailability", False)
        eta_min = 2 if availability else 5
        eta_max = 5 if availability else 10
        
        return NormalizedListing(
            id=str(product.get("sku", "")),
            source=Source.BESTBUY,
            title=product.get("name", "Unknown Product"),
            url=product.get("url", ""),
            image_url=product.get("image"),
            price=float(price),
            shipping_cost=float(shipping) if shipping else None,
            total_cost=float(price) + (float(shipping) if shipping else 0),
            condition=self._parse_condition(product),
            eta_min_days=eta_min,
            eta_max_days=eta_max,
            return_window_days=return_days,
            seller_rating=98.0,  # Best Buy has high baseline trust
            seller_feedback_count=100000,  # Large retailer
            warranty_months=warranty_months,
            specs=self._parse_specs(product, category),
            raw={
                "sku": product.get("sku"),
                "regularPrice": product.get("regularPrice"),
                "salePrice": product.get("salePrice"),
                "customerReviewAverage": product.get("customerReviewAverage"),
                "customerReviewCount": product.get("customerReviewCount"),
            }
        )
    
    async def search(
        self,
        query: str,
        category: str,
        max_results: int = 25
    ) -> list[NormalizedListing]:
        """Search Best Buy Products API."""
        if not self.settings.bestbuy_api_key:
            return []
        
        # Check cache first
        cache_params = {"query": query, "category": category, "max": max_results}
        cached = self.cache.get("bestbuy_search", cache_params)
        if cached:
            return [NormalizedListing(**item) for item in cached]
        
        category_filter = self._get_category_filter(category)
        
        # Build search query
        # Best Buy API uses a combination of search terms and category filters
        search_filter = f"(search={query})&{category_filter}"
        
        url = f"{self.BASE_URL}/products{search_filter}"
        params = {
            "apiKey": self.settings.bestbuy_api_key,
            "format": "json",
            "show": "sku,name,salePrice,regularPrice,url,image,shortDescription,"
                   "freeShipping,shippingCost,onlineAvailability,customerReviewAverage,"
                   "customerReviewCount,screenSizeIn",
            "pageSize": min(max_results, 100),
            "page": 1,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
            products = data.get("products", [])
            listings = [
                self._normalize_listing(p, category) 
                for p in products[:max_results]
            ]
            
            # Cache results
            self.cache.set(
                "bestbuy_search", 
                cache_params, 
                [l.model_dump() for l in listings]
            )
            
            return listings
            
        except httpx.HTTPError as e:
            print(f"Best Buy API error: {e}")
            return []
    
    async def get_details(self, product_id: str) -> NormalizedListing | None:
        """Fetch detailed product information by SKU."""
        if not self.settings.bestbuy_api_key:
            return None
        
        # Check cache
        cache_params = {"sku": product_id}
        cached = self.cache.get("bestbuy_detail", cache_params)
        if cached:
            return NormalizedListing(**cached)
        
        url = f"{self.BASE_URL}/products/{product_id}.json"
        params = {
            "apiKey": self.settings.bestbuy_api_key,
            "show": "sku,name,salePrice,regularPrice,url,image,shortDescription,"
                   "longDescription,freeShipping,shippingCost,onlineAvailability,"
                   "customerReviewAverage,customerReviewCount,details",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                product = response.json()
                
            listing = self._normalize_listing(product, "headphones")
            
            # Cache result
            self.cache.set("bestbuy_detail", cache_params, listing.model_dump())
            
            return listing
            
        except httpx.HTTPError as e:
            print(f"Best Buy API error: {e}")
            return None
