"""
FastAPI application for Agentic Buyer decision engine.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import DecisionSpec, RecommendationResponse
from .services import Recommender


# Initialize FastAPI app
app = FastAPI(
    title="Agentic Buyer API",
    description="Deterministic decision engine for electronics purchases",
    version="1.0.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommender
recommender = Recommender()


# ============================================================================
# Health & Info Endpoints
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str


class CategoryInfo(BaseModel):
    id: str
    name: str
    description: str


class CategoriesResponse(BaseModel):
    categories: list[CategoryInfo]


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.get("/api/categories", response_model=CategoriesResponse)
async def get_categories():
    """Get available product categories."""
    return CategoriesResponse(
        categories=[
            CategoryInfo(
                id="headphones",
                name="Headphones",
                description="Over-ear, on-ear, and in-ear headphones including wireless and noise-canceling options"
            ),
            CategoryInfo(
                id="monitors",
                name="Monitors",
                description="Computer monitors including gaming, professional, and ultrawide options"
            ),
        ]
    )


# ============================================================================
# Recommendation Endpoint
# ============================================================================

class RecommendationRequest(BaseModel):
    """Request body for recommendations endpoint."""
    category: str = "headphones"
    query: str
    budget_max: float
    condition_allowed: list[str] = ["new", "refurb"]
    delivery_priority: str = "medium"
    risk_tolerance: str = "low"
    weights: dict[str, float] = {
        "price": 0.25,
        "delivery": 0.20,
        "reliability": 0.25,
        "warranty": 0.15,
        "spec_match": 0.15,
    }
    user_location_zip: str | None = None


@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get product recommendations based on user preferences.
    
    Returns top 3 recommendations (Overall, Value, Low Risk) with:
    - Score breakdowns for each dimension
    - Explanations for why each was picked
    - Sensitivity analysis showing decision stability
    """
    try:
        # Convert request to DecisionSpec
        from .models import WeightConfig, DeliveryPriority, RiskTolerance
        
        spec = DecisionSpec(
            category=request.category,
            query=request.query,
            budget_max=request.budget_max,
            condition_allowed=request.condition_allowed,
            delivery_priority=DeliveryPriority(request.delivery_priority),
            risk_tolerance=RiskTolerance(request.risk_tolerance),
            weights=WeightConfig(**request.weights),
            user_location_zip=request.user_location_zip,
        )
        
        # Get recommendations
        response = await recommender.get_recommendations(spec)
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
