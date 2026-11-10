import React, { useState, useEffect } from 'react';
import { Target, Plus, Sparkles, Calculator } from 'lucide-react';
import { PremiumCard } from '../common/PremiumCard';
import { SavingsGoal } from '../../types';
import { api } from '../../services/api';

interface SavingsGoalsViewProps {
  goals?: SavingsGoal[];
}

export const SavingsGoalsView: React.FC<SavingsGoalsViewProps> = ({ goals: initialGoals }) => {
  const [goals, setGoals] = useState<SavingsGoal[]>(initialGoals || []);
  const [simulationCut, setSimulationCut] = useState(20);

  useEffect(() => {
    if (initialGoals && initialGoals.length > 0) {
      setGoals(initialGoals);
      return;
    }
    api.getSavingsGoals().then(setGoals);
  }, [initialGoals]);

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Top Banner - Glossy Apple 3D Surface */}
      <PremiumCard className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold text-violet-400 uppercase tracking-widest block mb-1">
            Predictive Savings Intelligence
          </span>
          <h2 className="text-[22px] font-extrabold text-metallic-silver tracking-tight">
            Active Savings Goals
          </h2>
          <p className="text-[12.5px] text-[#8E8AA5] mt-0.5">
            Automated monthly progress tracking toward your milestones
          </p>
        </div>

        <button
          onClick={() => alert('Add Goal: Enter target amount and milestone date in assistant chat.')}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-b from-violet-600/40 via-violet-700/50 to-indigo-900/60 border-t border-white/[0.25] border-b border-black/50 text-white text-[12.5px] font-bold shadow-[0_2px_10px_rgba(0,0,0,0.5),0_0_12px_rgba(139,92,246,0.3)] hover:brightness-110 active:scale-95 transition-all"
        >
          <Plus className="w-3.5 h-3.5 text-violet-300" />
          <span>New Savings Goal</span>
        </button>
      </PremiumCard>

      {/* Goals Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map((goal) => (
          <PremiumCard key={goal.id} className="p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[14.5px] font-bold text-white flex items-center gap-2.5">
                  <span className="w-3 h-3 rounded-full shadow-[0_0_8px_currentColor]" style={{ backgroundColor: goal.color }} />
                  {goal.name}
                </span>
                <span className="text-[14px] font-extrabold tabular-nums text-metallic-violet">
                  {goal.percentage}%
                </span>
              </div>

              {/* 3D Sunken Progress bar track with liquid glow */}
              <div className="w-full h-2.5 glass-inset-tray rounded-full overflow-hidden my-3 p-[1px] shadow-inner">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ 
                    width: `${goal.percentage}%`, 
                    backgroundColor: goal.color,
                    boxShadow: `0 0 10px ${goal.color}`
                  }}
                />
              </div>

              <div className="flex items-center justify-between text-[12.5px] text-[#8E8AA5] tabular-nums">
                <span>
                  Current: <strong className="text-white font-extrabold">₹{goal.currentAmount.toLocaleString('en-IN')}</strong>
                </span>
                <span>
                  Target: <strong className="text-metallic-silver font-extrabold">₹{goal.targetAmount.toLocaleString('en-IN')}</strong>
                </span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11.5px] text-[#8E8AA5]">
              <span>
                Estimated Completion: <strong className="text-white font-semibold">May {new Date().getFullYear() + 1}</strong>
              </span>
              <span className="text-emerald-400 font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/25">
                On Schedule
              </span>
            </div>
          </PremiumCard>
        ))}
      </div>

      {/* What-If Financial Simulation Card */}
      <div className="rounded-2xl glass-card-3d p-5 sm:p-6 shadow-lg border border-white/[0.08]">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-xl bg-violet-600/20 border-t border-white/[0.2] border-b border-black/40 flex items-center justify-center text-violet-300 shadow-sm">
            <Calculator className="w-4 h-4 text-violet-400" />
          </div>
          <h3 className="text-[15px] font-extrabold text-metallic-silver tracking-tight">What-If Savings Simulator</h3>
          <span className="text-[11px] bg-violet-500/15 text-violet-300 border border-violet-500/30 px-3 py-0.5 rounded-full font-bold ml-auto shadow-sm">
            Conversational Model
          </span>
        </div>

        <p className="text-[12.5px] text-[#C8C5DC] mb-4 leading-relaxed">
          "If you reduce discretionary food delivery spending by{' '}
          <strong className="text-violet-300 tabular-nums">{simulationCut}%</strong> (saving ~₹{Math.round(14200 * (simulationCut / 100)).toLocaleString('en-IN')}/month), you will achieve your <strong>Vacation Fund (₹60,000)</strong> in{' '}
          <strong className="text-emerald-400 tabular-nums font-bold">{(24000 / (18650 + 14200 * (simulationCut / 100))).toFixed(1)} months</strong> instead of 7 months."
        </p>

        <div className="flex items-center gap-4">
          <div className="flex-1 glass-inset-tray p-1.5 rounded-xl border border-white/[0.04]">
            <input
              type="range"
              min="5"
              max="50"
              step="5"
              value={simulationCut}
              onChange={(e) => setSimulationCut(Number(e.target.value))}
              className="w-full accent-violet-500 cursor-pointer h-2 rounded-lg bg-transparent"
            />
          </div>
          <span className="text-[12.5px] font-extrabold text-metallic-silver glass-pill-active px-3.5 py-1.5 rounded-xl min-w-20 text-center tabular-nums shadow-md">
            {simulationCut}% cut
          </span>
        </div>
      </div>
    </div>
  );
};
