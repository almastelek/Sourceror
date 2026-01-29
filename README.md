# 🎯 Agentic Buyer (Electronics)

A **deterministic decision engine** that recommends the best electronics purchases using **Best Buy** and **eBay APIs**. Built as a resume-ready, demo-friendly MVP.

![Tech Stack](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-blue)
![Tech Stack](https://img.shields.io/badge/Frontend-Next.js%20%7C%20TypeScript%20%7C%20Tailwind-cyan)
![Tech Stack](https://img.shields.io/badge/Caching-Redis-red)

## ✨ Features

- **Top 3 Recommendations**:
  - 🏆 **Best Overall** — optimized for your custom weights
  - 💎 **Best Value** — price-weighted alternative
  - 🛡️ **Lowest Risk** — reliability/warranty-weighted alternative

- **Multi-dimensional Scoring**:
  - Price, Delivery Speed, Seller Reliability, Warranty, Spec Match
  - Transparent score breakdowns for each recommendation

- **Sensitivity Analysis**:
  - Weight sweep: shows when preference changes would flip the winner
  - Budget relaxation: shows what becomes available with +$50/+$100

- **Real-time Data**: Fetches live listings from Best Buy and eBay APIs

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional, falls back gracefully)
- API keys (see below)

### 1. Get API Keys

| Service | Get Key | Notes |
|---------|---------|-------|
| Best Buy | [developer.bestbuy.com](https://developer.bestbuy.com/) | Free tier available |
| eBay | [developer.ebay.com](https://developer.ebay.com/) | OAuth app required |

### 2. Setup Environment

```bash
# Clone and enter project
cd Sourceror

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# BESTBUY_API_KEY=your_key
# EBAY_CLIENT_ID=your_id
# EBAY_CLIENT_SECRET=your_secret
```

### 3. Start Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### 5. Open App

Navigate to [http://localhost:3000](http://localhost:3000)

## 🐳 Docker (Alternative)

```bash
# Start all services
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

## 📚 API Reference

### `GET /api/health`
Health check endpoint.

```json
{ "status": "healthy", "version": "1.0.0" }
```

### `GET /api/categories`
List available product categories.

```json
{
  "categories": [
    { "id": "headphones", "name": "Headphones", "description": "..." }
  ]
}
```

### `POST /api/recommendations`
Get product recommendations.

**Request:**
```json
{
  "category": "headphones",
  "query": "noise cancelling wireless headphones",
  "budget_max": 250,
  "condition_allowed": ["new", "refurb"],
  "delivery_priority": "medium",
  "risk_tolerance": "low",
  "weights": {
    "price": 0.25,
    "delivery": 0.20,
    "reliability": 0.25,
    "warranty": 0.15,
    "spec_match": 0.15
  }
}
```

**Response:**
```json
{
  "decision_spec": { ... },
  "top3": [
    {
      "label": "overall",
      "listing": {
        "id": "bb-123",
        "source": "bestbuy",
        "title": "Sony WH-1000XM5",
        "price": 248.00,
        "total_cost": 248.00,
        "condition": "new",
        "eta_max_days": 4,
        "seller_rating": 98.0,
        "warranty_months": 12
      },
      "scores": {
        "price": 0.72,
        "delivery": 0.85,
        "reliability": 0.92,
        "warranty": 0.80,
        "spec_match": 0.90
      },
      "total_score": 0.83,
      "why": [
        "Competitive price at $248.00",
        "Best Buy's trusted retail experience",
        "12-month warranty included"
      ],
      "tradeoff": "May not match all preferences"
    }
  ],
  "sensitivity": {
    "stability": "high",
    "switch_conditions": [],
    "budget_relaxation": [
      {
        "budget": 300,
        "new_winner_id": null,
        "message": "With +$50 budget, the recommendation stays the same"
      }
    ]
  },
  "debug": {
    "candidates_considered": 42,
    "candidates_after_filter": 18,
    "sources_used": ["bestbuy", "ebay"],
    "errors": []
  }
}
```

## 🧪 Running Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_scoring.py -v
```

## 📁 Project Structure

```
Sourceror/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI endpoints
│   │   ├── models.py         # Pydantic models
│   │   ├── config.py         # Settings
│   │   ├── cache.py          # Redis caching
│   │   ├── connectors/       # API connectors
│   │   │   ├── bestbuy.py
│   │   │   └── ebay.py
│   │   └── services/         # Business logic
│   │       ├── scoring.py    # Scoring engine
│   │       ├── sensitivity.py
│   │       └── recommender.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/page.tsx      # Main page
│       ├── components/       # UI components
│       ├── lib/api.ts        # API client
│       └── types/            # TypeScript types
├── docker-compose.yml
└── .env.example
```

## 🔧 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│  Best Buy   │
│   Frontend  │     │   Backend    │     │    API      │
└─────────────┘     │              │     └─────────────┘
                    │  ┌────────┐  │
                    │  │ Redis  │  │     ┌─────────────┐
                    │  │ Cache  │  │────▶│   eBay      │
                    │  └────────┘  │     │    API      │
                    └──────────────┘     └─────────────┘
```

**Data Flow:**
1. User submits preferences → Frontend
2. Frontend calls `/api/recommendations` → Backend
3. Backend fetches from Best Buy + eBay (with caching)
4. Scoring engine ranks candidates deterministically
5. Sensitivity analyzer checks decision stability
6. Results returned with explanations

## 📝 Resume Bullet

> **Agentic Buyer** — Built a deterministic decision engine for electronics purchases, aggregating real-time data from Best Buy and eBay APIs. Implemented multi-dimensional scoring (price, delivery, reliability, warranty, spec-match), sensitivity analysis (weight sweeps, budget relaxation), and a React/Next.js frontend rendering top-3 recommendations with explainable score breakdowns. Stack: Python/FastAPI, TypeScript/Next.js, Redis caching.

## 📄 License

MIT License - feel free to use this project for learning and portfolio purposes.
