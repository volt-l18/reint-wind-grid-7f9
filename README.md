# UK Wind Grid — Day-Ahead Forecasting & Procurement Advisory System

> **Product Demo & Technical Challenge Submission**  
> **Client:** UK Electricity Utility — Wholesale Power Trading Desk  
> **Domain:** UK Day-Ahead Electricity Market (EPEX SPOT / Nord Pool)  
> **Evaluation Period:** January 2026  
> **Data Provider:** Elexon BMRS (Balancing Mechanism Reporting Service)  

---

## 1. Executive Summary & Problem Setting

Electricity utilities in the UK must balance consumer demand against intermittent renewable energy. In the wholesale **Day-Ahead Market**, power purchase decisions for delivery day $D$ are finalized on day $D-1$ before gate closure (12:00 PM UTC).

Because wind power is weather-dependent:
1. **Under-forecasting (Surplus):** Actual wind is higher than forecasted. Excess power may lead to balancing penalties or curtailment.
2. **Over-forecasting (Shortfall):** Actual wind is lower than forecasted. The utility faces an immediate deficit and is forced to procure costly reserve thermal/gas (CCGT) power in the balancing mechanism.

This application provides the trading desk with:
* Real-time visibility into the **latest wind forecast available prior to day-ahead gate closure** for any settlement date in January 2026.
* **Quantitative forecast accuracy evaluation:** Hourly and daily metrics including Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Bias Error (MBE).
* **Net Shortfall & Backup Volume:** Quantifies total MWh of unserved energy requiring thermal dispatch.

---

## 2. System Architecture

```
                       ┌──────────────────────────────┐
                       │   Elexon BMRS Public APIs    │
                       └──────────────┬───────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
 ┌──────────────────────┐                            ┌──────────────────────┐
 │ Actuals: FUELHH      │                            │ Forecasts: WINDFOR   │
 │ Target: 'startTime'  │                            │ Target: 'startTime'  │
 │ Filter: 'WIND'       │                            │ Filter: 'publishTime'│
 └──────────┬───────────┘                            └──────────┬───────────┘
            │                                                   │
            └─────────────────────────┬─────────────────────────┘
                                      ▼
                       ┌──────────────────────────────┐
                       │   FastAPI Backend Engine     │
                       │   • Gate Closure Filter      │
                       │   • SQLite Fast Cache        │
                       │   • Error & Metrics Compute  │
                       └──────────────┬───────────────┘
                                      ▼  REST API (/api/wind/*)
                       ┌──────────────────────────────┐
                       │   React + Tailwind Dashboard │
                       │   • Interactive Time Series  │
                       │   • Shortfall Error Delta    │
                       │   • Trading Advisory Banner  │
                       └──────────────────────────────┘
```

---

## 3. Directory Layout

```
uk-wind-forecast/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application, CORS, and route definitions
│   │   ├── config.py            # Environment configuration and Elexon base URLs
│   │   ├── models.py            # Pydantic schemas for data points and metrics
│   │   ├── elexon_client.py     # Async HTTP client for BMRS FUELHH & WINDFOR streams
│   │   ├── processing.py        # Day-ahead gate closure alignment & metric calculations
│   │   └── cache.py             # SQLite caching layer for instantaneous responses
│   ├── data/                    # Persistent cache storage
│   ├── Dockerfile               # Production container definition for FastAPI
│   ├── requirements.txt         # Python dependencies
│   └── venv/                    # Local Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main interactive trading desk dashboard
│   │   ├── main.jsx             # React DOM mounting
│   │   └── index.css            # Tailwind styles & dark mode palette
│   ├── package.json             # NPM dependencies (React 19, Recharts, Lucide)
│   ├── vite.config.js           # Vite configuration with API proxy
│   ├── tailwind.config.js       # Custom grid colors and theme
│   └── Dockerfile               # Multi-stage production container with Nginx
├── docker-compose.yml           # Single-command orchestration for entire stack
└── README.md                    # Project documentation & pitch guide
```

---

## 4. How to Run

### Option A: Using Docker Compose (Recommended)
Ensure Docker is installed and running:
```bash
docker compose up --build
```
* **Frontend:** Open `http://localhost:5173`
* **Backend API Docs (Swagger):** Open `http://localhost:8000/docs`

---

### Option B: Running Locally

#### 1. Backend:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. The Vite proxy will automatically route `/api/*` calls to the FastAPI backend at port 8000.

---

## 5. Mathematical Metrics & Formulas

For $N = 24$ hourly settlement windows across delivery date $D$:
* **Forecast Error:** 
  $$\text{Error}_t = \text{Actual}_t - \text{Forecast}_t$$
* **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{N} \sum_{t=1}^{N} |\text{Actual}_t - \text{Forecast}_t|$$
* **Mean Bias Error (MBE / Directional Bias):**
  $$\text{MBE} = \frac{1}{N} \sum_{t=1}^{N} (\text{Actual}_t - \text{Forecast}_t)$$
  * $\text{MBE} < 0$: Systematic over-forecasting (Shortfall risk).
  * $\text{MBE} > 0$: Systematic under-forecasting (Surplus wind).
* **Backup Power Required (Shortfall Volume):**
  $$\text{Shortfall (MWh)} = \sum_{t \in \text{deficit}} |\text{Error}_t| \times 1\text{ hour}$$

---

## 6. Video Presentation Guide (Max 10 Minutes)

### Part 1: Client Pitch (Max 5 mins)
* **Audience:** UK Utility Power Trading Lead.
* **Talking Points:**
  1. *The Challenge:* Why day-ahead procurement decisions carry severe financial risk when wind generation forecasts deviate from reality.
  2. *Live Walkthrough:* Show the interactive dashboard for **January 2, 2026**. Point out that the forecast predicted ~18,500 MW, but actual outturn was ~15,000 MW (over-forecasted by ~3,000 MW).
  3. *Business Impact:* Show the **Backup Power Required** KPI (`79,004 MWh`). Explain that without this dashboard, the desk would face unexpected balancing mechanism penalty prices.
  4. *The Advisory Banner:* Explain how the automated advisory provides actionable bidding buffers.

### Part 2: Technical Lead Walkthrough (Max 5 mins)
* **Audience:** Internal Engineering Lead.
* **Talking Points:**
  1. *Architecture:* Clean separation between React frontend (Vite/Tailwind/Recharts) and Python FastAPI backend.
  2. *Elexon API Integration:* Explain the use of `/datasets/FUELHH/stream` (settlement actuals) and `/datasets/WINDFOR/stream` (forecasts).
  3. *Gate Closure Logic:* Explain how the backend strictly enforces that only forecasts published **before 12:00 PM on D-1** are evaluated.
  4. *Performance & Caching:* Explain the SQLite caching layer ensuring sub-10ms response times on repeated date queries.
  5. *Containerization:* Demonstrate `docker-compose.yml` for reproducible zero-config deployments.

---

## 7. AI Disclosure

In accordance with the challenge guidelines, AI coding assistants (Google Antigravity CLI) were utilized to accelerate boilerplate generation, API parameter inspection, and schema design.
