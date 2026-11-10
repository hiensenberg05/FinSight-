import React from 'react';
import { FinancialHealthMetrics } from '../../types';
import { Calendar } from 'lucide-react';

interface QuickOverviewCardProps {
  metrics: FinancialHealthMetrics;
}

export const QuickOverviewCard: React.FC<QuickOverviewCardProps> = ({ metrics }) => {
  return (
    <div className="bg-[#0E1322] border border-slate-700/60 border-t-white/10 rounded-2xl p-5 shadow-panel ring-1 ring-inset ring-white/[0.04] transition-all duration-300 hover:border-purple-500/40">
      {/* Header with Title and Period Pill */}
      <div className="flex items-center justify-between mb-3.5">
        <h3 className="text-xs font-semibold text-slate-100 tracking-wide">
          Quick Overview
        </h3>
        <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#141A2D] border border-slate-700/60 border-t-white/10 text-slate-200 shadow-sm">
          <Calendar className="w-3 h-3 text-purple-400" />
          <span>{metrics.period}</span>
        </div>
      </div>

      {/* Segmented Horizontal Progress / Balance Bar (from reference) */}
      <div className="w-full h-1.5 bg-slate-800/90 rounded-full overflow-hidden flex mb-3.5 shadow-inner">
        <div className="h-full bg-purple-500 w-[55%]" title="Living Expenses (55%)" />
        <div className="h-full bg-cyan-400 w-[25%]" title="Savings & Investments (25%)" />
        <div className="h-full bg-pink-500 w-[12%]" title="Discretionary (12%)" />
        <div className="h-full bg-amber-400 w-[8%]" title="Pending Bills (8%)" />
      </div>

      {/* 3 Metric Columns with Divider Lines */}
      <div className="grid grid-cols-3 gap-2 pt-1.5 border-t border-slate-800/70">
        {/* Available Balance */}
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-400 truncate font-medium">
            Available Balance
          </span>
          <span className="text-xs sm:text-sm font-extrabold text-white font-mono mt-0.5 truncate tracking-tight">
            ₹{metrics.availableBalance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </span>
        </div>

        {/* Monthly Savings */}
        <div className="flex flex-col border-l border-slate-800/90 pl-2">
          <span className="text-[10px] text-slate-400 truncate font-medium">
            Monthly Savings
          </span>
          <span className="text-xs sm:text-sm font-extrabold text-cyan-400 font-mono mt-0.5 truncate tracking-tight">
            +₹{metrics.monthlySavings.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </span>
        </div>

        {/* Pending Bills */}
        <div className="flex flex-col border-l border-slate-800/90 pl-2">
          <span className="text-[10px] text-slate-400 truncate font-medium">
            Pending Bills
          </span>
          <span className="text-xs sm:text-sm font-extrabold text-amber-400 font-mono mt-0.5 truncate tracking-tight">
            ₹{metrics.pendingBills.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </span>
        </div>
      </div>
    </div>
  );
};
