import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sliders, Sparkles, TrendingUp, Calendar, Zap } from 'lucide-react';
import { SimulationData } from '../../types';

interface InteractiveSimulationCardProps {
  initialData: SimulationData;
  onSliderChange?: (category: string, pct: number) => void;
}

export const InteractiveSimulationCard: React.FC<InteractiveSimulationCardProps> = ({
  initialData,
  onSliderChange,
}) => {
  const [sliderPct, setSliderPct] = useState<number>(initialData.reduction_percentage || 20);

  // Deterministic live client-side recalculation matching backend logic exactly
  const baseSpend = initialData.historical_monthly_spend || 14200;
  const monthlySavings = Math.round(baseSpend * (sliderPct / 100));
  const annualizedSavings = Math.round(monthlySavings * 12);
  const simulatedSpend = Math.round(baseSpend - monthlySavings);

  // Vacation goal acceleration calculation
  const goalRemaining = initialData.goal_impact?.remaining_amount || 24000;
  const baseMonthlyContribution = 18650;
  const newMonthlyContribution = baseMonthlyContribution + monthlySavings;
  const baselineMonths = +(goalRemaining / baseMonthlyContribution).toFixed(1);
  const acceleratedMonths = +(goalRemaining / newMonthlyContribution).toFixed(1);
  const monthsSaved = Math.max(0, +(baselineMonths - acceleratedMonths).toFixed(1));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setSliderPct(val);
    onSliderChange?.(initialData.category, val);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className="w-full my-3 bg-[#12182B] border border-purple-500/30 rounded-2xl p-4 shadow-panel backdrop-blur-md"
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-700/50">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-purple-600/30 border border-purple-400/40 flex items-center justify-center text-purple-300">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-white">
              Predictive Advisory: What-If Simulator
            </h3>
            <span className="text-[10px] text-purple-300 font-mono">
              Deterministic Discretionary Modeling
            </span>
          </div>
        </div>

        <span className="text-xs font-bold font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-400/30">
          {sliderPct}% Cut
        </span>
      </div>

      {/* Interactive Slider Section */}
      <div className="py-4 space-y-3">
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-300 font-medium">
            Reduce {initialData.category} spend:
          </span>
          <span className="text-slate-400 font-mono text-[11px]">
            Current: ₹{baseSpend.toLocaleString('en-IN')}/mo
          </span>
        </div>

        {/* Range Slider */}
        <div className="space-y-1">
          <input
            type="range"
            min="0"
            max="50"
            step="5"
            value={sliderPct}
            onChange={handleChange}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>0% (No change)</span>
            <span>25%</span>
            <span>50% (Max cut)</span>
          </div>
        </div>
      </div>

      {/* Real-Time Recalculated Metrics Grid */}
      <div className="grid grid-cols-2 gap-2.5 pt-1 pb-3">
        {/* Monthly Savings Card */}
        <div className="bg-[#0E1322] p-3 rounded-xl border border-slate-800">
          <div className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
            <TrendingUp className="w-3 h-3 text-emerald-400" />
            <span>Monthly Savings</span>
          </div>
          <div className="text-sm font-bold font-mono text-emerald-400">
            +₹{monthlySavings.toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-500">
            New spend: ₹{simulatedSpend.toLocaleString('en-IN')}
          </div>
        </div>

        {/* Annualized Savings Card */}
        <div className="bg-[#0E1322] p-3 rounded-xl border border-slate-800">
          <div className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
            <Sparkles className="w-3 h-3 text-purple-400" />
            <span>Annual Run-Rate</span>
          </div>
          <div className="text-sm font-bold font-mono text-purple-300">
            +₹{annualizedSavings.toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-500">
            Compounded in 1 year
          </div>
        </div>
      </div>

      {/* Goal Velocity Impact */}
      {initialData.goal_impact && (
        <div className="bg-purple-950/20 border border-purple-500/20 rounded-xl p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0 text-purple-300">
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xs">
            <span className="text-white font-medium">
              {initialData.goal_impact.goal_name || 'Vacation Fund'} Impact:
            </span>
            <p className="text-purple-200/90 text-[11px] mt-0.5">
              Achieve milestone in <span className="font-bold text-white font-mono">{acceleratedMonths} months</span> (
              <span className="text-emerald-400 font-semibold">{monthsSaved} months faster</span> than current pace).
            </p>
          </div>
        </div>
      )}
    </motion.div>
  );
};
