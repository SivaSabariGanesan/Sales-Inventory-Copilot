TRACK_ID=PS6
# Retail Sales & Inventory Copilot

An intelligent, production-ready retail decision-support system designed to detect stock-out risks, overstocked and slow-moving inventory, sales velocity anomalies, provide evidence-backed action recommendations, and deliver a grounded natural-language Copilot interface for store managers.

---

## 1. Problem Statement (PS03)

Retail store managers must constantly balance inventory turnover against stock depletion. Traditional dashboards either present overwhelming raw numbers without actionability or rely on ungrounded AI models that hallucinate metrics.

Managers need immediate, reliable answers to critical operational questions:
- *Which products are at risk of running out before replenishment?*
- *Where are we holding excess inventory that isn't moving?*
- *Which products recently experienced sudden sales spikes or drops?*
- *What specific action should I take today, and what numerical evidence supports it?*

---

## 2. Solution Architecture

The **Retail Sales & Inventory Copilot** enforces a strict separation between **language understanding** and **business truth**:
- **Python & SQLite**: The authoritative, deterministic source of truth for all metric calculations, days-of-stock estimates, anomaly classifications, and recommendation rules.
- **Google Gemini**: Used exclusively for natural-language intent understanding and grounded explanation synthesis. Gemini **never** calculates numbers, invents data, or executes unvalidated operations.

```
┌─────────────────────────────────────────────────────────┐
│              Single-Page React Application              │
│       Executive Dashboard · Copilot · Analytics UI       │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / JSON
┌────────────────────────────▼────────────────────────────┐
│                  FastAPI Backend Server                 │
│                 (Single Process Port 8000)              │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
┌──────────────▼──────────────┐  ┌─────────▼──────────────┐
│    Deterministic Engine     │  │   Gemini Copilot Layer  │
│  - Stock-Out Detection (F1) │  │  - Intent Understanding │
│  - Overstock Analysis (F2)  │  │  - Grounded Explanation │
│  - Velocity Anomalies (F3)  │  │  - Pre-Validation Guard │
│  - Recommendation Engine(F5)│  │  - Safe Refusals (F6)   │
└──────────────┬──────────────┘  └─────────┬──────────────┘
               │                           │
┌──────────────▼──────────────┐            │
│       SQLite Database       │            │
│  (Foreign Keys & Seed Data) │            │
└─────────────────────────────┘  ┌─────────▼──────────────┐
                                 │   Google Gemini API    │
                                 │   (HTTPS, Auth via Key)│
                                 └────────────────────────┘
```

---

## 3. Implemented Capabilities & Features

1. **Feature 1 — Stock-Out Risk Detection**:
   - Deterministic demand velocity estimation over 14 calendar days.
   - Classification into `HIGH` ($\le 3$ days of stock) and `MEDIUM` ($3-7$ days of stock) risks.
   - Exact numerical evidence for every alert.

2. **Feature 2 — Overstock & Slow-Moving Inventory**:
   - 30-day demand lookback identifying `SEVERE_OVERSTOCK` ($> 60$ days), `OVERSTOCK` ($> 30$ days), and `SLOW_MOVING` ($\le 1.0$ units/day).
   - Dedicated `NO_RECENT_DEMAND` state for positive stock with 0 recent sales.

3. **Feature 3 — Sales Velocity Spikes & Drops**:
   - Non-overlapping comparison between recent 7-day demand and prior 30-day baseline.
   - Detection of `SPIKE` ($\ge +50\%$) and `DROP` ($\le -40\%$) with minimum baseline reliability guard ($2.0$ units/day).

4. **Feature 4 — Gemini Natural-Language Copilot**:
   - Conversational question answering mapped to deterministic SQLite queries.
   - Grounded responses displaying exact numerical evidence, insights, and time windows.

5. **Feature 5 — Action Recommendations**:
   - Rule-based decision engine converting conditions into concrete actions (`REPLENISH_NOW`, `PLAN_REPLENISHMENT`, `REDUCE_FUTURE_REPLENISHMENT`, `INVESTIGATE_SALES_DECLINE`).
   - Precedence ordering and multi-condition deduplication.

6. **Feature 6 — Insufficient Data, Refusal & Human Escalation**:
   - Explicit state machine (`ANSWERED`, `INSUFFICIENT_DATA`, `AMBIGUOUS`, `UNSUPPORTED`, `NOT_FOUND`, `HUMAN_REVIEW`).
   - Safe refusal of predictive forecasting and exact purchase sizing without supplier MOQs.
   - Entity disambiguation with interactive clarification choices.

7. **Feature 7 — Consolidated Executive Dashboard**:
   - Unified overview answering *"What needs my attention today?"*.
   - Filterable by store and category with real-time scope indicators.
   - Inventory health distribution, sales velocity extrema, and multi-store comparison matrix.

---

## 4. Quick Start & Execution (Judge Ready)

The entire application runs as a unified service from a single terminal with **no Node.js/npm dependencies required at runtime**.

### Prerequisites
- Python 3.11+
- Git

### Single-Command Launch
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start application
python app.py
```

Open your browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

---

## 5. Environment & Configuration

Create an optional `.env` file in the root directory (or set environment variables):

```env
# Optional: Google Gemini API Key for Natural Language Copilot
GEMINI_API_KEY=your_gemini_api_key_here

# Optional Server Settings (Defaults to 0.0.0.0:8000)
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

> **Offline / Keyless Operation:**
> If `GEMINI_API_KEY` is not provided, the application starts normally and all analytics, dashboard views, inventory calculations, and recommendations function seamlessly. The Copilot layer utilizes deterministic rule-based grounding for offline evaluation.

---

## 6. Dataset Structure

The database `data/retail.db` contains a realistic, lightweight synthetic retail dataset:
- **4 Retail Stores:** Chennai Central, Anna Nagar, Velachery, T. Nagar.
- **90 Catalog Products:** Electronics, Accessories, Home & Office, Audio, Peripherals.
- **39,943 Sales Records:** Continuous 180-day transaction history with natural seasonalities.
- **360 Multi-Store Inventory Records:** Realistic stock levels reflecting all alert scenarios.

---

## 7. API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | `GET` | Health check and SQLite connectivity status |
| `/api/dashboard/summary` | `GET` | Consolidated executive metrics, attention items, and store matrix |
| `/api/inventory/stockout-risks` | `GET` | Filtered list of products facing imminent stock-out |
| `/api/inventory/overstock` | `GET` | Filtered list of overstocked and slow-moving items |
| `/api/sales/anomalies` | `GET` | Detected 7d vs 30d sales velocity spikes and drops |
| `/api/recommendations` | `GET` | Prioritized, deduplicated business action recommendations |
| `/api/recommendations/today` | `GET` | Top high-priority actionable items for executive review |
| `/api/copilot/query` | `POST` | Natural-language query endpoint with grounded evidence |

---

## 8. Automated Testing

Run the full pytest test suite covering all services, APIs, refusal guards, and end-to-end smoke tests:

```powershell
# Run full test suite
python -m pytest
```

---

## 9. Stated Limitations

- **Forecasting Scope:** Predictive machine learning forecasting for future years is outside current scope.
- **Supplier Constraints:** Exact replenishment purchase order sizing requires supplier lead time and MOQ contracts not present in the transaction dataset; these queries are safely escalated to manager review (`HUMAN_REVIEW`).