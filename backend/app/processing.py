import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from .models import DataPoint, DailyMetrics, DayAheadResponse
from .elexon_client import elexon_client
from .config import Config

class DataProcessor:
    @staticmethod
    def get_gate_closure(delivery_date_str: str) -> datetime:
        """
        UK Day-Ahead market gate closure is typically 12:00 PM (noon) on D-1.
        """
        delivery_dt = datetime.strptime(delivery_date_str, "%Y-%m-%d")
        d_minus_one = delivery_dt - timedelta(days=1)
        return d_minus_one.replace(hour=Config.GATE_CLOSURE_HOUR, minute=0, second=0)

    @classmethod
    async def process_day_ahead(cls, delivery_date_str: str) -> DayAheadResponse:
        gate_closure = cls.get_gate_closure(delivery_date_str)
        gate_closure_str = gate_closure.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Fetch actuals for delivery date D
        actuals_raw = await elexon_client.get_actual_generation(delivery_date_str)

        # 2. Fetch forecasts published in window prior to gate closure
        # (Looking back 36 hours before gate closure to ensure we catch all latest published forecasts)
        window_start = (gate_closure - timedelta(hours=36)).strftime("%Y-%m-%dT%H:%M:%SZ")
        forecasts_raw = await elexon_client.get_forecasts(window_start, gate_closure_str)

        # 3. Filter latest forecast for each target hour on delivery date D published <= gate_closure
        latest_forecasts: Dict[str, float] = {}
        for f in forecasts_raw:
            st = f.get("startTime", "")
            pub = f.get("publishTime", "")
            if st.startswith(delivery_date_str) and pub <= gate_closure_str:
                if st not in latest_forecasts or pub > latest_forecasts[st]["publishTime"]:
                    latest_forecasts[st] = {
                        "generation": float(f.get("generation", 0)),
                        "publishTime": pub
                    }

        # 4. Group actuals by hour (average MW of 30-min settlement periods in that hour)
        actuals_by_hour: Dict[str, List[float]] = {}
        for a in actuals_raw:
            st = a.get("startTime", "")
            if st.startswith(delivery_date_str):
                # Standardize to hour: "YYYY-MM-DDTHH:00:00Z"
                hour_key = st[:13] + ":00:00Z"
                actuals_by_hour.setdefault(hour_key, []).append(float(a.get("generation", 0)))

        # 5. Build combined data points
        data_points: List[DataPoint] = []
        all_errors: List[float] = []
        all_sq_errors: List[float] = []
        pct_errors: List[float] = []

        total_fc_mwh = 0.0
        total_act_mwh = 0.0
        net_shortfall_mwh = 0.0
        net_surplus_mwh = 0.0
        peak_fc = 0.0
        peak_act = 0.0

        for hour_int in range(24):
            hour_str = f"{delivery_date_str}T{hour_int:02d}:00:00Z"
            fc_info = latest_forecasts.get(hour_str)
            fc_val = fc_info["generation"] if fc_info else 0.0

            act_list = actuals_by_hour.get(hour_str, [])
            act_val = sum(act_list) / len(act_list) if act_list else 0.0

            error = act_val - fc_val  # negative = shortfall, positive = surplus
            abs_err = abs(error)

            all_errors.append(error)
            all_sq_errors.append(error ** 2)
            if act_val > 0:
                pct_errors.append((abs_err / act_val) * 100)

            total_fc_mwh += fc_val * 1.0  # 1 hour block
            total_act_mwh += act_val * 1.0

            if error < 0:
                net_shortfall_mwh += abs(error) * 1.0
            else:
                net_surplus_mwh += error * 1.0

            peak_fc = max(peak_fc, fc_val)
            peak_act = max(peak_act, act_val)

            data_points.append(DataPoint(
                timestamp=hour_str,
                settlement_period=(hour_int * 2) + 1,
                forecast_mw=round(fc_val, 1),
                actual_mw=round(act_val, 1),
                error_mw=round(error, 1),
                abs_error_mw=round(abs_err, 1)
            ))

        n = len(all_errors) if all_errors else 1
        mae = sum(abs(e) for e in all_errors) / n
        rmse = math.sqrt(sum(all_sq_errors) / n)
        mbe = sum(all_errors) / n
        mape = (sum(pct_errors) / len(pct_errors)) if pct_errors else None

        metrics = DailyMetrics(
            date=delivery_date_str,
            mae_mw=round(mae, 1),
            rmse_mw=round(rmse, 1),
            mbe_mw=round(mbe, 1),
            mape_percent=round(mape, 1) if mape is not None else None,
            total_forecast_mwh=round(total_fc_mwh, 1),
            total_actual_mwh=round(total_act_mwh, 1),
            net_shortfall_mwh=round(net_shortfall_mwh, 1),
            net_surplus_mwh=round(net_surplus_mwh, 1),
            peak_forecast_mw=round(peak_fc, 1),
            peak_actual_mw=round(peak_act, 1)
        )

        return DayAheadResponse(
            delivery_date=delivery_date_str,
            gate_closure_time=gate_closure_str,
            metrics=metrics,
            data_points=data_points
        )

processor = DataProcessor()
