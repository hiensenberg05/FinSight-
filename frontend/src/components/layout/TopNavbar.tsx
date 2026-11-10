import React from 'react';
import { Search, Bell, ChevronDown, Sparkles } from 'lucide-react';

interface TopNavbarProps {
  currentTabName: string;
  userName?: string;
  userRole?: string;
  onOpenSearch?: () => void;
  onOpenNotifications?: () => void;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  currentTabName = 'AI Assistant',
  userName = 'Aarav Sharma',
  userRole = 'Fintech Analyst',
  onOpenSearch,
  onOpenNotifications,
}) => {
  return (
    <header className="h-14 w-full bg-[#080B14] border-b border-slate-800/80 px-6 flex items-center justify-between select-none flex-shrink-0 z-20">
      {/* Left: Current Page Label */}
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-semibold text-slate-200">
          {currentTabName}
        </h1>
        <span className="text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded-full font-medium hidden sm:inline-flex items-center gap-1">
          <Sparkles className="w-2.5 h-2.5" /> Gnani AI Connected
        </span>
      </div>

      {/* Right: Search, Notifications & User Profile */}
      <div className="flex items-center gap-3">
        {/* Search Icon Button */}
        <button
          onClick={onOpenSearch}
          className="w-8 h-8 rounded-full bg-[#12182B] hover:bg-[#1A223B] border border-slate-700/60 flex items-center justify-center text-slate-400 hover:text-white transition-all shadow-sm"
          title="Search transactions and insights"
        >
          <Search className="w-3.5 h-3.5" />
        </button>

        {/* Notification Icon Button */}
        <button
          onClick={onOpenNotifications}
          className="relative w-8 h-8 rounded-full bg-[#12182B] hover:bg-[#1A223B] border border-slate-700/60 flex items-center justify-center text-slate-400 hover:text-white transition-all shadow-sm"
          title="Notifications & Alerts"
        >
          <Bell className="w-3.5 h-3.5" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-purple-400" />
        </button>

        {/* User Profile Capsule (Matching Reference) */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800/80 cursor-pointer group">
          <div className="relative w-8 h-8 rounded-full overflow-hidden border border-purple-500/40 bg-gradient-to-tr from-purple-700 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
            <span>AS</span>
          </div>
          <div className="flex flex-col text-left hidden sm:flex">
            <span className="text-xs font-semibold text-slate-200 group-hover:text-white transition-colors leading-tight">
              {userName}
            </span>
            <span className="text-[10px] text-slate-400 leading-tight">
              {userRole}
            </span>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
        </div>
      </div>
    </header>
  );
};
