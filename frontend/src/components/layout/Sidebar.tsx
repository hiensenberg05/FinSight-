import React from 'react';
import {
  LayoutGrid,
  PieChart,
  Target,
  TrendingUp,
  Receipt,
  CalendarCheck,
  Sparkles,
  ShieldCheck,
  FileText,
  Settings,
  HelpCircle,
  LogOut,
  ChevronRight,
  UploadCloud,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenUpload?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  onOpenUpload,
}) => {
  const generalItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
    { id: 'budgeting', label: 'Budgeting & Expenses', icon: PieChart },
    { id: 'savings', label: 'Savings & Goals', icon: Target },
    { id: 'analytics', label: 'Cash Advances & Analytics', icon: TrendingUp },
    { id: 'transactions', label: 'Transactions', icon: Receipt },
    { id: 'bills', label: 'Bills & Payments', icon: CalendarCheck },
  ];

  const aiItems = [
    { id: 'ai-assistant', label: 'AI Assistant', icon: Sparkles },
    { id: 'financial-health', label: 'Financial Health', icon: ShieldCheck },
    { id: 'reports', label: 'Reports & Analytics', icon: FileText },
  ];

  const userItems = [
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'help', label: 'Help & Support', icon: HelpCircle },
  ];

  const renderNavItem = (item: { id: string; label: string; icon: React.ElementType }) => {
    const Icon = item.icon;
    const isActive = activeTab === item.id;

    return (
      <button
        key={item.id}
        onClick={() => onSelectTab(item.id)}
        className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
          isActive
            ? 'bg-[#1D1735] border border-purple-500/50 text-white shadow-glow-purple'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
        }`}
      >
        <div className="flex items-center gap-3 truncate">
          <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-purple-400' : 'text-slate-400'}`} />
          <span className="truncate">{item.label}</span>
        </div>
        {isActive && (
          <div className="w-5 h-5 rounded-full bg-purple-600/40 border border-purple-400/40 flex items-center justify-center flex-shrink-0">
            <ChevronRight className="w-3 h-3 text-purple-200" />
          </div>
        )}
      </button>
    );
  };

  return (
    <aside className="w-60 h-full bg-[#090D18] border-r border-slate-800/80 flex flex-col justify-between py-5 px-3 select-none flex-shrink-0">
      {/* Top Logo & App Branding */}
      <div>
        <div 
          onClick={() => onSelectTab('ai-assistant')}
          className="flex items-center gap-2.5 px-3 mb-6 cursor-pointer group"
        >
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-violet-400 flex items-center justify-center shadow-glow-purple group-hover:scale-105 transition-transform">
            <span className="text-white text-base font-bold">✦</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-white font-sans flex items-center gap-0.5">
              FinSight<span className="text-purple-400">.</span>
            </span>
          </div>
        </div>

        {/* Upload Statement Action Pill */}
        {onOpenUpload && (
          <div className="px-1 mb-4">
            <button
              onClick={onOpenUpload}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-purple-900/30 hover:bg-purple-900/50 border border-purple-500/30 text-purple-200 text-xs font-semibold transition-all shadow-sm group"
            >
              <UploadCloud className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
              <span>Import Bank CSV</span>
            </button>
          </div>
        )}

        {/* Section: GENERAL */}
        <div className="mb-4">
          <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
            General
          </p>
          <nav className="space-y-0.5">
            {generalItems.map(renderNavItem)}
          </nav>
        </div>

        {/* Section: AI & INSIGHTS */}
        <div className="mb-4">
          <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
            AI & Insights
          </p>
          <nav className="space-y-0.5">
            {aiItems.map(renderNavItem)}
          </nav>
        </div>

        {/* Section: USER */}
        <div>
          <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
            User
          </p>
          <nav className="space-y-0.5">
            {userItems.map(renderNavItem)}
          </nav>
        </div>
      </div>

      {/* Bottom: Logout Button */}
      <div className="pt-3 border-t border-slate-800/60">
        <button
          onClick={() => alert('FinSight: Session locked for security.')}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 transition-all"
        >
          <LogOut className="w-4 h-4 text-slate-400" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};
