import React, { useState } from 'react';
import { Calendar, ChevronDown, CheckCircle2, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface TimelineEvent {
  id: string;
  dateStr: string;
  dayLabel: string;
  isToday?: boolean;
  inflow?: number;
  outflow?: number;
  title: string;
  subtitle: string;
  category: string;
  type: 'credit' | 'debit' | 'settlement';
}

const timelineMilestones: TimelineEvent[] = [
  {
    id: 'm-1',
    dateStr: 'Jul 20',
    dayLabel: '20 Jul',
    outflow: 14200,
    title: 'Quarterly Insurance Premium',
    subtitle: 'HDFC Life · Auto-debited',
    category: 'Insurance',
    type: 'debit',
  },
  {
    id: 'm-2',
    dateStr: 'Aug 04',
    dayLabel: '04 Aug',
    inflow: 85000,
    title: 'Salary Credit - TechCorp',
    subtitle: 'Direct Deposit · Verified',
    category: 'Income',
    type: 'credit',
  },
  {
    id: 'm-3',
    dateStr: 'Aug 15',
    dayLabel: '15 Aug',
    outflow: 8500,
    title: 'Rent & Maintenance Transfer',
    subtitle: 'NEFT to Landlord',
    category: 'Housing',
    type: 'debit',
  },
  {
    id: 'm-4',
    dateStr: 'Aug 30',
    dayLabel: '30 Aug',
    isToday: true,
    inflow: 85000,
    outflow: 18200,
    title: 'TechCorp Salary & Card Settlement',
    subtitle: 'Salary (+₹85k) · HDFC CC Bill (-₹18.2k)',
    category: 'Settlement',
    type: 'settlement',
  },
  {
    id: 'm-5',
    dateStr: 'Sep 06',
    dayLabel: '06 Sep',
    outflow: 3200,
    title: 'SIP Mutual Fund Execution',
    subtitle: 'Nifty 50 Index Fund · Automated',
    category: 'Investment',
    type: 'debit',
  },
  {
    id: 'm-6',
    dateStr: 'Sep 13',
    dayLabel: '13 Sep',
    outflow: 1450,
    title: 'BESCOM Utility Bill Due',
    subtitle: 'Scheduled Auto-pay',
    category: 'Utilities',
    type: 'debit',
  },
  {
    id: 'm-7',
    dateStr: 'Sep 18',
    dayLabel: '18 Sep',
    inflow: 12400,
    title: 'Freelance Design Retainer',
    subtitle: 'UPI Transfer from Client',
    category: 'Income',
    type: 'credit',
  },
];

export const FinancialTimeline: React.FC = () => {
  const [selectedMilestone, setSelectedMilestone] = useState<TimelineEvent>(
    timelineMilestones[3] // Default to Aug 30
  );

  return (
    <div className="rounded-xl bg-[#111018] border border-white/[0.08] p-5 shadow-sm">
      {/* Top Header with title and horizon selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-violet-400" />
            <h3 className="text-sm font-bold text-white tracking-tight">
              Cash Flow Horizon & Milestones
            </h3>
          </div>
          <p className="text-xs text-[#8E8B9A] mt-0.5">
            Chronological forecast of recurring commitments, salary cycles, and settlements
          </p>
        </div>

        {/* Dropdown selector matching Pinterest Task timeline pill */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#181628] border border-violet-500/25 text-xs font-semibold text-white cursor-pointer hover:bg-violet-900/30 transition-colors">
            <span>July - September 2025</span>
            <ChevronDown className="w-3 h-3 text-violet-400" />
          </div>
        </div>
      </div>

      {/* Horizontal Gantt / Timeline Rail */}
      <div className="relative pt-3 pb-4 overflow-x-auto scrollbar-none">
        {/* Continuous Guide Line */}
        <div className="absolute top-8 left-4 right-4 h-0.5 bg-white/[0.08]" />

        {/* Milestone Nodes Rail */}
        <div className="flex items-start justify-between min-w-[560px] px-2 relative z-10">
          {timelineMilestones.map((milestone) => {
            const isSelected = selectedMilestone.id === milestone.id;
            const hasBoth = milestone.inflow && milestone.outflow;

            return (
              <button
                key={milestone.id}
                onClick={() => setSelectedMilestone(milestone)}
                className="flex flex-col items-center group focus-visible:outline-none"
              >
                {/* Node Pill / Dot */}
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-150 ${
                    isSelected
                      ? 'bg-violet-600 border-2 border-white ring-4 ring-violet-500/30 scale-110 shadow-lg'
                      : milestone.isToday
                      ? 'bg-[#181628] border-2 border-violet-400 text-violet-400'
                      : 'bg-[#181628] border border-white/[0.2] text-[#8E8B9A] group-hover:border-violet-400 group-hover:text-white'
                  }`}
                >
                  {hasBoth ? (
                    <span className="w-2 h-2 rounded-full bg-violet-400" />
                  ) : milestone.inflow ? (
                    <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 text-rose-400" />
                  )}
                </div>

                {/* Date Label */}
                <span
                  className={`text-[11px] font-mono mt-2 tracking-tight transition-colors ${
                    isSelected
                      ? 'font-bold text-white'
                      : milestone.isToday
                      ? 'font-semibold text-violet-400'
                      : 'text-[#8E8B9A] group-hover:text-white'
                  }`}
                >
                  {milestone.dateStr}
                </span>

                {/* Micro Amount Pill */}
                <span className="text-[10px] font-mono text-[#5C596C] tabular-numbers mt-0.5">
                  {milestone.inflow ? `+₹${Math.round(milestone.inflow / 1000)}k` : `-₹${Math.round((milestone.outflow || 0) / 1000)}k`}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Milestone Card Focus Plate (Matching Reference's August 30 highlight box) */}
      <div className="mt-4 rounded-lg bg-[#181628] border border-violet-500/30 p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-400 flex items-center justify-center flex-shrink-0 mt-0.5">
            {selectedMilestone.type === 'settlement' ? (
              <CheckCircle2 className="w-4 h-4" />
            ) : selectedMilestone.type === 'credit' ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-amber-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-tight">
                {selectedMilestone.dateStr} · {selectedMilestone.title}
              </span>
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-500/25 text-violet-300">
                {selectedMilestone.category}
              </span>
            </div>
            <p className="text-[11px] text-[#8E8B9A] mt-0.5">
              {selectedMilestone.subtitle}
            </p>
          </div>
        </div>

        {/* Milestone financials */}
        <div className="flex items-center gap-4 text-xs font-mono tabular-numbers">
          {selectedMilestone.inflow && (
            <div className="text-right">
              <span className="text-[10px] text-[#5C596C] font-sans block leading-none mb-1">Expected Inflow</span>
              <span className="font-bold text-emerald-400 text-sm">
                +₹{selectedMilestone.inflow.toLocaleString('en-IN')}
              </span>
            </div>
          )}
          {selectedMilestone.outflow && (
            <div className="text-right">
              <span className="text-[10px] text-[#5C596C] font-sans block leading-none mb-1">Scheduled Outflow</span>
              <span className="font-bold text-rose-400 text-sm">
                -₹{selectedMilestone.outflow.toLocaleString('en-IN')}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
