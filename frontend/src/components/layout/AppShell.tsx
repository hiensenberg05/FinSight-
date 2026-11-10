import React from 'react';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';

interface AppShellProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenUpload?: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeTab,
  onSelectTab,
  onOpenUpload,
  children,
}) => {
  const getTabTitle = (tab: string) => {
    switch (tab) {
      case 'dashboard': return 'Dashboard Overview';
      case 'budgeting': return 'Budgeting & Expense Limits';
      case 'savings': return 'Savings Goals & Planning';
      case 'analytics': return 'UPI & Cash-Flow Analytics';
      case 'transactions': return 'All Transactions';
      case 'bills': return 'Bills & Recurring Payments';
      case 'ai-assistant': return 'AI Assistant';
      case 'financial-health': return 'Financial Health Index';
      case 'reports': return 'Financial Reports';
      default: return 'AI Assistant';
    }
  };

  return (
    <div className="h-screen w-screen bg-[#060810] flex items-center justify-center p-2 sm:p-3 md:p-4 select-none font-sans overflow-hidden">
      {/* Outer Application Container Frame (Matching FinWise reference rounded frame) */}
      <div className="w-full max-w-[1560px] h-full bg-[#080B14] border border-slate-700/60 border-t-white/10 rounded-3xl shadow-[0_25px_70px_-15px_rgba(0,0,0,0.9)] flex overflow-hidden ring-1 ring-inset ring-white/[0.04]">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={onSelectTab}
          onOpenUpload={onOpenUpload}
        />

        {/* Main Application Area (Strictly Constrained Flexbox to prevent nested overflows) */}
        <div className="flex-1 min-w-0 flex flex-col h-full overflow-hidden bg-[#080B14]">
          {/* Top Header Navbar */}
          <TopNavbar
            currentTabName={getTabTitle(activeTab)}
            userName="Aarav Sharma"
            userRole="Tech Professional"
            onOpenSearch={() => alert('Search: Filter by UPI merchant, date, or amount.')}
            onOpenNotifications={() => alert('Notifications: Recurring bill reminder for Netflix (₹649) due tomorrow.')}
          />

          {/* Application Two-Column Content Workspace */}
          <main className="flex-1 min-h-0 p-3 sm:p-3.5 overflow-hidden">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};
