import React, { useState, useEffect } from 'react';
import { 
  Wind, 
  Activity, 
  AlertTriangle, 
  TrendingDown, 
  TrendingUp, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  Info,
  Zap,
  BarChart3,
  Layers
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area
} from 'recharts';

export default function App() {
  const [selectedDate, setSelectedDate] = useState('2026-01-02');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quick select dates in Jan 2026
  const sampleDates = [
    '2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', 
    '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-10', 
    '2026-01-15', '2026-01-20', '2026-01-25', '2026-01-31'
  ];

  const fetchData = async (date) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/wind/day-ahead?date=${date}`);
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}: ${res.statusText}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to fetch wind data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(selectedDate);
  }, [selectedDate]);

  const metrics = data?.metrics;
  const dataPoints = data?.data_points || [];

  // Format chart time
  const formattedChartData = dataPoints.map(dp => ({
    ...dp,
    timeLabel: dp.timestamp.substring(11, 16),
    shortfall: dp.error_mw < 0 ? Math.abs(dp.error_mw) : 0,
    surplus: dp.error_mw > 0 ? dp.error_mw : 0,
  }));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
              <Wind className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">UK Wind Grid Insights</h1>
                <span className="text-xs bg-cyan-950 text-cyan-400 border border-cyan-800/60 px-2 py-0.5 rounded-full font-medium">
                  Day-Ahead Market
                </span>
              </div>
              <p className="text-xs text-slate-400">Elexon BMRS Generation Forecast vs Actual Outturn Validation</p>
            </div>
          </div>

          {/* Date Picker Bar */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-1.5 text-sm">
              <Calendar className="w-4 h-4 text-slate-400" />
              <label htmlFor="date-select" className="text-slate-400 text-xs">Delivery Date:</label>
              <select
                id="date-select"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                {sampleDates.map(d => (
                  <option key={d} value={d} className="bg-slate-900 text-white">{d}</option>
                ))}
              </select>
            </div>

            {data && (
              <div className="hidden lg:flex items-center gap-1.5 text-xs bg-slate-800/50 border border-slate-700/60 px-3 py-1.5 rounded-lg text-slate-300">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span>Gate Closure:</span>
                <span className="font-mono text-amber-300 font-semibold">{data.gate_closure_time}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto w-full px-6 py-6 flex-1 space-y-6">
        {loading && (
          <div className="flex items-center justify-center p-24 text-slate-400 gap-3">
            <Activity className="w-6 h-6 animate-spin text-cyan-400" />
            <span>Fetching live Elexon datasets and calculating metrics...</span>
          </div>
        )}

        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-xl flex items-center gap-3 text-rose-300">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
            <div>
              <div className="font-semibold text-sm">Unable to load data</div>
              <div className="text-xs opacity-80">{error}</div>
            </div>
          </div>
        )}

        {!loading && !error && metrics && (
          <>
            {/* KPI Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* MAE */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Mean Absolute Error (MAE)</span>
                  <Activity className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-2xl font-bold text-white tracking-tight">
                  {metrics.mae_mw.toLocaleString()} <span className="text-xs font-normal text-slate-400">MW</span>
                </div>
                <div className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                  <span>RMSE:</span>
                  <span className="font-mono text-slate-300 font-semibold">{metrics.rmse_mw.toLocaleString()} MW</span>
                </div>
              </div>

              {/* Mean Bias Error (MBE) */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Forecast Bias (MBE)</span>
                  {metrics.mbe_mw < 0 ? (
                    <TrendingDown className="w-4 h-4 text-rose-400" />
                  ) : (
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  )}
                </div>
                <div className="text-2xl font-bold text-white tracking-tight flex items-baseline gap-2">
                  <span>{metrics.mbe_mw > 0 ? `+${metrics.mbe_mw}` : metrics.mbe_mw}</span>
                  <span className="text-xs font-normal text-slate-400">MW</span>
                </div>
                <div className="text-xs mt-2">
                  {metrics.mbe_mw < 0 ? (
                    <span className="text-rose-400 font-medium">Over-forecasted (Shortfall Risk)</span>
                  ) : (
                    <span className="text-emerald-400 font-medium">Under-forecasted (Surplus)</span>
                  )}
                </div>
              </div>

              {/* Net Shortfall Energy */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Backup Power Required</span>
                  <Zap className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-2xl font-bold text-amber-400 tracking-tight">
                  {metrics.net_shortfall_mwh.toLocaleString()} <span className="text-xs font-normal text-slate-400">MWh</span>
                </div>
                <div className="text-xs text-slate-400 mt-2">
                  Volume needed from thermal/reserve plants
                </div>
              </div>

              {/* Total Generation Outturn */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Total Delivery Outturn</span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-white tracking-tight">
                  {metrics.total_actual_mwh.toLocaleString()} <span className="text-xs font-normal text-slate-400">MWh</span>
                </div>
                <div className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                  <span>Forecast was:</span>
                  <span className="font-mono text-slate-300 font-semibold">{metrics.total_forecast_mwh.toLocaleString()} MWh</span>
                </div>
              </div>
            </div>

            {/* Trading Decision Advisory Banner */}
            <div className={`p-4 rounded-xl border flex items-start gap-3 ${
              metrics.mbe_mw < -1000 
                ? 'bg-amber-950/30 border-amber-800/50 text-amber-200' 
                : 'bg-cyan-950/30 border-cyan-800/50 text-cyan-200'
            }`}>
              <Info className="w-5 h-5 flex-shrink-0 mt-0.5 text-cyan-400" />
              <div className="text-xs sm:text-sm leading-relaxed">
                <strong className="font-semibold text-white">Procurement Advisory for {selectedDate}: </strong> 
                {metrics.mbe_mw < 0 ? (
                  <>
                    Wind forecast consistently exceeded actual delivery by an average of <span className="font-bold underline text-amber-300">{Math.abs(metrics.mbe_mw)} MW</span>. 
                    Power traders relying purely on raw forecasts would have faced a cumulative shortfall of <span className="font-bold text-white">{metrics.net_shortfall_mwh.toLocaleString()} MWh</span>. 
                    <strong> Recommendation:</strong> Apply a negative risk buffer of ~15% to day-ahead wind bids and pre-procure flexible thermal/CCGT capacity.
                  </>
                ) : (
                  <>
                    Actual wind output met or exceeded day-ahead forecast expectations with positive surplus of <span className="font-bold text-emerald-300">{metrics.net_surplus_mwh.toLocaleString()} MWh</span>. 
                    Low thermal dispatch required.
                  </>
                )}
              </div>
            </div>

            {/* Main Interactive Chart: Actual vs Forecast */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <h2 className="text-base font-semibold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-cyan-400" />
                    Hourly Day-Ahead Wind Forecast vs Actual Outturn (MW)
                  </h2>
                  <p className="text-xs text-slate-400">Comparing WINDFOR (published before Day-Ahead gate closure) vs FUELHH actuals</p>
                </div>
              </div>

              <div className="h-80 w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={formattedChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.25}/>
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0}/>
                      </linearGradient>
                      <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.25}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} tickFormatter={(val) => `${val / 1000}k`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                      labelFormatter={(label) => `Time: ${label} UTC`}
                      formatter={(val, name) => [`${Number(val).toLocaleString()} MW`, name]}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                    <Area type="monotone" dataKey="forecast_mw" name="Day-Ahead Forecast (MW)" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#forecastGrad)" />
                    <Line type="monotone" dataKey="actual_mw" name="Actual Outturn (MW)" stroke="#10b981" strokeWidth={2.5} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Error Delta Chart: Shortfall vs Surplus */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-amber-400" />
                    Quantified Forecast Error Distribution (Actual − Forecast)
                  </h2>
                  <p className="text-xs text-slate-400">Negative values indicate unserved energy shortfall; positive values indicate wind surplus</p>
                </div>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={formattedChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} tickFormatter={(val) => `${val} MW`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                      formatter={(val) => [`${Number(val).toLocaleString()} MW`, 'Error Delta']}
                    />
                    <Bar dataKey="error_mw" name="Error (Actual − Forecast)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Detailed Table */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">Settlement Period Breakdown</h3>
                <span className="text-xs text-slate-400">24 Hourly Periods</span>
              </div>
              <div className="overflow-x-auto max-h-72">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-800/60 text-slate-300 uppercase sticky top-0 font-medium">
                    <tr>
                      <th className="py-2.5 px-4">Time (UTC)</th>
                      <th className="py-2.5 px-4">Settlement Period</th>
                      <th className="py-2.5 px-4">Forecast (MW)</th>
                      <th className="py-2.5 px-4">Actual (MW)</th>
                      <th className="py-2.5 px-4">Error Delta</th>
                      <th className="py-2.5 px-4">Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {formattedChartData.map((dp) => (
                      <tr key={dp.timestamp} className="hover:bg-slate-800/40">
                        <td className="py-2 px-4 font-mono text-slate-300">{dp.timeLabel}</td>
                        <td className="py-2 px-4 text-slate-400">{dp.settlement_period} – {dp.settlement_period + 1}</td>
                        <td className="py-2 px-4 font-mono text-cyan-400">{dp.forecast_mw.toLocaleString()}</td>
                        <td className="py-2 px-4 font-mono text-emerald-400">{dp.actual_mw.toLocaleString()}</td>
                        <td className={`py-2 px-4 font-mono font-semibold ${dp.error_mw < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {dp.error_mw > 0 ? `+${dp.error_mw}` : dp.error_mw} MW
                        </td>
                        <td className="py-2 px-4">
                          {dp.error_mw < 0 ? (
                            <span className="bg-rose-950/60 border border-rose-800/60 text-rose-300 px-2 py-0.5 rounded text-[10px]">
                              Shortfall (-{Math.abs(dp.error_mw)} MW)
                            </span>
                          ) : (
                            <span className="bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 px-2 py-0.5 rounded text-[10px]">
                              Surplus (+{dp.error_mw} MW)
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 px-6 py-4 text-xs text-slate-500 text-center">
        UK Wholesale Electricity Day-Ahead Wind Forecasting Engine • Built with FastAPI, React, Tailwind & Elexon BMRS API
      </footer>
    </div>
  );
}
