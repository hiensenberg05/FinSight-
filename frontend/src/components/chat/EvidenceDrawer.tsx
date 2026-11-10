import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShieldCheck, Database, Calendar, CreditCard, AlertTriangle, Hash } from 'lucide-react';
import { EvidenceItem } from '../../types';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceItem[];
  metadata?: {
    calculation_period?: string;
    aggregation_methodology?: string;
    record_count?: number;
    executed_at?: string;
  };
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  evidence,
  metadata,
}) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Slide-out Drawer */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 300 }}
          className="relative w-full max-w-lg h-full bg-[#0E1322] border-l border-slate-700/60 shadow-2xl flex flex-col z-10"
        >
          {/* Header */}
          <div className="p-5 border-b border-slate-700/50 bg-[#12182B] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                  Verified Data Provenance
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 font-mono">
                    {evidence.length} Records
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  Direct ledger references grounded in indexed SQL tables
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Metadata Banner */}
          {metadata && (
            <div className="p-4 bg-[#141B30]/60 border-b border-slate-700/40 text-xs text-slate-300 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Calculation Period:</span>
                <span className="font-mono text-purple-300">{metadata.calculation_period || 'Current Cycle'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Aggregation Methodology:</span>
                <span className="text-slate-200 text-right font-medium max-w-[260px] truncate">
                  {metadata.aggregation_methodology || 'SUM(abs(amount_minor)) GROUP BY category'}
                </span>
              </div>
            </div>
          )}

          {/* Transaction List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {evidence.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-slate-400 text-center">
                <Database className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-xs">No specific transaction references in this turn.</p>
              </div>
            ) : (
              evidence.map((item) => (
                <div
                  key={item.transaction_id}
                  className="bg-[#141B30] border border-slate-700/50 hover:border-purple-500/40 rounded-xl p-3.5 transition-all shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <div className="text-xs font-semibold text-slate-100 flex items-center gap-2">
                        <span>{item.merchant}</span>
                        {item.is_anomaly && (
                          <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            <AlertTriangle className="w-2.5 h-2.5" />
                            Outlier
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-purple-300 font-medium">
                        {item.category}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-bold font-mono text-white">
                        {item.amount_formatted}
                      </span>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {item.payment_mode || 'UPI'}
                      </div>
                    </div>
                  </div>

                  {item.anomaly_reason && (
                    <div className="text-[11px] text-amber-200/90 bg-amber-500/10 rounded px-2 py-1 mb-2 border border-amber-500/20">
                      {item.anomaly_reason}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {item.date}
                    </span>
                    <span className="flex items-center gap-1 text-slate-300">
                      <CreditCard className="w-3 h-3 text-slate-500" />
                      {item.account_reference}
                    </span>
                  </div>

                  <div className="mt-1 text-[9px] text-slate-500 font-mono flex items-center gap-1 truncate">
                    <Hash className="w-2.5 h-2.5 text-slate-600" />
                    ID: {item.transaction_id}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-700/50 bg-[#12182B] text-center">
            <span className="text-[11px] text-slate-400 flex items-center justify-center gap-1.5 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              100% Deterministic Financial Tool Evidence Layer
            </span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
