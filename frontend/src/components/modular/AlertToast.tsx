import React from 'react';
import { ArrowRight, X, AlertTriangle, ShieldAlert } from 'lucide-react';
import { useVoice } from '../../voice/VoiceContext';

interface AlertToastProps {
  onAction?: () => void;
}

export const AlertToast: React.FC<AlertToastProps> = ({ onAction }) => {
  const { proactiveAlerts, dismissProactiveAlert, setActivePage } = useVoice();

  // If there are real backend proactive alerts, show the top unacknowledged alert
  const activeAlert = proactiveAlerts.length > 0 ? proactiveAlerts[0] : null;

  if (!activeAlert) return null;

  const handleDismiss = () => {
    dismissProactiveAlert(activeAlert.alert_id);
  };

  const handleAction = () => {
    if (activeAlert?.category?.toLowerCase().includes('food') || activeAlert?.type === 'budget_threshold') {
      setActivePage('budgets');
    } else if (activeAlert?.type === 'upcoming_bill') {
      setActivePage('bills');
    } else if (activeAlert?.type === 'spending_spike') {
      setActivePage('transactions');
    } else {
      onAction?.();
    }
    handleDismiss();
  };

  const title = activeAlert.title;
  const detail = activeAlert.detail;
  const isCritical = activeAlert?.severity === 'critical';

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-5 right-6 z-40 max-w-sm rounded-2xl bg-[#111018]/95 border border-purple-500/30 shadow-2xl p-3.5 flex items-start gap-3 backdrop-blur-md animate-in fade-in slide-in-from-bottom-3 duration-200"
    >
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
          isCritical
            ? 'bg-rose-500/15 border border-rose-500/30 text-rose-400'
            : 'bg-amber-500/15 border border-amber-500/30 text-amber-400'
        }`}
      >
        {isCritical ? <ShieldAlert className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-white tracking-tight truncate">
            {title}
          </span>
          <button
            onClick={handleDismiss}
            aria-label="Dismiss notification"
            className="text-slate-400 hover:text-white p-0.5 rounded transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <p className="text-[11px] text-slate-300 mt-0.5 leading-snug">
          {detail}
        </p>

        <div className="mt-2.5 flex items-center gap-2">
          <button
            onClick={handleAction}
            className="px-2.5 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-[11px] font-semibold flex items-center gap-1.5 transition-colors shadow-sm cursor-pointer"
          >
            <span>Review & Action</span>
            <ArrowRight className="w-3 h-3" />
          </button>
          <button
            onClick={handleDismiss}
            className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white text-[11px] font-medium transition-colors cursor-pointer"
          >
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
};
