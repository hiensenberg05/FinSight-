import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, CheckCircle, Clock, XCircle, ArrowRight } from 'lucide-react';
import { ActionProposal } from '../../types';

interface ActionConfirmationCardProps {
  proposal: ActionProposal;
  onConfirm: (actionId: string) => Promise<boolean>;
  onCancel: (actionId: string) => Promise<boolean>;
}

export const ActionConfirmationCard: React.FC<ActionConfirmationCardProps> = ({
  proposal,
  onConfirm,
  onCancel,
}) => {
  const [secondsLeft, setSecondsLeft] = useState<number>(proposal.ttl_seconds || 300);
  const [status, setStatus] = useState<'pending' | 'executing' | 'executed' | 'cancelled' | 'expired'>('pending');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Live countdown timer for 5-minute safety TTL
  useEffect(() => {
    if (status !== 'pending') return;

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setStatus('expired');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [status]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const timeFormatted = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

  const handleConfirm = async () => {
    setStatus('executing');
    try {
      const ok = await onConfirm(proposal.action_id);
      if (ok) {
        setStatus('executed');
      } else {
        setStatus('pending');
        setErrorMessage('Failed to execute action. Please retry.');
      }
    } catch (err: any) {
      setStatus('pending');
      setErrorMessage(err?.message || 'Execution error');
    }
  };

  const handleCancel = async () => {
    try {
      await onCancel(proposal.action_id);
      setStatus('cancelled');
    } catch {
      setStatus('cancelled');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="w-full my-3 bg-[#13192B] border border-purple-500/30 rounded-2xl p-4 shadow-lg overflow-hidden backdrop-blur-md"
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-700/50">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-purple-300">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-white">
              Action Operator Proposal
            </h3>
            <span className="text-[10px] text-purple-300 font-medium">
              Human-In-The-Loop Confirmation Required
            </span>
          </div>
        </div>

        {status === 'pending' && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-slate-800 text-[11px] font-mono text-purple-300 border border-slate-700/60">
            <Clock className="w-3 h-3 text-purple-400" />
            <span>{timeFormatted}</span>
          </div>
        )}
      </div>

      {/* Proposal Body */}
      <div className="py-3.5 space-y-2">
        <p className="text-xs text-slate-200 font-medium leading-relaxed">
          {proposal.description}
        </p>

        {proposal.parameters && (
          <div className="bg-[#0B0F19] rounded-xl p-3 border border-slate-800 space-y-1.5 text-xs">
            {Object.entries(proposal.parameters).map(([key, val]) => (
              <div key={key} className="flex justify-between items-center text-[11px]">
                <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-mono text-slate-200 font-semibold">
                  {typeof val === 'number' && key.includes('amount') ? `₹${val.toLocaleString('en-IN')}` : String(val)}
                </span>
              </div>
            ))}
          </div>
        )}

        {errorMessage && (
          <p className="text-xs text-red-400">{errorMessage}</p>
        )}
      </div>

      {/* Action Buttons or Final Status */}
      {status === 'pending' && (
        <div className="flex items-center gap-2 pt-2 border-t border-slate-700/50">
          <button
            onClick={handleConfirm}
            className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-medium transition-all shadow-md flex items-center justify-center gap-1.5"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Confirm Change</span>
          </button>
          <button
            onClick={handleCancel}
            className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors border border-slate-700/60"
          >
            Cancel
          </button>
        </div>
      )}

      {status === 'executing' && (
        <div className="pt-2 text-center text-xs text-purple-300 animate-pulse font-medium">
          Applying mutation to ledger with audit record...
        </div>
      )}

      {status === 'executed' && (
        <div className="pt-2 flex items-center justify-center gap-2 text-xs text-emerald-300 font-medium bg-emerald-500/10 py-2 rounded-xl border border-emerald-500/20">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          <span>Action executed & audited successfully</span>
        </div>
      )}

      {status === 'cancelled' && (
        <div className="pt-2 flex items-center justify-center gap-2 text-xs text-slate-400 py-2 rounded-xl bg-slate-800/60 border border-slate-700/40">
          <XCircle className="w-4 h-4 text-slate-500" />
          <span>Proposal cancelled by user</span>
        </div>
      )}

      {status === 'expired' && (
        <div className="pt-2 flex items-center justify-center gap-2 text-xs text-amber-400 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
          <Clock className="w-4 h-4 text-amber-400" />
          <span>Proposal expired (5-minute safety TTL elapsed)</span>
        </div>
      )}
    </motion.div>
  );
};
