import React from 'react';
import { Wallet, Activity, TrendingUp, AlertCircle, ArrowUpRight, ArrowDownRight, Target } from 'lucide-react';

interface SculptedCardProps {
  type: 'liquidity' | 'expenses' | 'portfolio';
  onAction?: () => void;
}

export const SculptedCard: React.FC<SculptedCardProps> = ({ type, onAction }) => {
  if (type === 'liquidity') {
    return (
      <div 
        onClick={onAction}
        className="relative overflow-hidden rounded-xl bg-[#111018] border border-white/[0.08] hover:border-violet-500/40 p-4 transition-all duration-200 shadow-sm group cursor-pointer flex flex-col justify-between"
      >
        {/* Top header row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-violet-500/15 border border-violet-500/30 flex items-center justify-center text-violet-400">
              <Wallet className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-semibold text-[#8E8B9A] tracking-tight">
              Total Liquidity
            </span>
          </div>
          <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
            <ArrowUpRight className="w-2.5 h-2.5" />
            <span>Healthy</span>
          </span>
        </div>

        {/* Big metric */}
        <div className="my-3">
          <div className="text-2xl font-bold font-mono text-white tracking-tight tabular-numbers">
            ₹1,24,500
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-400 mt-1">
            <span>+₹18,650</span>
            <span className="text-[11px] text-[#5C596C] font-normal">net inflow this month</span>
          </div>
        </div>

        {/* Sculpted inner plate */}
        <div className="rounded-lg bg-[#181628] border border-violet-500/20 p-2.5 flex items-center justify-between text-[11px]">
          <div>
            <span className="text-[#8E8B9A] block leading-tight">HDFC Everyday</span>
            <span className="font-mono font-bold text-white tabular-numbers leading-tight mt-0.5 block">
              ₹98,250
            </span>
          </div>
          <div className="text-right">
            <span className="text-[#8E8B9A] block leading-tight">ICICI Savings</span>
            <span className="font-mono font-bold text-white tabular-numbers leading-tight mt-0.5 block">
              ₹26,250
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (type === 'expenses') {
    return (
      <div 
        onClick={onAction}
        className="relative overflow-hidden rounded-xl bg-[#111018] border border-white/[0.08] hover:border-amber-500/40 p-4 transition-all duration-200 shadow-sm group cursor-pointer flex flex-col justify-between"
      >
        {/* Top header row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Activity className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-semibold text-[#8E8B9A] tracking-tight">
              Monthly Outflows
            </span>
          </div>
          <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
            <AlertCircle className="w-2.5 h-2.5" />
            <span>63% used</span>
          </span>
        </div>

        {/* Big metric */}
        <div className="my-3">
          <div className="text-2xl font-bold font-mono text-white tracking-tight tabular-numbers">
            ₹53,500
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-amber-400/90 mt-1">
            <span>42 UPI debits</span>
            <span className="text-[11px] text-[#5C596C] font-normal">₹18,450 discretionary</span>
          </div>
        </div>

        {/* Sculpted inner plate */}
        <div className="rounded-lg bg-[#1D1714] border border-amber-500/20 p-2.5 flex items-center justify-between text-[11px]">
          <div>
            <span className="text-[#A3988F] block leading-tight">Food & Dining</span>
            <span className="font-mono font-bold text-amber-300 tabular-numbers leading-tight mt-0.5 block">
              ₹14,200 <span className="text-[9px] text-rose-400 font-sans font-normal">(+28%)</span>
            </span>
          </div>
          <div className="text-right">
            <span className="text-[#A3988F] block leading-tight">Fixed Utilities</span>
            <span className="font-mono font-bold text-white tabular-numbers leading-tight mt-0.5 block">
              ₹8,500
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Portfolio & Goals
  return (
    <div 
      onClick={onAction}
      className="relative overflow-hidden rounded-xl bg-[#111018] border border-white/[0.08] hover:border-cyan-500/40 p-4 transition-all duration-200 shadow-sm group cursor-pointer flex flex-col justify-between"
    >
      {/* Top header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <TrendingUp className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold text-[#8E8B9A] tracking-tight">
            Portfolio & Goals
          </span>
        </div>
        <span className="text-[10px] font-semibold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
          <Target className="w-2.5 h-2.5" />
          <span>67% on track</span>
        </span>
      </div>

      {/* Big metric */}
      <div className="my-3">
        <div className="text-2xl font-bold font-mono text-white tracking-tight tabular-numbers">
          ₹2,34,920
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-cyan-400 mt-1">
          <span>+12.4% ARR</span>
          <span className="text-[11px] text-[#5C596C] font-normal">Nifty 50 Index + SGB</span>
        </div>
      </div>

      {/* Sculpted inner plate */}
      <div className="rounded-lg bg-[#0E1924] border border-cyan-500/20 p-2.5 flex items-center justify-between text-[11px]">
        <div>
          <span className="text-[#87A4B8] block leading-tight">Vacation Goal</span>
          <span className="font-mono font-bold text-cyan-300 tabular-numbers leading-tight mt-0.5 block">
            ₹1,20,000 / ₹1.5L
          </span>
        </div>
        <div className="text-right">
          <span className="text-[#87A4B8] block leading-tight">Emergency Fund</span>
          <span className="font-mono font-bold text-white tabular-numbers leading-tight mt-0.5 block">
            ₹1,14,920
          </span>
        </div>
      </div>
    </div>
  );
};
