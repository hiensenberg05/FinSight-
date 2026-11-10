import React, { useEffect } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { AIAssistantView } from './components/views/AIAssistantView';
import { DashboardView } from './components/views/DashboardView';
import { AccountsView } from './components/views/AccountsView';
import { TransactionsView } from './components/views/TransactionsView';
import { BudgetingView } from './components/views/BudgetingView';
import { SavingsGoalsView } from './components/views/SavingsGoalsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { BillsView } from './components/views/BillsView';
import { FinancialHealthView } from './components/views/FinancialHealthView';
import { ReportsView } from './components/views/ReportsView';
import { SettingsView } from './components/views/SettingsView';
import { VoiceProvider, useVoice } from './voice/VoiceContext';
import { EvidenceDrawer } from './components/chat/EvidenceDrawer';
import { AlertToast } from './components/modular/AlertToast';
import { VoiceOperationsView } from './components/views/VoiceOperationsView';

const AppContent: React.FC = () => {
  const {
    activePage,
    setActivePage,
    isEvidenceDrawerOpen,
    closeEvidenceDrawer,
    activeEvidenceItems,
  } = useVoice();

  // Read initial page from URL query
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab) {
      setActivePage(tab);
    }
  }, []);

  const renderActiveView = () => {
    switch (activePage) {
      case 'dashboard':
      case 'home':
        return <DashboardView onSelectTab={setActivePage} />;
      case 'ai-assistant':
        return <AIAssistantView onSelectTab={setActivePage} />;
      case 'accounts':
        return <AccountsView onSelectTab={setActivePage} />;
      case 'transactions':
        return <TransactionsView onSelectTab={setActivePage} />;
      case 'budgets':
      case 'budgeting':
        return <BudgetingView onSelectTab={setActivePage} />;
      case 'goals':
      case 'savings':
        return <SavingsGoalsView />;
      case 'predictive':
      case 'investments':
      case 'analytics':
        return <AnalyticsView />;
      case 'bills':
        return <BillsView />;
      case 'financial-health':
        return <FinancialHealthView />;
      case 'reports':
        return <ReportsView />;
      case 'settings':
        return <SettingsView />;
      case 'voice-operations':
        return <VoiceOperationsView />;
      default:
        return <AIAssistantView onSelectTab={setActivePage} />;
    }
  };

  return (
    <>
      <DashboardLayout activeTab={activePage} onSelectTab={setActivePage}>
        {renderActiveView()}
      </DashboardLayout>
      <EvidenceDrawer
        isOpen={isEvidenceDrawerOpen}
        onClose={closeEvidenceDrawer}
        evidence={activeEvidenceItems}
      />
      <AlertToast />
    </>
  );
};

export const App: React.FC = () => {
  return (
    <VoiceProvider>
      <AppContent />
    </VoiceProvider>
  );
};

export default App;
