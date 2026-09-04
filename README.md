TRACK_ID=PS03
# Retail Sales & Inventory Copilot

An intelligent, production-ready retail decision-support system designed to detect stock-out risks, overstocked and slow-moving inventory, sales velocity anomalies, provide evidence-backed action recommendations, deliver a grounded natural-language Copilot interface for store managers, and offer a full-featured executive web portal with full AI Governance & Auditability.

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
- **Python & SQLite**: The authoritative, deterministic source of truth for all metric calculations, days-of-stock estimates, anomaly classifications, master catalogs, recommendation rules, audit trails, and versioned application cache.
- **Google Gemini 2.5 Flash**: Used exclusively for natural-language intent understanding and grounded explanation synthesis. Gemini **never** calculates numbers, invents data, or executes unvalidated operations.

```
┌───────────────────────────────────────────────────────────────────┐
│                    Single-Page React Application                  │
│   Landing Page (/landing) · Executive Dashboard (/) · Copilot     │
│   Inventory · Sales · Products Catalog · Stores Network · Import  │
│   AI Audit Trail (/audit) · Settings & AI Configuration           │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ HTTP / JSON
┌─────────────────────────────────▼─────────────────────────────────┐
│                       FastAPI Backend Server                      │
│                  (Single Process Port 8000 / Vercel)              │
│                                                                   │
│  ┌───────────────────────┐             ┌───────────────────────┐  │
│  │   Deterministic Logic │             │  Audit & Governance   │  │
│  │   - Stockout Engine   │             │  - Non-blocking Logs  │  │
│  │   - Overstock Engine  │             │  - Flow Step Tracing  │  │
│  │   - Sales Anomalies   │             │  - Data Versioning    │  │
│  │   - CSV Ingestion     │             │  - Token Telemetry    │  │
│  └───────────┬───────────┘             └───────────┬───────────┘  │
│              │                                     │              │
│  ┌───────────▼───────────┐             ┌───────────▼───────────┐  │
│  │   SQLite Retail DB    │             │ Safe Prompt Caching   │  │
│  │   (data/retail.db)    │◄────────────┤ SHA-256 Key Cache     │  │
│  └───────────┬───────────┘             └───────────────────────┘  │
│              │ Evidence Object                                    │
│  ┌───────────▼─────────────────────────────────────────────────┐  │
│  │            Google Gemini 2.5 Flash Interface                │  │
│  │     - Intent Classification (extract filters)               │  │
│  │     - Grounded Explanation Synthesis (strictly bound)       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Features

### A. Stock-Out Risk Detection
- **Calculations:** 30-day rolling daily sales velocity ($V_{30}$), Days of Stock ($\text{DoS} = \text{Current Stock} / V_{30}$).
- **Categorization:** `HIGH_RISK` ($\text{DoS} \le 7$ days), `MEDIUM_RISK` ($7 < \text{DoS} \le 14$ days), `HEALTHY` ($\text{DoS} > 14$ days).

### B. Overstock & Slow-Moving Detection
- **Categorization:** `SEVERE_OVERSTOCK` ($\text{DoS} \ge 90$ days), `OVERSTOCK` ($60 \le \text{DoS} < 90$ days), `NO_RECENT_DEMAND` ($\ge 30$ days of zero sales despite active stock), `SLOW_MOVING` ($\text{DoS} \ge 45$ days).

### C. Sales Velocity Anomaly Detection
- Compares 7-day velocity ($V_7$) to 30-day baseline ($V_{30}$) using percentage ratio $\Delta = ((V_7 - V_{30}) / V_{30}) \times 100\%$.
- **Spike:** $\ge +50\%$ increase.
- **Drop:** $\le -40\%$ decrease.

### D. Retail Value & Revenue Analytics
- **Deterministic Valuation Source of Truth:** Python & SQLite exclusively compute inventory holding valuations and sales revenue figures with zero AI financial hallucinations.
- **Inventory Holding Value:** Calculated deterministically as $\text{Current Stock Quantity} \times \text{Product Unit Price}$ per SKU, store, category, and catalog-wide.
- **Sales Revenue:** Computed from authoritative recorded transaction revenue with fallback to $\text{Quantity} \times \text{Unit Price}$.
- **Overstock Capital Analysis:** Evaluates capital tied up in slow-moving, no-demand, and excess stock by reusing verified `OverstockService` classifications.
- **Value Copilot Intents:** Dedicated NLP intents (`INVENTORY_VALUE`, `REVENUE_SUMMARY`, `OVERSTOCK_VALUE`, `STORE_VALUE_ANALYSIS`, `PRODUCT_VALUE_ANALYSIS`, `CATEGORY_VALUE_ANALYSIS`) grounded in verified numerical evidence records.

### E. AI Auditability, Governance & Prompt Caching
- **Non-blocking Audit Trail:** Every Copilot query records timestamp, normalized question, classified intent, confidence, status, cache hit, verified token counts, prompt version, model, data version, and step-by-step execution timeline.
- **Data-Versioned Prompt & Application Cache:** Responses are securely cached in SQLite indexed by a deterministic SHA-256 key (`prompt_version:model:normalized_question:data_version`). Zero live API calls or tokens are incurred on identical repeat queries.
- **Automatic Cache Invalidation on Mutation:** Ingesting new data or resetting demo data increments the system `data_version`, immediately invalidating stale cache entries while strictly preserving historical audit logs.
- **Zero-Fabrication Token Telemetry:** Aggregates real prompt and completion tokens from Gemini API responses; cost transparency explicitly displays `"Cost unavailable"` when live billing APIs are disconnected rather than fabricating monetary figures.
- **Privacy & Security Guarantee:** Zero API keys, passwords, or raw secrets are stored in database logs or caches.

### F. Data Import Engine
- Interactive CSV validation and ingestion supporting individual datasets (`products`, `stores`, `sales`, `inventory`) or unified `all.csv`.
- Non-destructive previews with column validation, data type checks, and foreign key constraint verification before commit.

---

## 4. Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Installation & Run

1. **Clone repository & enter directory:**
   ```bash
   git clone <repo-url>
   cd "Sales & Inventory Copilot"
   ```

2. **Backend Setup:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Application:**
   ```bash
   python app.py
   # Or using Python launcher on Windows:
   py app.py
   ```
   The backend API and static frontend will be running at `http://localhost:8000`.

---

## 5. API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | `GET` | Health check and SQLite connectivity status |
| `/api/analytics/value` | `GET` | Deterministic financial analytics: inventory value, sales revenue, overstock capital |
| `/api/dashboard/summary` | `GET` | Consolidated executive metrics, attention items, and store matrix |
| `/api/inventory` | `GET` | Complete inventory stock records with unit price and inventory values |
| `/api/inventory/stockout-risks` | `GET` | Filtered list of products facing imminent stock-out with valuation |
| `/api/inventory/overstock` | `GET` | Filtered list of overstocked and slow-moving items with tied-up capital |
| `/api/sales/anomalies` | `GET` | Detected 7d vs 30d sales velocity spikes and drops |
| `/api/recommendations` | `GET` | Prioritized, deduplicated business action recommendations |
| `/api/recommendations/today` | `GET` | Top high-priority actionable items for executive review |
| `/api/copilot/query` | `POST` | Natural-language query endpoint with grounded evidence |
| `/api/products` | `GET` | Searchable master product catalog with category filters |
| `/api/stores` | `GET` | Physical store network with inventory rollups and KPIs |
| `/api/audit` | `GET` | Paginated, filterable Copilot audit logs |
| `/api/audit/{id}` | `GET` | Deep execution trace, step breakdown, and grounded evidence |
| `/api/usage` | `GET` | Gemini API token telemetry, cache hit efficiency, and cost transparency |
| `/api/settings/gemini` | `GET` | Masked Gemini API key status preview |
| `/api/settings/gemini` | `POST` | Secure backend Gemini API key configuration |
| `/api/settings/gemini/test` | `POST` | Minimal live Google Gemini endpoint connection test |
| `/api/import/status` | `GET` | Live entity counts across products, stores, sales, and inventory |
| `/api/import/preview` | `POST` | Non-destructive CSV validation and preview for single dataset |
| `/api/import/preview-all` | `POST` | Non-destructive validation and preview for combined `all.csv` |
| `/api/import/{dataset}` | `POST` | Atomic CSV ingestion for `products`, `stores`, `sales`, or `inventory` |
| `/api/import/all` | `POST` | Multi-dataset atomic commit from `all.csv` |
| `/api/import/templates/{name}` | `GET` | Download standard starter CSV templates |
| `/api/import/reset-demo` | `POST` | Reset database back to baseline seeded synthetic dataset |

---

## 6. Automated Testing

Run the full pytest test suite covering all services, value analytics, refusal guards, settings security, data import validation, audit governance, prompt caching, and end-to-end smoke tests:

```bash
# Run full test suite (103 tests)
python -m pytest -v
```

---

## 7. Stated Limitations

- **Forecasting Scope:** Predictive machine learning forecasting for multi-year horizons is outside current operational decision-support scope.
- **Supplier Constraints:** Exact replenishment purchase order sizing requires supplier lead time and MOQ contracts not present in store POS datasets; these queries are safely escalated to manager review (`HUMAN_REVIEW`).