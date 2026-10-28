from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DataPoint(BaseModel):
    timestamp: str  # ISO string, e.g. "2026-01-02T14:00:00Z"
    settlement_period: Optional[int] = None
    forecast_mw: float
    actual_mw: float
    error_mw: float  # actual - forecast (negative = shortfall, positive = surplus)
    abs_error_mw: float

class DailyMetrics(BaseModel):
    date: str
    mae_mw: float  # Mean Absolute Error
    rmse_mw: float  # Root Mean Squared Error
    mbe_mw: float  # Mean Bias Error (avg of actual - forecast)
    mape_percent: Optional[float] = None
    total_forecast_mwh: float
    total_actual_mwh: float
    net_shortfall_mwh: float  # Total deficit when actual < forecast
    net_surplus_mwh: float    # Total excess when actual > forecast
    peak_forecast_mw: float
    peak_actual_mw: float

class DayAheadResponse(BaseModel):
    delivery_date: str
    gate_closure_time: str
    metrics: DailyMetrics
    data_points: List[DataPoint]

class MonthlySummaryItem(BaseModel):
    date: str
    mae_mw: float
    rmse_mw: float
    mbe_mw: float
    total_actual_mwh: float
    total_forecast_mwh: float

class MonthlyOverviewResponse(BaseModel):
    month: str
    days_count: int
    overall_mae_mw: float
    overall_rmse_mw: float
    overall_mbe_mw: float
    total_actual_mwh: float
    total_forecast_mwh: float
    days: List[MonthlySummaryItem]
