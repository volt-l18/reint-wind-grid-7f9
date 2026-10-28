from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, timedelta
import calendar
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
        # Validate format
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

    # Limit to first 7 days for quick overview or all days
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
