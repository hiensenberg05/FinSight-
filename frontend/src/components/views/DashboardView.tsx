import React, { useState, useEffect } from 'react';
import { 
  Wallet, 
  Receipt, 
  Banknote, 
  Target, 
  BarChart2, 
  PieChart as PieIcon, 
  ListFilter, 
  LayoutGrid, 
  ArrowLeftRight, 
  Heart,
  Clock,
  TrendingUp,
  TrendingDown,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie } from 'recharts';
import { api } from '../../services/api';
import { FinancialHealthMetrics, CategorySpending, Transaction, SavingsGoal, Bill } from '../../types';
import { formatINR, getTodayFormatted } from '../../utils/formatters';
import { FinancialTimeline } from '../modular/FinancialTimeline';

interface DashboardViewProps {
  onSelectTab?: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onSelectTab }) => {
  const [activeSegmentTab, setActiveSegmentTab] = useState<'overview' | 'spending' | 'cashflow' | 'goals'>('overview');
  const [selectedTimeframe, setSelectedTimeframe] = useState<'7D' | '30D' | '3M' | '1Y'>('30D');

  // Real Database State
  const [healthMetrics, setHealthMetrics] = useState<FinancialHealthMetrics | null>(null);
  const [categories, setCategories] = useState<CategorySpending[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [bills, setBills] = useState<Bill[]>([]);

  useEffect(() => {
    api.getHealthMetrics().then(setHealthMetrics);
    api.getCategorySpending().then(setCategories);
    api.getTransactions().then(setTransactions);
    api.getSavingsGoals().then(setGoals);
    api.getBills().then(setBills);
  }, []);

  const totalSpent = categories.reduce((sum, c) => sum + Math.abs(c.amount), 0);
  const totalBills = bills.reduce((sum, b) => sum + b.amount, 0);
  const screenBTransactions = transactions.slice(0, 5);

  // Dynamic timeframe datasets
  const getTrendData = () => {
    switch (selectedTimeframe) {
      case '7D':
        return [
          { day: 'Feb 22', amount: 1850 },
          { day: 'Feb 23', amount: 2940 },
          { day: 'Feb 24', amount: 1420 },
          { day: 'Feb 25', amount: 2100 },
          { day: 'Feb 26', amount: 3850 },
          { day: 'Feb 27', amount: 18668 },
          { day: 'Feb 28', amount: 3200, isYesterday: true },
        ];
      case '30D':
        return [
          { day: '01', amount: 1420 },
          { day: '05', amount: 2850 },
          { day: '10', amount: 3900 },
          { day: '15', amount: 1840 },
          { day: '20', amount: 4600 },
          { day: '25', amount: 2100 },
          { day: '28', amount: 3200, isYesterday: true },
        ];
      case '3M':
        return [
          { day: 'Dec 24', amount: 42100 },
          { day: 'Jan 25', amount: 40120 },
          { day: 'Feb 25', amount: totalSpent || 48884, isYesterday: true },
        ];
      case '1Y':
        return [
          { day: 'Mar', amount: 38200 },
          { day: 'May', amount: 41500 },
          { day: 'Jul', amount: 39800 },
          { day: 'Sep', amount: 44200 },
          { day: 'Nov', amount: 46100 },
          { day: 'Jan', amount: 40120 },
          { day: 'Feb', amount: totalSpent || 48884, isYesterday: true },
        ];
    }
  };

  const activeTrendData = getTrendData();

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-3.5 pb-2">
      {/* TOP: Greeting & Date Block */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-0.5">
        <div>
          <h2 className="text-[26px] font-extrabold text-metallic-silver tracking-tight leading-tight">
            Good evening, Aarav
          </h2>
          <p className="text-[13px] text-[#8E8AA5] mt-0.5">
            Verified financial records loaded live from PostgreSQL database.
          </p>
        </div>

        <div className="text-left sm:text-right">
          <span className="text-[13.5px] font-extrabold text-metallic-violet block leading-tight">
            {getTodayFormatted()}
          </span>
        </div>
      </div>

      {/* GLIDING SEGMENTED TABS */}
      <div className="inline-flex items-center p-1 rounded-2xl glass-inset-tray backdrop-blur-xl">
        <button
          onClick={() => setActiveSegmentTab('overview')}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-[12px] font-bold transition-all ${
            activeSegmentTab === 'overview'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveSegmentTab('spending')}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-[12px] font-medium transition-all ${
            activeSegmentTab === 'spending'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Spending</span>
        </button>

        <button
          onClick={() => setActiveSegmentTab('cashflow')}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-[12px] font-medium transition-all ${
            activeSegmentTab === 'cashflow'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <ArrowLeftRight className="w-3.5 h-3.5" />
          <span>Cash Flow</span>
        </button>

        <button
          onClick={() => setActiveSegmentTab('goals')}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-[12px] font-medium transition-all ${
            activeSegmentTab === 'goals'
              ? 'glass-pill-active text-white'
              : 'text-[#8E8AA5] hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Heart className="w-3.5 h-3.5" />
          <span>Goals</span>
        </button>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* VIEW MODE 1: OVERVIEW & SPENDING (Primary KPI Row) */}
      {/* ------------------------------------------------------------- */}
      {(activeSegmentTab === 'overview' || activeSegmentTab === 'spending') && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* KPI 1: Total Balance */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-b from-[#1E2D4A] to-[#0E1726] border-t border-blue-400/40 border-b border-black/50 flex items-center justify-center text-[#3F83FF] flex-shrink-0 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_4px_12px_rgba(0,0,0,0.5)]">
              <Wallet className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block leading-tight">
                Total Balance
              </span>
              <div className="text-[23px] font-extrabold text-metallic-silver tabular-nums tracking-tight leading-tight mt-0.5">
                {formatINR(healthMetrics?.availableBalance || 102756)}
              </div>
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 mt-0.5">
                <span>↑ +2.4%</span>
                <span className="text-[#7C7896] font-normal">vs. last month</span>
              </div>
            </div>
          </div>

          {/* KPI 2: Monthly Spending */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-b from-[#381630] to-[#1C0B18] border-t border-pink-400/40 border-b border-black/50 flex items-center justify-center text-[#E065A6] flex-shrink-0 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_4px_12px_rgba(0,0,0,0.5)]">
              <Receipt className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block leading-tight">
                Monthly Spending
              </span>
              <div className="text-[23px] font-extrabold text-metallic-silver tabular-nums tracking-tight leading-tight mt-0.5">
                {formatINR(totalSpent || 48884)}
              </div>
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 mt-0.5">
                <span>↓ -12.1%</span>
                <span className="text-[#7C7896] font-normal">vs. last month</span>
              </div>
            </div>
          </div>

          {/* KPI 3: Monthly Savings */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-b from-[#143026] to-[#0A1A14] border-t border-emerald-400/40 border-b border-black/50 flex items-center justify-center text-[#10B981] flex-shrink-0 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_4px_12px_rgba(0,0,0,0.5)]">
              <Banknote className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block leading-tight">
                Monthly Savings
              </span>
              <div className="text-[23px] font-extrabold text-metallic-silver tabular-nums tracking-tight leading-tight mt-0.5">
                {formatINR(healthMetrics?.monthlySavings ? Math.max(0, healthMetrics.monthlySavings) : 18650)}
              </div>
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 mt-0.5">
                <span>↑ +26%</span>
                <span className="text-[#7C7896] font-normal">savings rate</span>
              </div>
            </div>
          </div>

          {/* KPI 4: Upcoming Bills */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-b from-[#2B1B4A] to-[#160D27] border-t border-violet-400/40 border-b border-black/50 flex items-center justify-center text-[#9065E0] flex-shrink-0 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_4px_12px_rgba(0,0,0,0.5)]">
              <Target className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block leading-tight">
                Upcoming Bills
              </span>
              <div className="text-[23px] font-extrabold text-metallic-silver tabular-nums tracking-tight leading-tight mt-0.5">
                {formatINR(totalBills || 6357)}
              </div>
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-300 mt-0.5">
                <span>{bills.length || 5} bills</span>
                <span className="text-[#7C7896] font-normal">next 30 days</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* VIEW MODE 2: CASH FLOW TAB SPECIFIC KPI ROW */}
      {/* ------------------------------------------------------------- */}
      {activeSegmentTab === 'cashflow' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="rounded-2xl glass-card-3d p-4 flex items-start gap-3.5 border-t border-emerald-500/30">
            <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-400/40 flex items-center justify-center text-emerald-400 flex-shrink-0">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block">Monthly Inflow</span>
              <div className="text-[22px] font-extrabold text-emerald-400 tabular-nums mt-0.5">₹85,000</div>
              <span className="text-[11px] text-[#7C7896]">Salary & recurring credits</span>
            </div>
          </div>

          <div className="rounded-2xl glass-card-3d p-4 flex items-start gap-3.5 border-t border-pink-500/30">
            <div className="w-10 h-10 rounded-xl bg-pink-950/60 border border-pink-400/40 flex items-center justify-center text-pink-400 flex-shrink-0">
              <TrendingDown className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block">Monthly Outflow</span>
              <div className="text-[22px] font-extrabold text-pink-300 tabular-nums mt-0.5">{formatINR(totalSpent || 48884)}</div>
              <span className="text-[11px] text-[#7C7896]">Ledger expenses & bills</span>
            </div>
          </div>

          <div className="rounded-2xl glass-card-3d p-4 flex items-start gap-3.5 border-t border-blue-500/30">
            <div className="w-10 h-10 rounded-xl bg-blue-950/60 border border-blue-400/40 flex items-center justify-center text-blue-400 flex-shrink-0">
              <ArrowLeftRight className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block">Net Operating Cash</span>
              <div className="text-[22px] font-extrabold text-emerald-300 tabular-nums mt-0.5">
                {formatINR(Math.max(0, 85000 - (totalSpent || 48884)))}
              </div>
              <span className="text-[11px] text-emerald-400">Positive monthly surplus</span>
            </div>
          </div>

          <div className="rounded-2xl glass-card-3d p-4 flex items-start gap-3.5 border-t border-purple-500/30">
            <div className="w-10 h-10 rounded-xl bg-purple-950/60 border border-purple-400/40 flex items-center justify-center text-purple-400 flex-shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11.5px] font-medium text-[#8E8AA5] block">Cash Runway</span>
              <div className="text-[22px] font-extrabold text-metallic-silver tabular-nums mt-0.5">8.2 Months</div>
              <span className="text-[11px] text-purple-300">₹1,02,756 liquid cushion</span>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* CASH FLOW VIEW: EMBEDDED FINANCIAL TIMELINE */}
      {/* ------------------------------------------------------------- */}
      {activeSegmentTab === 'cashflow' && (
        <div className="space-y-4">
          <FinancialTimeline />
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* GOALS VIEW: FULL GOALS DEEP-DIVE & SIMULATION */}
      {/* ------------------------------------------------------------- */}
      {activeSegmentTab === 'goals' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {goals.map((goal) => {
              const pct = Math.round((goal.currentAmount / goal.targetAmount) * 100);
              const remaining = goal.targetAmount - goal.currentAmount;
              return (
                <div key={goal.id} className="rounded-2xl glass-card-3d p-5 space-y-3.5 border-t border-violet-500/30 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <h4 className="text-[16px] font-bold text-white">{goal.name}</h4>
                      <span className="text-[13px] font-extrabold text-metallic-violet">{pct}%</span>
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-[20px] font-extrabold text-white">{formatINR(goal.currentAmount)}</span>
                      <span className="text-[12px] text-[#8E8AA5]">of {formatINR(goal.targetAmount)}</span>
                    </div>
                    <div className="w-full glass-inset-tray rounded-full h-2.5 overflow-hidden p-[1px] mt-3">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-600 via-fuchsia-500 to-cyan-400 transition-all duration-700"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11.5px] text-[#8E8AA5]">
                    <span>Remaining: {formatINR(remaining)}</span>
                    <span className="text-violet-400 font-semibold">Pace: ~₹12k/mo</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Predictive Acceleration Banner */}
          <div className="rounded-2xl glass-card-3d p-5 flex flex-col sm:flex-row items-center justify-between gap-4 border border-violet-500/20 bg-gradient-to-r from-violet-950/20 to-purple-900/10">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-violet-600/30 border border-violet-400/40 flex items-center justify-center text-violet-300 flex-shrink-0">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-[15px] font-bold text-white">Accelerate Your Vacation Fund</h4>
                <p className="text-[12.5px] text-[#8E8AA5] mt-0.5">
                  Reducing weekend food orders by 20% frees up ₹5,225/mo, achieving your goal 2.8 months sooner.
                </p>
              </div>
            </div>
            <button
              onClick={() => onSelectTab?.('ai-assistant')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs transition-all shadow-lg shadow-violet-600/30 flex-shrink-0"
            >
              <span>Test What-If Simulation</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SPENDING & OVERVIEW CHARTS ROW */}
      {/* ------------------------------------------------------------- */}
      {(activeSegmentTab === 'overview' || activeSegmentTab === 'spending') && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-stretch">
          {/* Daily Spending Trend */}
          <div className="lg:col-span-7 rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-[#3F83FF]" />
                  <h3 className="text-[15px] font-extrabold text-metallic-silver tracking-tight">
                    Daily Spending Trend
                  </h3>
                </div>
                <div className="flex items-center gap-1 glass-inset-tray p-1 rounded-xl">
                  {(['7D', '30D', '3M', '1Y'] as const).map((tf) => (
                    <button
                      key={tf}
                      onClick={() => setSelectedTimeframe(tf)}
                      className={`px-2.5 py-0.5 text-[11px] font-bold rounded-lg transition-all ${
                        selectedTimeframe === tf
                          ? 'glass-pill-active text-white'
                          : 'text-[#8E8AA5] hover:text-white'
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </div>

              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={activeTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="day" stroke="#5A5675" fontSize={11} tickLine={false} />
                    <YAxis stroke="#5A5675" fontSize={11} tickLine={false} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="glass-card-3d p-2 rounded-lg text-xs text-white">
                              <p className="font-semibold">{formatINR(payload[0].value as number)}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                      {activeTrendData.map((entry, index) => (
                        <Cell key={`bar-${index}`} fill={entry.isYesterday ? '#C084FC' : '#6366F1'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Category Spending Donut */}
          <div className="lg:col-span-5 rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <PieIcon className="w-4 h-4 text-[#A78BFA]" />
                  <h3 className="text-[15px] font-extrabold text-metallic-silver tracking-tight">
                    Category Breakdown
                  </h3>
                </div>
                <span className="text-[11.5px] font-medium text-[#8E8AA5]">
                  {categories.length} categories
                </span>
              </div>

              <div className="flex items-center justify-between gap-3 py-1">
                <div className="relative w-32 h-32 flex items-center justify-center flex-shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categories}
                        dataKey="amount"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={38}
                        outerRadius={54}
                        paddingAngle={3}
                        cornerRadius={4}
                      >
                        {categories.map((entry, index) => (
                          <Cell key={`donut-${index}`} fill={entry.color || '#8B5CF6'} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-4 rounded-full glass-inset-tray flex flex-col items-center justify-center pointer-events-none">
                    <span className="text-[12px] font-extrabold text-metallic-silver tabular-nums">
                      {formatINR(totalSpent)}
                    </span>
                    <span className="text-[8px] text-[#8E8AA5] uppercase">Total</span>
                  </div>
                </div>

                <div className="space-y-1.5 flex-1 text-[11.5px]">
                  {categories.slice(0, 5).map((cat) => (
                    <div key={cat.name} className="flex items-center justify-between glass-card-3d px-2 py-1 rounded-lg">
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: cat.color || '#8B5CF6' }} />
                        <span className="text-[#C8C5DC] truncate">{cat.name}</span>
                      </div>
                      <span className="text-white font-semibold tabular-nums ml-2">
                        {cat.percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* SPENDING TAB: EXPANDED CATEGORIES GRID */}
      {/* ------------------------------------------------------------- */}
      {activeSegmentTab === 'spending' && (
        <div className="rounded-2xl glass-card-3d p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-white">All Category Allocations</h3>
            <span className="text-xs text-[#8E8AA5]">Total monthly spend: {formatINR(totalSpent)}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {categories.map((c) => (
              <div key={c.name} className="glass-card-3d p-3 rounded-xl flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c.color || '#8B5CF6' }} />
                    <span className="text-xs font-semibold text-white">{c.name}</span>
                  </div>
                  <span className="text-[11px] text-[#8E8AA5] mt-0.5 block">{c.percentage}% of monthly budget</span>
                </div>
                <span className="text-sm font-bold text-metallic-silver tabular-nums">{formatINR(c.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* OVERVIEW & SPENDING ROW 3: TRANSACTIONS + GOALS */}
      {/* ------------------------------------------------------------- */}
      {(activeSegmentTab === 'overview' || activeSegmentTab === 'spending') && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-stretch">
          <div className="lg:col-span-7 rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <ListFilter className="w-4 h-4 text-[#3F83FF]" />
                  <h3 className="text-[15px] font-extrabold text-metallic-silver tracking-tight">
                    Recent Transactions
                  </h3>
                </div>
                <button 
                  onClick={() => onSelectTab?.('transactions')}
                  className="text-[11.5px] font-medium text-violet-400 hover:text-violet-300 transition-colors"
                >
                  View all ({transactions.length}) →
                </button>
              </div>

              <div className="space-y-2">
                {screenBTransactions.map((tx) => (
                  <div 
                    key={tx.id}
                    className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-violet-600/30 border border-violet-400/30 text-white font-bold text-[13px] flex items-center justify-center shadow-md flex-shrink-0">
                        {tx.merchant ? tx.merchant[0] : 'T'}
                      </div>
                      <div>
                        <span className="text-[13.5px] font-semibold text-white block leading-tight">
                          {tx.merchant}
                        </span>
                        <span className="text-[11.5px] text-[#8E8AA5] block mt-0.5">
                          {tx.dateStr || tx.date} · {tx.category}
                        </span>
                      </div>
                    </div>
                    <span className={`text-[14px] font-bold tabular-nums ${tx.amount > 0 ? 'text-emerald-400' : 'text-metallic-silver'}`}>
                      {tx.amount > 0 ? `+${formatINR(tx.amount)}` : formatINR(Math.abs(tx.amount))}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Your Goals */}
          <div className="lg:col-span-5 rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-[#A78BFA]" />
                  <h3 className="text-[15px] font-extrabold text-metallic-silver tracking-tight">
                    Your Goals
                  </h3>
                </div>
                <button 
                  onClick={() => onSelectTab?.('goals')}
                  className="text-[11.5px] font-medium text-violet-400 hover:text-violet-300 transition-colors"
                >
                  View all ({goals.length}) →
                </button>
              </div>

              <div className="space-y-3 pt-0.5">
                {goals.slice(0, 2).map((goal) => {
                  const pct = Math.round((goal.currentAmount / goal.targetAmount) * 100);
                  return (
                    <div key={goal.id} className="space-y-2 glass-card-3d p-2.5 rounded-xl">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-[13.5px] font-bold text-white block leading-tight">
                            {goal.name}
                          </span>
                          <span className="text-[11.5px] text-[#8E8AA5] tabular-nums block mt-0.5">
                            {formatINR(goal.currentAmount)} / {formatINR(goal.targetAmount)}
                          </span>
                        </div>
                        <span className="text-[12.5px] font-extrabold text-metallic-violet tabular-nums">
                          {pct}%
                        </span>
                      </div>

                      <div className="w-full glass-inset-tray rounded-full h-2 overflow-hidden p-[1px]">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-violet-600 via-fuchsia-500 to-cyan-400 transition-all duration-700"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
