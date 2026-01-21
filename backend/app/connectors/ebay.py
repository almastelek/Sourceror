"""
eBay Browse API connector.

API Documentation: https://developer.ebay.com/api-docs/buy/browse/overview.html
"""
import httpx
import base64
from typing import Any
from datetime import datetime, timedelta
from .base import BaseConnector
from ..models import NormalizedListing, Source, Condition
from ..config import get_settings
from ..cache import get_cache


class EbayConnector(BaseConnector):
    """Connector for eBay Browse API."""
    
    BROWSE_API_URL = "https://api.ebay.com/buy/browse/v1"
    AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    
    # Category IDs for eBay
    CATEGORY_IDS = {
        "headphones": "112529",   # Headphones category
        "monitors": "80053",      # Monitors category  
        "laptops": "175672",      # Laptops & Netbooks
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.cache = get_cache()
        self._access_token: str | None = None
        self._token_expires: datetime | None = None
    
    @property
    def source_name(self) -> str:
        return "ebay"
    
    async def _get_access_token(self) -> str | None:
        """Get OAuth access token, refreshing if needed."""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires:
            if datetime.now() < self._token_expires - timedelta(minutes=5):
                return self._access_token
        
        if not self.settings.ebay_client_id or not self.settings.ebay_client_secret:
            return None
        
        # Request new token
        credentials = f"{self.settings.ebay_client_id}:{self.settings.ebay_client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.AUTH_URL,
                    headers=headers,
                    data=data
                )
                response.raise_for_status()
                token_data = response.json()
                
            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 7200)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in)
            
            return self._access_token
            
        except httpx.HTTPError as e:
            print(f"eBay OAuth error: {e}")
            return None
    
    def _parse_condition(self, item: dict[str, Any]) -> Condition | None:
        """Parse condition from eBay item data."""
        condition = item.get("condition", "")
        condition_id = item.get("conditionId", "")
        
        if isinstance(condition, dict):
            condition = condition.get("conditionDisplayName", "").lower()
        else:
            condition = str(condition).lower()
        
        if "new" in condition or condition_id in ["1000", "1500"]:
            return Condition.NEW
        elif "refurbished" in condition or "renewed" in condition or condition_id in ["2000", "2010", "2020", "2030"]:
            return Condition.REFURBISHED
        elif condition_id in ["3000", "4000", "5000", "6000", "7000"]:
            return Condition.USED
        elif "used" in condition or "pre-owned" in condition:
            return Condition.USED
        
        return None
    
    def _parse_price(self, item: dict[str, Any]) -> tuple[float, float | None, float]:
        """Parse price, shipping, and total from eBay item."""
        price_info = item.get("price", {})
        price = float(price_info.get("value", 0))
        
        shipping_info = item.get("shippingOptions", [{}])
        if shipping_info:
            shipping_cost_info = shipping_info[0].get("shippingCost", {})
            shipping = float(shipping_cost_info.get("value", 0))
        else:
            shipping = None
        
        total = price + (shipping if shipping else 0)
        return price, shipping, total
    
    def _parse_seller(self, item: dict[str, Any]) -> tuple[float | None, int | None]:
        """Parse seller rating and feedback count."""
        seller = item.get("seller", {})
        
        feedback_percentage = seller.get("feedbackPercentage")
        rating = float(feedback_percentage) if feedback_percentage else None
        
        feedback_score = seller.get("feedbackScore")
        count = int(feedback_score) if feedback_score else None
        
        return rating, count
    
    def _parse_eta(self, item: dict[str, Any]) -> tuple[int | None, int | None]:
        """Parse estimated delivery days."""
        shipping_options = item.get("shippingOptions", [])
        if not shipping_options:
            return None, None
        
        shipping = shipping_options[0]
        min_days = shipping.get("minEstimatedDeliveryDays")
        max_days = shipping.get("maxEstimatedDeliveryDays")
        
        return (
            int(min_days) if min_days else None,
            int(max_days) if max_days else None
        )
    
    def _parse_returns(self, item: dict[str, Any]) -> int | None:
        """Parse return window days."""
        returns = item.get("returnTerms", {})
        period = returns.get("returnPeriod", {})
        value = period.get("value")
        unit = period.get("unit", "").upper()
        
        if value and unit == "DAY":
            return int(value)
        elif value and unit == "MONTH":
            return int(value) * 30
        
        return None
    
    def _parse_specs(self, item: dict[str, Any], category: str) -> dict[str, Any]:
        """Extract category-specific specs from item."""
        specs: dict[str, Any] = {}
        title = item.get("title", "").lower()
        
        if category == "headphones":
            specs["wireless"] = any(w in title for w in ["wireless", "bluetooth"])
            specs["noise_canceling"] = any(w in title for w in [
                "noise cancel", "noise-cancel", "anc", "active noise"
            ])
            specs["over_ear"] = "over-ear" in title or "over ear" in title
            specs["in_ear"] = "in-ear" in title or "earbud" in title
            
            # Try to extract brand
            title_parts = item.get("title", "").split()
            if title_parts:
                specs["brand"] = title_parts[0]
                
        elif category == "monitors":
            # Would need to parse from title or aspects
            specs["size_inches"] = None
            specs["resolution"] = None
            
        return specs
    
    def _normalize_listing(
        self, 
        item: dict[str, Any], 
        category: str
    ) -> NormalizedListing:
        """Convert eBay item to NormalizedListing."""
        price, shipping, total = self._parse_price(item)
        seller_rating, feedback_count = self._parse_seller(item)
        eta_min, eta_max = self._parse_eta(item)
        
        return NormalizedListing(
            id=item.get("itemId", ""),
            source=Source.EBAY,
            title=item.get("title", "Unknown Item"),
            url=item.get("itemWebUrl", ""),
            image_url=item.get("image", {}).get("imageUrl"),
            price=price,
            shipping_cost=shipping,
            total_cost=total,
            condition=self._parse_condition(item),
            eta_min_days=eta_min,
            eta_max_days=eta_max,
            return_window_days=self._parse_returns(item),
            seller_rating=seller_rating,
            seller_feedback_count=feedback_count,
            warranty_months=None,  # eBay items rarely have warranty info
            specs=self._parse_specs(item, category),
            raw={
                "itemId": item.get("itemId"),
                "condition": item.get("condition"),
                "seller": item.get("seller"),
            }
        )
    
    async def search(
        self,
        query: str,
        category: str,
        max_results: int = 25
    ) -> list[NormalizedListing]:
        """Search eBay Browse API."""
        token = await self._get_access_token()
        if not token:
            return []
        
        # Check cache first
        cache_params = {"query": query, "category": category, "max": max_results}
        cached = self.cache.get("ebay_search", cache_params)
        if cached:
            return [NormalizedListing(**item) for item in cached]
        
        category_id = self.CATEGORY_IDS.get(category.lower())
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }
        
        params = {
            "q": query,
            "limit": min(max_results, 50),
            "filter": "buyingOptions:{FIXED_PRICE}",  # Exclude auctions for consistent pricing
        }
        
        if category_id:
            params["category_ids"] = category_id
        
        url = f"{self.BROWSE_API_URL}/item_summary/search"
        
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            
            items = data.get("itemSummaries", [])
            listings = [
                self._normalize_listing(item, category) 
                for item in items[:max_results]
            ]
            
            # Cache results
            self.cache.set(
                "ebay_search", 
                cache_params, 
                [l.model_dump() for l in listings]
            )
            
            return listings
            
        except httpx.HTTPError as e:
            print(f"eBay API error: {e}")
            return []
    
    async def get_details(self, product_id: str) -> NormalizedListing | None:
        """Fetch detailed item information."""
        token = await self._get_access_token()
        if not token:
            return None
        
        # Check cache
        cache_params = {"item_id": product_id}
        cached = self.cache.get("ebay_detail", cache_params)
        if cached:
            return NormalizedListing(**cached)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }
        
        url = f"{self.BROWSE_API_URL}/item/{product_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                item = response.json()
            
            listing = self._normalize_listing(item, "headphones")
            
            # Cache result
            self.cache.set("ebay_detail", cache_params, listing.model_dump())
            
            return listing
            
        except httpx.HTTPError as e:
            print(f"eBay API error: {e}")
            return None
