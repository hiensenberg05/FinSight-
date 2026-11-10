import React, { useState } from 'react';
import { 
  Home, 
  Radio, 
  CreditCard, 
  ArrowLeftRight, 
  SlidersHorizontal, 
  TrendingUp, 
  Target, 
  FileText, 
  Search, 
  Bell, 
  ChevronRight,
  ChevronDown,
  Sparkles,
  Settings,
  Activity,
} from 'lucide-react';
import { userProfile } from '../../data/mock';
import { GlobalVoiceDock } from '../voice/GlobalVoiceDock';
import { useVoice } from '../../voice/VoiceContext';

interface DashboardLayoutProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  activeTab,
  onSelectTab,
  children,
}) => {
  const [showNotificationPopup, setShowNotificationPopup] = useState(false);
  const { isMicOn, isWsConnected } = useVoice();

  const navItems = [
    { id: 'dashboard', label: 'Home', icon: Home },
    { id: 'ai-assistant', label: 'AI Assistant', icon: Radio },
    { id: 'accounts', label: 'Accounts', icon: CreditCard },
    { id: 'transactions', label: 'Transactions', icon: ArrowLeftRight },
    { id: 'budgets', label: 'Budgets', icon: SlidersHorizontal },
    { id: 'predictive', label: 'Predictive', icon: TrendingUp },
    { id: 'goals', label: 'Goals', icon: Target },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'voice-operations', label: 'Voice Operations', icon: Activity },
  ];

  return (
    <div className="relative h-[100dvh] h-screen w-screen bg-ambient-3d text-white overflow-hidden select-none font-sans flex">
      {/* =========================================================================
          1. Left Sidebar: Fixed ~240px
         ========================================================================= */}
      <aside 
        aria-label="Main Navigation"
        className="w-[240px] h-full bg-[#0D111A] border-r border-slate-800/80 flex flex-col justify-between p-3.5 flex-shrink-0 z-20"
      >
        <div className="flex flex-col min-h-0">
          {/* Logo Brand: Indigo badge + FinSight */}
          <div 
            onClick={() => onSelectTab('dashboard')}
            className="flex items-center gap-3 px-1.5 py-1 mb-4 cursor-pointer group focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-xl"
            tabIndex={0}
            role="button"
            onKeyDown={(e) => e.key === 'Enter' && onSelectTab('dashboard')}
          >
            <div className="w-8 h-8 rounded-full bg-[#6366F1] border border-indigo-400/40 flex items-center justify-center shadow-[0_0_12px_rgba(99,102,241,0.4)] flex-shrink-0">
              <span className="text-white text-xs flex flex-col items-center justify-center gap-0.5">
                <span className="w-3.5 h-[2px] bg-white rounded-full" />
                <span className="w-3.5 h-[2px] bg-white rounded-full" />
                <span className="w-2.5 h-[2px] bg-white rounded-full" />
              </span>
            </div>
            <div className="min-w-0">
              <h1 className="text-[16px] font-bold tracking-tight text-white leading-tight">
                FinSight
              </h1>
            </div>
          </div>

          {/* Navigation Items List */}
          <nav className="space-y-0.5 overflow-y-auto pr-0.5 flex-1 min-h-0 scrollbar-none">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`relative w-full flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] font-semibold transition-all select-none focus-visible:ring-1 focus-visible:ring-indigo-400 focus-visible:outline-none ${
                    isActive
                      ? 'glass-pill-active text-white shadow-lg'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-indigo-200' : 'text-slate-400'}`} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Pinned Sidebar Items (Settings + Upgrade Card + User Capsule) */}
        <div className="space-y-2.5 pt-2 border-t border-slate-800/80 flex-shrink-0">
          {/* Settings Nav Item */}
          <button
            onClick={() => onSelectTab('settings')}
            className={`w-full flex items-center gap-3 px-3 py-1.5 rounded-xl text-[12.5px] font-medium transition-colors ${
              activeTab === 'settings'
                ? 'bg-[#1E293B] text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/30'
            }`}
          >
            <Settings className="w-4 h-4 text-slate-400" />
            <span>Settings</span>
          </button>

          {/* Upgrade to Pro Card */}
          <div className="rounded-xl glass-card-3d glass-card-3d-interactive p-2.5 flex items-start gap-2.5 cursor-pointer border border-slate-800/80">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[12px] font-bold text-slate-100 block leading-tight">
                Upgrade to Pro
              </span>
              <p className="text-[10px] text-slate-400 leading-tight mt-0.5 truncate">
                Institutional-grade forecasting
              </p>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-500 mt-1" />
          </div>

          {/* User Profile Capsule in Sidebar */}
          <div className="flex items-center justify-between px-2 py-1.5 rounded-xl hover:bg-slate-800/30 transition-colors cursor-pointer">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0 border border-indigo-400/30">
                {userProfile.initials}
              </div>
              <div className="truncate">
                <span className="text-[11.5px] font-bold text-white block truncate leading-tight">
                  {userProfile.name}
                </span>
                <span className="text-[10px] text-slate-400 block truncate leading-tight">
                  {userProfile.plan}
                </span>
              </div>
            </div>
            <ChevronRight className="w-3 h-3 text-slate-500 flex-shrink-0" />
          </div>
        </div>
      </aside>

      {/* =========================================================================
          2. Main Application Workspace Area
         ========================================================================= */}
      <div className="flex-1 min-w-0 flex flex-col h-full overflow-hidden bg-transparent">
        {/* Top Header Navbar: Search + Status Badge + Bell + User Capsule */}
        <header className="h-12 px-6 flex items-center justify-between flex-shrink-0 bg-[#0B0F17]/80 backdrop-blur-xl relative z-30 border-b border-slate-800/80">
          {/* Left / Status Badge */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#111622] border border-slate-700/80 text-[11px] font-medium text-slate-300">
              <span className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span>{isWsConnected ? '14ms Gateway Connected' : 'Gateway Offline'}</span>
            </div>

            {/* Mic Active Trust Badge */}
            {isMicOn && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/15 border border-rose-500/30 text-[11px] font-semibold text-rose-300 animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                <span>Mic Active</span>
              </div>
            )}
          </div>

          {/* Right Controls: Search, Bell, User Capsule */}
          <div className="flex items-center gap-3">
            {/* Search Box with ⌘ K chip */}
            <div className="relative hidden md:block w-72">
              <input
                type="text"
                placeholder="Search transactions, merchants, or goals..."
                className="w-full glass-inset-tray border border-slate-700/80 rounded-xl pl-8 pr-12 py-1.5 text-[12px] text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500/60 transition-colors shadow-inner"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5 pointer-events-none" />
              <div className="absolute right-2 top-1.5 px-1.5 py-0.5 rounded-lg bg-slate-800/60 border border-slate-700/80 text-[9px] font-semibold text-slate-400 pointer-events-none">
                ⌘ K
              </div>
            </div>

            {/* Notification Bell Button */}
            <div className="relative">
              <button 
                aria-label="Notifications"
                onClick={() => setShowNotificationPopup(!showNotificationPopup)}
                className="relative w-8 h-8 rounded-full glass-card-3d flex items-center justify-center text-slate-400 hover:text-white transition-colors border border-slate-700/80"
              >
                <Bell className="w-3.5 h-3.5" />
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e]" />
              </button>

              {showNotificationPopup && (
                <div className="absolute right-0 top-11 w-52 rounded-xl glass-card-3d border border-slate-700/80 p-3 shadow-2xl z-50 backdrop-blur-2xl">
                  <span className="text-[12px] font-semibold text-white block">You're all caught up</span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">No new financial alerts.</span>
                </div>
              )}
            </div>

            {/* User Profile Capsule */}
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full glass-card-3d cursor-pointer hover:border-indigo-500/40 transition-colors border border-slate-700/80">
              <div className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0 shadow-sm border border-white/[0.2]">
                {userProfile.initials}
              </div>
              <div className="text-left leading-tight hidden sm:block pr-1">
                <span className="text-[11px] font-extrabold text-metallic-silver block leading-none">
                  {userProfile.name}
                </span>
                <span className="text-[9px] text-slate-400 block leading-none mt-0.5 font-medium">
                  {userProfile.plan}
                </span>
              </div>
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </div>
          </div>
        </header>

        {/* 3. Main Workspace Container */}
        <main className="flex-1 min-h-0 px-6 py-3 pb-24 overflow-y-auto scrollbar-none relative">
          {children}
        </main>

        {/* 4. Global Voice Dock: Persistent on EVERY page */}
        <GlobalVoiceDock />
      </div>
    </div>
  );
};

