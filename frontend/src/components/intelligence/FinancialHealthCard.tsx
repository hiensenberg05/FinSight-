import React from 'react';
import { FinancialHealthMetrics } from '../../types';
import { ChevronRight } from 'lucide-react';

interface FinancialHealthCardProps {
  metrics: FinancialHealthMetrics;
  onImproveScore?: () => void;
}

export const FinancialHealthCard: React.FC<FinancialHealthCardProps> = ({
  metrics,
  onImproveScore,
}) => {
  // Circular progress calculations for SVG ring
  const size = 86;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (metrics.score / 100) * circumference;

  return (
    <div className="bg-[#0E1322] border border-slate-700/60 border-t-white/10 rounded-2xl p-5 shadow-panel ring-1 ring-inset ring-white/[0.04] transition-all duration-300 hover:border-purple-500/40">
      <div className="flex items-center justify-between mb-3.5">
        <h3 className="text-xs font-semibold text-slate-100 tracking-wide flex items-center gap-2">
          <span>Financial Health Score</span>
        </h3>
        <span className="text-[10px] uppercase font-bold tracking-wider text-purple-300 bg-purple-500/15 px-2.5 py-0.5 rounded-full border border-purple-500/30">
          FinSight Index
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Circular Progress Gauge */}
        <div className="relative flex-shrink-0 flex items-center justify-center">
          <svg width={size} height={size} className="transform -rotate-90">
            {/* Background track ring */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth={strokeWidth}
              fill="transparent"
            />
            {/* Animated Progress ring */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="url(#healthGradient)"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
            <defs>
              <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#06B6D4" />
              </linearGradient>
            </defs>
          </svg>

          {/* Center Score Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-sm font-extrabold text-white font-mono leading-none">
              {metrics.score}
              <span className="text-[10px] text-slate-400 font-normal">/100</span>
            </span>
            <span className="text-[9px] font-semibold text-emerald-400 mt-0.5">
              {metrics.rating}
            </span>
          </div>
        </div>

        {/* Health Description and Action */}
        <div className="flex-1 flex flex-col justify-between">
          <p className="text-xs text-slate-300 leading-relaxed">
            {metrics.summary}
          </p>

          <div className="mt-2.5">
            <button
              onClick={onImproveScore}
              className="text-xs font-medium text-slate-200 hover:text-white bg-[#141A2D] hover:bg-[#1A223B] border border-slate-700/60 border-t-white/10 hover:border-purple-500/40 px-3 py-1.5 rounded-full transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span>Improve My Score</span>
              <ChevronRight className="w-3.5 h-3.5 text-purple-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
