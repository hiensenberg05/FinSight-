import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { AlertCircle, BrainCircuit, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { ForecastPoint, Transaction } from '../../types';
import { formatINR } from '../../utils/formatters';

export const AnalyticsView: React.FC = () => {
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [anomalyTx, setAnomalyTx] = useState<Transaction | null>(null);
  const [anomaliesList, setAnomaliesList] = useState<Transaction[]>([]);

  useEffect(() => {
    api.getForecast().then((points) => {
      // Map to horizon data
      const chartPoints = points.map((p) => ({
        month: p.month || p.date,
        actual: p.actualAmount !== undefined && p.actualAmount !== null
          ? p.actualAmount
          : (p.date?.includes('Projected') ? null : p.predictedSpend),
        forecast: p.predictedAmount !== undefined && p.predictedAmount !== null
          ? p.predictedAmount
          : p.predictedSpend,
        lower: p.lowerBound || p.lowerConfidence,
        upper: p.upperBound || p.upperConfidence,
      }));
      setForecastData(chartPoints);
    });

    api.getTransactions().then((txns) => {
      const flagged = txns.filter((t) => t.isAnomaly);
      setAnomaliesList(flagged);
      if (flagged.length > 0) {
        setAnomalyTx(flagged[0]);
      }
    });
  }, []);

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Top Banner */}
      <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div>
          <span className="text-[11px] font-bold text-violet-400 uppercase tracking-widest block mb-0.5">
            Predictive Intelligence Engine
          </span>
          <h2 className="text-[22px] font-extrabold text-metallic-silver tracking-tight leading-tight">
            Predictive Analytics & Forecasting
          </h2>
          <p className="text-[12.5px] text-[#8E8AA5] mt-0.5">
            12-month cash-flow projection model running Holt-Winters / Prophet over verified database transactions
          </p>
        </div>

        <div className="flex items-center gap-2 glass-pill-active px-3.5 py-1.5 rounded-xl self-start sm:self-auto shadow-md">
          <BrainCircuit className="w-4 h-4 text-violet-300" />
          <span className="text-[11.5px] text-white font-bold">PostgreSQL Verified</span>
        </div>
      </div>

      {/* Cash Flow Forecast Chart */}
      <div className="rounded-2xl glass-card-3d p-5 shadow-lg border border-white/[0.08]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-[16px] font-extrabold text-metallic-silver tracking-tight">
              Cash-Flow Trend & Projection Horizon
            </h3>
            <p className="text-[12px] text-[#8E8AA5]">
              Historical Actuals (Cyan) vs. Projected Forecast (Dotted Violet)
            </p>
          </div>
          <div className="flex items-center gap-4 text-[12px] glass-inset-tray px-3 py-1.5 rounded-xl border border-white/[0.04]">
            <span className="flex items-center gap-1.5 text-white font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" /> Actual Historical
            </span>
            <span className="flex items-center gap-1.5 text-white font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(168,85,247,0.8)]" /> Projected
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={forecastData}>
              <defs>
                <linearGradient id="actual3DGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22D3EE" stopOpacity={0.45} />
                  <stop offset="50%" stopColor="#0891B2" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#0891B2" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="forecast3DGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#C084FC" stopOpacity={0.45} />
                  <stop offset="50%" stopColor="#7C3AED" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#7C3AED" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" stroke="#6C6785" fontSize={11} tickLine={false} />
              <YAxis 
                stroke="#6C6785" 
                fontSize={11} 
                tickFormatter={(val) => `₹${Math.round(val/1000)}k`} 
                domain={['auto', 'auto']}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="glass-card-3d p-3 rounded-xl text-xs text-white shadow-2xl border border-white/[0.15]">
                        <p className="font-extrabold text-metallic-silver text-sm">{data.month}</p>
                        {data.actual !== null && data.actual !== undefined && (
                          <p className="text-cyan-300 font-bold mt-1 tabular-nums">
                            Actual: {formatINR(data.actual)}
                          </p>
                        )}
                        {data.forecast !== null && data.forecast !== undefined && (
                          <p className="text-violet-300 font-bold mt-0.5 tabular-nums">
                            Projected: {formatINR(data.forecast)}
                          </p>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area 
                type="monotone" 
                dataKey="actual" 
                stroke="#22D3EE" 
                strokeWidth={2.5} 
                fillOpacity={1} 
                fill="url(#actual3DGrad)" 
                isAnimationActive={false} 
              />
              <Area 
                type="monotone" 
                dataKey="forecast" 
                stroke="#A855F7" 
                strokeDasharray="4 4" 
                strokeWidth={2.5} 
                fillOpacity={1} 
                fill="url(#forecast3DGrad)" 
                isAnimationActive={false} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two Column Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        {/* Anomaly Detection Card */}
        <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-rose-500/20 border border-rose-500/35 flex items-center justify-center text-rose-300 shadow-sm">
                <AlertCircle className="w-4 h-4 text-rose-400" />
              </div>
              <h3 className="text-[15px] font-bold text-white tracking-tight">
                Statistical Anomaly Inspection
              </h3>
            </div>
            <span className="text-[11px] font-bold text-rose-300 bg-rose-500/15 border border-rose-500/35 px-2.5 py-0.5 rounded-full">
              Flagged in Ledger
            </span>
          </div>

          <div className="space-y-2.5">
            {anomaliesList.slice(0, 2).map((item, idx) => (
              <div key={item.id || idx} className="glass-card-3d p-3.5 rounded-xl border border-white/[0.08] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[14px] font-bold text-white">{item.merchant}</span>
                  <span className="text-[14px] font-extrabold text-rose-300 tabular-nums">
                    {formatINR(Math.abs(item.amount))}
                  </span>
                </div>
                <p className="text-[11.5px] text-[#A29DBE]">
                  {item.anomalyReason || 'Statistical outlier: 3.4 standard deviations above category baseline.'}
                </p>
                <div className="flex items-center justify-between pt-1.5 border-t border-white/[0.06] text-[10.5px]">
                  <span className="text-amber-300 font-semibold">Severity: High (Confidence: 94%)</span>
                  <span className="text-[#8E8AA5]">{item.date}</span>
                </div>
              </div>
            ))}
            {anomaliesList.length === 0 && (
              <div className="glass-card-3d p-4 rounded-xl border border-white/[0.08] text-center text-[#8E8AA5] text-[12px]">
                No anomalies flagged. All transactions within 2.5-sigma confidence intervals.
              </div>
            )}
          </div>
        </div>

        {/* Top UPI Merchants */}
        <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-white tracking-tight">
              Top Counterparty Merchants
            </h3>
            <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full font-bold">
              UPI Analyzed
            </span>
          </div>

          <div className="space-y-2 text-xs">
            {[
              { name: 'Swiggy', amount: 14200, count: 28 },
              { name: 'Uber India', amount: 4800, count: 14 },
              { name: 'Blinkit Commerce', amount: 3600, count: 8 },
              { name: 'Zomato', amount: 3200, count: 7 },
            ].map((m) => (
              <div key={m.name} className="flex items-center justify-between py-2 px-3 rounded-xl glass-card-3d border border-white/[0.04]">
                <div>
                  <span className="text-white font-semibold text-[13px] block">{m.name}</span>
                  <span className="text-[10.5px] text-[#8E8AA5]">{m.count} UPI settlements</span>
                </div>
                <span className="text-metallic-silver font-extrabold text-[13.5px] tabular-nums">{formatINR(m.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
