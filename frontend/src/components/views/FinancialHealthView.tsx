import React from 'react';
import { ShieldCheck, TrendingUp, AlertTriangle, CheckCircle, ArrowUpRight, Sparkles } from 'lucide-react';
import { PremiumCard } from '../common/PremiumCard';

export const FinancialHealthView: React.FC = () => {
  const pillars = [
    { title: 'Savings Rate', score: '22%', benchmark: 'Target > 20%', status: 'optimal', desc: 'You save ₹18,650 out of ₹85,000 monthly income.' },
    { title: 'Emergency Runway', score: '3.8 mos', benchmark: 'Target > 6 mos', status: 'warning', desc: 'Current emergency fund ₹85,000 covers ~3.8 months of fixed living expenses.' },
    { title: 'Discretionary Ratio', score: '34%', benchmark: 'Target < 30%', status: 'warning', desc: 'Dining and entertainment spending is slightly above optimal allocation.' },
    { title: 'Fixed Debt/EMI Ratio', score: '0%', benchmark: 'Target < 35%', status: 'optimal', desc: 'Zero outstanding personal loans or credit card revolving debt.' },
  ];

  return (
    <div className="h-full overflow-y-auto space-y-4 pr-1 scroll-smooth">
      {/* Score Hero Card - Glossy Apple 3D Surface */}
      <PremiumCard className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6 border-violet-500/35 shadow-xl">
        <div className="flex items-center gap-5">
          {/* 3D Illuminated Circular Score Ring */}
          <div className="relative w-24 h-24 rounded-full bg-gradient-to-tr from-violet-600 via-fuchsia-500 to-cyan-400 p-[3px] flex items-center justify-center shadow-[0_0_28px_rgba(168,85,247,0.45)] flex-shrink-0">
            <div className="w-full h-full rounded-full glass-inset-tray flex flex-col items-center justify-center shadow-inner">
              <span className="text-[28px] font-black text-metallic-silver tabular-nums">78</span>
              <span className="text-[10px] text-emerald-400 font-extrabold uppercase tracking-wider drop-shadow-[0_0_6px_rgba(52,211,153,0.5)]">Good</span>
            </div>
          </div>
          <div>
            <h2 className="text-[22px] font-extrabold text-metallic-silver tracking-tight">FinSight Financial Health Index</h2>
            <p className="text-[12.5px] text-[#8E8AA5] mt-1 max-w-lg leading-relaxed">
              Your overall financial position is strong. You are living well within your means, with zero bad debt and a 26% monthly savings rate.
            </p>
          </div>
        </div>

        <div className="glass-inset-tray border border-white/[0.08] p-4 rounded-2xl flex flex-col items-center justify-center text-center shadow-inner min-w-[140px]">
          <span className="text-[10.5px] text-[#8E8AA5] uppercase tracking-widest font-bold">Potential Score</span>
          <span className="text-[22px] font-extrabold text-metallic-violet tabular-nums mt-0.5">88 / 100</span>
          <span className="text-[11.5px] text-[#8E8AA5] mt-0.5 font-medium">Achievable in 90 days</span>
        </div>
      </PremiumCard>

      {/* 4 Core Pillars */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {pillars.map((p) => (
          <PremiumCard key={p.title} className="p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-[#8E8AA5] font-semibold">{p.title}</span>
                <span className={`text-[10.5px] uppercase font-bold px-2 py-0.5 rounded-full ${
                  p.status === 'optimal' 
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-[0_0_8px_rgba(52,211,153,0.2)]' 
                    : 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-[0_0_8px_rgba(245,158,11,0.2)]'
                }`}>
                  {p.status}
                </span>
              </div>
              <p className="text-[26px] font-extrabold text-metallic-platinum tabular-nums mt-1">{p.score}</p>
              <span className="text-[11px] text-[#8E8AA5] font-medium block mt-0.5">{p.benchmark}</span>
            </div>
            <p className="text-[11.5px] text-[#C8C5DC] mt-2.5 leading-relaxed border-t border-white/[0.06] pt-2">{p.desc}</p>
          </PremiumCard>
        ))}
      </div>

      {/* Personalized Improvement Actions */}
      <PremiumCard className="p-5">
        <h3 className="text-[15px] font-extrabold text-metallic-silver mb-1 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span>Recommended Score Booster Actions</span>
        </h3>
        <p className="text-[12.5px] text-[#8E8AA5] mb-3">
          Voice assistant verified suggestions to push your index above 85+:
        </p>
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between p-3.5 rounded-xl glass-inset-tray border border-white/[0.04]">
            <span className="text-white font-medium">Direct ₹3,500/month from Dining to Emergency Fund (target 6 months runway)</span>
            <span className="text-emerald-400 font-extrabold tabular-nums drop-shadow-[0_0_6px_rgba(52,211,153,0.4)] text-[13px]">+6 pts</span>
          </div>
          <div className="flex items-center justify-between p-3.5 rounded-xl glass-inset-tray border border-white/[0.04]">
            <span className="text-white font-medium">Cancel inactive subscription (unused account)</span>
            <span className="text-emerald-400 font-extrabold tabular-nums drop-shadow-[0_0_6px_rgba(52,211,153,0.4)] text-[13px]">+4 pts</span>
          </div>
        </div>
      </PremiumCard>
    </div>
  );
};
