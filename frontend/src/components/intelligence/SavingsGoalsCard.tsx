import React from 'react';
import { SavingsGoal } from '../../types';
import { Plus } from 'lucide-react';

interface SavingsGoalsCardProps {
  goals: SavingsGoal[];
  onAddGoal?: () => void;
}

export const SavingsGoalsCard: React.FC<SavingsGoalsCardProps> = ({
  goals,
  onAddGoal,
}) => {
  // Dimension definitions for concentric dual rings
  const size = 112;
  const strokeWidth = 8.5;
  const center = size / 2;

  // Outer ring (Goal 1: Vacation Fund - Cyan)
  const outerRadius = 46;
  const outerCircumference = 2 * Math.PI * outerRadius;
  const outerPercentage = goals[0]?.percentage || 60;
  const outerOffset = outerCircumference - (outerPercentage / 100) * outerCircumference;

  // Inner ring (Goal 2: Emergency Fund - Pink)
  const innerRadius = 32;
  const innerCircumference = 2 * Math.PI * innerRadius;
  const innerPercentage = goals[1]?.percentage || 85;
  const innerOffset = innerCircumference - (innerPercentage / 100) * innerCircumference;

  return (
    <div className="bg-[#0E1322] border border-slate-700/60 border-t-white/10 rounded-2xl p-5 shadow-panel ring-1 ring-inset ring-white/[0.04] transition-all duration-300 hover:border-purple-500/40">
      <div className="flex items-center justify-between mb-2.5">
        <h3 className="text-xs font-semibold text-slate-100 tracking-wide flex items-center gap-2">
          <span>Savings Goals</span>
        </h3>
        <button
          onClick={onAddGoal}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
          title="Add New Goal"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex items-center justify-between gap-3">
        {/* Concentric Progress Rings */}
        <div className="relative flex-shrink-0 flex items-center justify-center">
          <svg width={size} height={size} className="transform -rotate-90">
            {/* Outer Track & Progress (Vacation Fund) */}
            <circle
              cx={center}
              cy={center}
              r={outerRadius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth={strokeWidth}
              fill="transparent"
            />
            <circle
              cx={center}
              cy={center}
              r={outerRadius}
              stroke="#06B6D4" // Cyan
              strokeWidth={strokeWidth}
              strokeDasharray={outerCircumference}
              strokeDashoffset={outerOffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />

            {/* Inner Track & Progress (Emergency Fund) */}
            <circle
              cx={center}
              cy={center}
              r={innerRadius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth={strokeWidth}
              fill="transparent"
            />
            <circle
              cx={center}
              cy={center}
              r={innerRadius}
              stroke="#EC4899" // Hot Pink
              strokeWidth={strokeWidth}
              strokeDasharray={innerCircumference}
              strokeDashoffset={innerOffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          {/* Center Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none px-2">
            <span className="text-[9px] font-bold text-slate-300 uppercase tracking-tighter leading-tight">
              Savings<br />Goals
            </span>
          </div>
        </div>

        {/* Legend List on Right */}
        <div className="flex-1 flex flex-col justify-center space-y-2.5">
          {goals.map((goal) => (
            <div key={goal.id} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 truncate">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0 shadow-sm"
                  style={{ backgroundColor: goal.color }}
                />
                <span className="text-slate-300 font-medium truncate">
                  {goal.name}
                </span>
              </div>
              <span className="font-bold text-white font-mono ml-2">
                {goal.percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
