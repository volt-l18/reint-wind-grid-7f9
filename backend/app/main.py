import os
import calendar
from typing import Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .models import DayAheadResponse, MonthlyOverviewResponse, MonthlySummaryItem
from .processing import processor

app = FastAPI(
    title="UK Wind Power Day-Ahead Forecasting & Grid Balancing API",
    description="API for evaluating UK day-ahead wind generation forecasts against actual settlement outturns (Elexon BMRS data for Jan 2026).",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "uk-wind-forecast-api"}

@app.get("/api/wind/day-ahead", response_model=DayAheadResponse)
async def get_day_ahead_analysis(
    date: str = Query(..., description="Target delivery date in YYYY-MM-DD format (e.g. 2026-01-02)")
):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    try:
        result = await processor.process_day_ahead(date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing day-ahead data: {str(e)}")

@app.get("/api/wind/overview", response_model=MonthlyOverviewResponse)
async def get_monthly_overview(
    month: str = Query("2026-01", description="Target month in YYYY-MM format")
):
    try:
        year, month_num = map(int, month.split("-"))
        _, num_days = calendar.monthrange(year, month_num)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Expected YYYY-MM.")

    days_summary = []
    total_mae = 0.0
    total_rmse = 0.0
    total_mbe = 0.0
    total_actual = 0.0
    total_forecast = 0.0
    valid_days = 0

    for day in range(1, num_days + 1):
        date_str = f"{year:04d}-{month_num:02d}-{day:02d}"
        try:
            day_res = await processor.process_day_ahead(date_str)
            m = day_res.metrics
            days_summary.append(MonthlySummaryItem(
                date=date_str,
                mae_mw=m.mae_mw,
                rmse_mw=m.rmse_mw,
                mbe_mw=m.mbe_mw,
                total_actual_mwh=m.total_actual_mwh,
                total_forecast_mwh=m.total_forecast_mwh
            ))
            total_mae += m.mae_mw
            total_rmse += m.rmse_mw
            total_mbe += m.mbe_mw
            total_actual += m.total_actual_mwh
            total_forecast += m.total_forecast_mwh
            valid_days += 1
        except Exception:
            continue

    n = valid_days if valid_days > 0 else 1
    return MonthlyOverviewResponse(
        month=month,
        days_count=valid_days,
        overall_mae_mw=round(total_mae / n, 1),
        overall_rmse_mw=round(total_rmse / n, 1),
        overall_mbe_mw=round(total_mbe / n, 1),
        total_actual_mwh=round(total_actual, 1),
        total_forecast_mwh=round(total_forecast, 1),
        days=days_summary
    )

# Static file serving if frontend/dist is built (allows single-origin all-in-one deployment)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path in ("health", "docs", "openapi.json", "redoc"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
