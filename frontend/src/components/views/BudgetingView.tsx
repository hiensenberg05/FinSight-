import React, { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import { Budget } from '../../types';
import { api } from '../../services/api';

interface BudgetingViewProps {
  onSelectTab?: (tab: string) => void;
  budgets?: Budget[];
}

export const BudgetingView: React.FC<BudgetingViewProps> = ({ onSelectTab, budgets: initialBudgets }) => {
  const [budgets, setBudgets] = useState<Budget[]>(initialBudgets || []);

  useEffect(() => {
    if (initialBudgets && initialBudgets.length > 0) {
      setBudgets(initialBudgets);
      return;
    }
    api.getBudgets().then(setBudgets);
  }, [initialBudgets]);

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Header Title & Subtitle */}
      <div>
        <h2 className="text-[26px] font-extrabold tracking-tight text-metallic-silver">Budgets</h2>
        <p className="text-[13px] text-[#8E8AA5] mt-0.5">Category limits and real-time expense thresholds</p>
      </div>

      {/* Monthly category budgets Card - Glossy Apple 3D Surface */}
      <div className="rounded-2xl glass-card-3d p-5 sm:p-6 space-y-5 shadow-lg border border-white/[0.08]">
        <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
          <h3 className="text-[16px] font-extrabold text-metallic-silver tracking-tight">
            Monthly Category Budgets
          </h3>
          <span className="text-[12px] font-bold text-metallic-violet px-3 py-1 rounded-full glass-card-3d border border-white/[0.1]">
            {budgets[0]?.period || 'Current Period'}
          </span>
        </div>

        <div className="space-y-3.5">
          {budgets.map((b) => {
            const percentage = Math.round((b.spent / b.limit) * 100);
            const isOver = percentage >= 85;

            return (
              <div key={b.id || b.category} className="space-y-2.5 glass-card-3d p-3.5 rounded-xl border border-white/[0.06]">
                <div className="flex items-center justify-between text-[13.5px]">
                  <div className="flex items-center gap-2.5">
                    <span className="font-bold text-white">{b.category}</span>
                    {isOver && (
                      <span className="flex items-center gap-1 text-[11px] text-amber-300 bg-amber-400/15 px-2 py-0.5 rounded-full border border-amber-400/30 font-bold shadow-sm">
                        <AlertCircle className="w-3 h-3 text-amber-400" />
                        {percentage}% Used
                      </span>
                    )}
                  </div>
                  <span className="text-metallic-silver tabular-nums font-extrabold">
                    ₹{b.spent.toLocaleString('en-IN')} / ₹{b.limit.toLocaleString('en-IN')}
                  </span>
                </div>

                {/* 3D Sunken Progress Bar Track with Liquid Glow Fill */}
                <div className="w-full glass-inset-tray rounded-full h-2.5 overflow-hidden p-[1px] shadow-inner">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      percentage >= 100
                        ? 'bg-gradient-to-r from-rose-600 to-red-500 shadow-[0_0_10px_rgba(244,63,94,0.7)]'
                        : isOver
                        ? 'bg-gradient-to-r from-amber-500 to-orange-400 shadow-[0_0_10px_rgba(245,158,11,0.7)]'
                        : 'bg-gradient-to-r from-violet-600 via-fuchsia-500 to-cyan-400 shadow-[0_0_10px_rgba(168,85,247,0.7)]'
                    }`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Return to overview link */}
      <div className="pt-2">
        <button
          onClick={() => onSelectTab?.('dashboard')}
          className="text-[12.5px] font-semibold text-violet-400 hover:text-violet-300 transition-colors"
        >
          ← Return to overview
        </button>
      </div>
    </div>
  );
};
