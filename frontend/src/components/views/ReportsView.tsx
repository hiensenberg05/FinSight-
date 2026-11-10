import React, { useState, useEffect } from 'react';
import { Download, Calendar, CheckCircle2 } from 'lucide-react';
import { PremiumCard } from '../common/PremiumCard';
import { api } from '../../services/api';
import { CategorySpending, FinancialHealthMetrics } from '../../types';
import { formatINR } from '../../utils/formatters';

export const ReportsView: React.FC = () => {
  const [selectedReport, setSelectedReport] = useState<'monthly' | 'quarterly' | 'tax'>('monthly');
  const [categories, setCategories] = useState<CategorySpending[]>([]);
  const [metrics, setMetrics] = useState<FinancialHealthMetrics | null>(null);

  useEffect(() => {
    api.getCategorySpending().then(setCategories);
    api.getHealthMetrics().then(setMetrics);
  }, []);

  const downloadReport = (format: string) => {
    alert(`Downloading FinSight ${selectedReport.toUpperCase()} Financial Report (${format})...`);
  };

  const totalSpent = categories.reduce((sum, c) => sum + c.amount, 0);

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Top Banner - Glossy Apple 3D Surface */}
      <PremiumCard className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold text-violet-400 uppercase tracking-widest block mb-1">
            Financial Intelligence Reports
          </span>
          <h2 className="text-[22px] font-extrabold text-metallic-silver tracking-tight">
            Financial Summaries & Statements
          </h2>
          <p className="text-[12.5px] text-[#8E8AA5] mt-0.5">
            Audit-ready statement reconciliations, tax readiness & spending variance logs from PostgreSQL
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadReport('PDF')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-b from-violet-600/40 via-violet-700/50 to-indigo-900/60 border-t border-white/[0.25] border-b border-black/50 text-white text-[12.5px] font-bold shadow-[0_2px_10px_rgba(0,0,0,0.5),0_0_12px_rgba(139,92,246,0.3)] hover:brightness-110 active:scale-95 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-violet-300" />
            <span>Download PDF</span>
          </button>
          <button
            onClick={() => downloadReport('CSV')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl glass-card-3d border border-white/[0.1] text-[#8E8AA5] hover:text-white text-[12.5px] font-bold transition-all active:scale-95"
          >
            <span>CSV</span>
          </button>
        </div>
      </PremiumCard>

      {/* Report Type Selector Tabs */}
      <div className="glass-inset-tray p-1.5 rounded-2xl flex items-center gap-1.5 w-fit border border-white/[0.04]">
        <button
          onClick={() => setSelectedReport('monthly')}
          className={`px-4 py-1.5 rounded-xl text-[12px] font-bold transition-all ${
            selectedReport === 'monthly'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white'
          }`}
        >
          Monthly Summary
        </button>
        <button
          onClick={() => setSelectedReport('quarterly')}
          className={`px-4 py-1.5 rounded-xl text-[12px] font-medium transition-all ${
            selectedReport === 'quarterly'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white'
          }`}
        >
          Quarterly Variance
        </button>
        <button
          onClick={() => setSelectedReport('tax')}
          className={`px-4 py-1.5 rounded-xl text-[12px] font-medium transition-all ${
            selectedReport === 'tax'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white'
          }`}
        >
          Tax Preparation
        </button>
      </div>

      {/* Statement Audit Card */}
      <PremiumCard className="p-6">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-600/30 border border-violet-400/40 text-violet-200 flex items-center justify-center shadow-md">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-[17px] font-extrabold text-white tracking-tight">Statement Audit & Reconciliation</h3>
              <p className="text-[12px] text-[#8E8AA5]">Statement period: November 2026 · Account: HDFC Primary & SBI Secondary</p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[12px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-3 py-1.5 rounded-xl font-bold shadow-sm">
            <CheckCircle2 className="w-4 h-4" />
            <span>100% Reconciled</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          <div className="glass-card-3d border border-white/[0.08] p-4 rounded-xl shadow-md">
            <span className="text-[11.5px] text-[#8E8AA5] block font-medium">Available Balance</span>
            <span className="text-[22px] tabular-nums font-extrabold text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]">
              {formatINR(metrics?.availableBalance || 102756)}
            </span>
          </div>
          <div className="glass-card-3d border border-white/[0.08] p-4 rounded-xl shadow-md">
            <span className="text-[11.5px] text-[#8E8AA5] block font-medium">Operating Expenses</span>
            <span className="text-[22px] tabular-nums font-extrabold text-metallic-silver">
              {formatINR(totalSpent || 48320)}
            </span>
          </div>
          <div className="glass-card-3d border border-white/[0.08] p-4 rounded-xl shadow-md">
            <span className="text-[11.5px] text-[#8E8AA5] block font-medium">Monthly Savings</span>
            <span className="text-[22px] tabular-nums font-extrabold text-metallic-violet">
              {formatINR(metrics?.monthlySavings || 18650)}
            </span>
          </div>
        </div>

        <h4 className="text-[12px] font-extrabold text-metallic-silver uppercase tracking-wider mb-2.5">Category Line Items from Database</h4>
        <div className="space-y-2 text-xs">
          {categories.map((c) => (
            <div key={c.name} className="flex items-center justify-between py-2.5 px-3 rounded-xl glass-card-3d border border-white/[0.04] hover:border-white/[0.12] transition-all">
              <span className="text-white font-semibold text-[13px]">{c.name}</span>
              <div className="flex items-center gap-4">
                <span className="text-[#8E8AA5] tabular-nums font-medium">{c.percentage}%</span>
                <span className="tabular-nums font-extrabold text-metallic-silver text-[13.5px]">{formatINR(c.amount)}</span>
              </div>
            </div>
          ))}
        </div>
      </PremiumCard>
    </div>
  );
};
