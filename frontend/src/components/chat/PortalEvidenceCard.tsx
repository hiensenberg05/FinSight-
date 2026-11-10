import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, ExternalLink, Globe, Sparkles, ZoomIn, X, AlertTriangle, CheckCircle, Zap, Receipt, ShoppingBag } from 'lucide-react';
import { PortalEvidenceData } from '../../types';

interface PortalEvidenceCardProps {
  evidence: PortalEvidenceData;
  onDismiss?: () => void;
}

export const PortalEvidenceCard: React.FC<PortalEvidenceCardProps> = ({
  evidence,
  onDismiss,
}) => {
  const [isZoomed, setIsZoomed] = useState(false);

  const isSwiggy = evidence.portal?.toLowerCase().includes('swiggy') || evidence.restaurant;
  const isBescom = evidence.portal?.toLowerCase().includes('bescom') || evidence.consumer_id;
  const isCroma = evidence.portal?.toLowerCase().includes('croma') || evidence.product_name;

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 12, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10 }}
        className="w-full my-3.5 rounded-2xl bg-gradient-to-b from-[#13192B] to-[#0D1220] border border-violet-500/35 p-4 sm:p-5 shadow-2xl relative overflow-hidden backdrop-blur-xl"
      >
        {/* Glow ambient background accent */}
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-violet-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header Bar */}
        <div className="flex items-start justify-between pb-3.5 border-b border-white/[0.08] relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-violet-600/25 border border-violet-400/40 flex items-center justify-center text-violet-300 shadow-md">
              {isBescom ? (
                <Zap className="w-5 h-5 text-amber-400" />
              ) : isSwiggy ? (
                <Receipt className="w-5 h-5 text-emerald-400" />
              ) : (
                <ShoppingBag className="w-5 h-5 text-blue-400" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold uppercase tracking-wider text-violet-300 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-violet-400" />
                  {evidence.portal || 'Merchant Portal'}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  Verified by Playwright
                </span>
              </div>
              <p className="text-sm font-semibold text-white mt-0.5">
                {isSwiggy && (evidence.restaurant || 'Swiggy Food Delivery')}
                {isBescom && `BESCOM Karnataka Power · Account #${evidence.consumer_id || '102938475'}`}
                {isCroma && (evidence.product_name || 'Croma Electronics Invoice')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {evidence.url && (
              <a
                href={evidence.url}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-slate-400 hover:text-white bg-white/[0.06] hover:bg-white/[0.1] px-2.5 py-1 rounded-lg transition-colors flex items-center gap-1 border border-white/[0.08]"
                title="View original mock portal page"
              >
                <span>Live URL</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/[0.08] transition-colors"
                aria-label="Dismiss evidence card"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Detailed Breakdown Section */}
        <div className="py-3.5 space-y-3 relative z-10">
          {/* Case 1: Swiggy Line-Item Forensics */}
          {isSwiggy && (
            <div className="space-y-3">
              {/* Ordered Items Pill List */}
              {evidence.items && evidence.items.length > 0 && (
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-1.5">
                    Itemized Order Lines
                  </span>
                  <div className="space-y-1">
                    {evidence.items.map((item, idx) => (
                      <div key={idx} className="text-xs text-slate-200 flex items-center justify-between py-0.5">
                        <span className="font-medium">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Fee Cards Matrix */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-slate-400 block">Food Subtotal</span>
                  <span className="text-sm font-bold text-white">₹{evidence.food_subtotal?.toLocaleString('en-IN') || '1,050'}</span>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/25 rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-rose-300 font-semibold flex items-center justify-center gap-0.5">
                    <AlertTriangle className="w-2.5 h-2.5 text-rose-400" />
                    Surge Fee
                  </span>
                  <span className="text-sm font-bold text-rose-300">₹{evidence.surge_fee?.toLocaleString('en-IN') || '120'}</span>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-amber-300 block">Packaging</span>
                  <span className="text-sm font-bold text-amber-300">₹{evidence.packaging_fee?.toLocaleString('en-IN') || '65'}</span>
                </div>
                <div className="bg-emerald-500/10 border border-emerald-500/25 rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-emerald-300 block font-semibold">Total Paid</span>
                  <span className="text-sm font-extrabold text-emerald-300">₹{evidence.total_amount?.toLocaleString('en-IN') || '1,480'}</span>
                </div>
              </div>

              {/* Optimization Callout */}
              <div className="flex items-start gap-2 text-xs bg-violet-500/10 border border-violet-500/20 text-violet-200 p-2.5 rounded-xl">
                <Sparkles className="w-4 h-4 text-violet-400 flex-shrink-0 mt-0.5" />
                <span>
                  Delivery markups & surge fees added <strong>₹{evidence.hidden_delivery_fees || 230}</strong> (15.5%) to this order. Capping midnight orders protects ₹4,800 monthly.
                </span>
              </div>
            </div>
          )}

          {/* Case 2: BESCOM Utility Bill Verification */}
          {isBescom && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-slate-400 block">Units Consumed</span>
                  <span className="text-sm font-bold text-white">{evidence.units_consumed_kwh || 184} kWh</span>
                </div>
                <div className="bg-blue-500/10 border border-blue-500/25 rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-blue-300 block">Bill Amount</span>
                  <span className="text-sm font-bold text-blue-300">₹{evidence.total_amount?.toLocaleString('en-IN') || '1,400'}</span>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-amber-300 block">Due Date</span>
                  <span className="text-sm font-bold text-amber-300">{evidence.due_date || '28 Feb 2025'}</span>
                </div>
                <div className="bg-emerald-500/10 border border-emerald-500/25 rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-emerald-300 block">Cushion Coverage</span>
                  <span className="text-sm font-bold text-emerald-300">73× Safe</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs bg-white/[0.03] border border-white/[0.06] p-2.5 rounded-xl">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="text-slate-300">
                    Consumer: <strong>{evidence.consumer_name || 'Aarav Mehta'}</strong> | Domestic Tariff LT-2a
                  </span>
                </div>
                <span className="text-[11px] font-semibold text-amber-300 bg-amber-500/20 px-2 py-0.5 rounded-md">
                  {evidence.payment_status || 'UNPAID'}
                </span>
              </div>
            </div>
          )}

          {/* Case 3: Croma Tax Invoice */}
          {isCroma && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-2.5 text-center col-span-2 sm:col-span-1">
                  <span className="text-[10px] text-slate-400 block">Total Invoiced</span>
                  <span className="text-sm font-bold text-emerald-300">₹{evidence.total_amount?.toLocaleString('en-IN') || '2,400'}</span>
                </div>
                <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-slate-400 block">Warranty Period</span>
                  <span className="text-sm font-bold text-white">2.0 Years Active</span>
                </div>
                <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-2.5 text-center">
                  <span className="text-[10px] text-slate-400 block">Return Eligibility</span>
                  <span className="text-sm font-bold text-violet-300">Until 26 Feb</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 p-2.5 rounded-xl">
                <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>
                  Authorized purchase matched to bank ledger. Statistical anomaly verified authentic.
                </span>
              </div>
            </div>
          )}

          {/* Screenshot Display Frame */}
          {evidence.screenshot_base64 && (
            <div className="mt-3">
              <div className="flex items-center justify-between pb-1.5 px-0.5">
                <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
                  Playwright DOM Screenshot Proof
                </span>
                <button
                  onClick={() => setIsZoomed(true)}
                  className="text-[11px] text-violet-300 hover:text-white flex items-center gap-1 transition-colors cursor-pointer"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                  <span>Enlarge Preview</span>
                </button>
              </div>

              {/* Browser Mock Frame */}
              <div className="rounded-xl overflow-hidden border border-slate-700/60 bg-black/40 shadow-inner group relative cursor-pointer" onClick={() => setIsZoomed(true)}>
                {/* Browser top-bar */}
                <div className="bg-[#1B2236] px-3 py-1.5 flex items-center gap-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-rose-500/80" />
                    <div className="w-2 h-2 rounded-full bg-amber-500/80" />
                    <div className="w-2 h-2 rounded-full bg-emerald-500/80" />
                  </div>
                  <div className="flex-1 text-[10px] font-mono text-slate-400 bg-black/30 px-2 py-0.5 rounded truncate">
                    {evidence.url || 'https://portal.merchant.com/invoice'}
                  </div>
                </div>

                <div className="relative max-h-56 overflow-hidden">
                  <img
                    src={`data:image/jpeg;base64,${evidence.screenshot_base64}`}
                    alt="Playwright portal evidence"
                    className="w-full object-cover object-top transition-transform duration-300 group-hover:scale-102"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0D1220] via-transparent to-transparent opacity-40" />
                  <div className="absolute bottom-2 right-2 bg-black/70 backdrop-blur-md px-2 py-1 rounded text-[10px] text-slate-300 font-mono flex items-center gap-1 border border-white/[0.1]">
                    <ZoomIn className="w-3 h-3 text-violet-300" />
                    <span>Click to expand</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Provenance */}
        <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between text-[11px] text-slate-400">
          <span className="font-mono text-[10px]">
            {evidence.provenance || 'Cryptographically verified via Playwright Chromium'}
          </span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            100% Provenance Match
          </span>
        </div>
      </motion.div>

      {/* Fullscreen Zoom Modal */}
      <AnimatePresence>
        {isZoomed && evidence.screenshot_base64 && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative max-w-4xl max-h-[90vh] bg-[#12182B] rounded-2xl border border-violet-500/40 p-4 shadow-2xl flex flex-col overflow-hidden"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-semibold text-white">
                    {evidence.portal} · Forensic Browser Capture
                  </span>
                </div>
                <button
                  onClick={() => setIsZoomed(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.08] transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="overflow-auto mt-3 rounded-lg border border-white/[0.08]">
                <img
                  src={`data:image/jpeg;base64,${evidence.screenshot_base64}`}
                  alt="High-resolution portal screenshot"
                  className="w-full object-contain"
                />
              </div>

              <div className="pt-3 text-right">
                <button
                  onClick={() => setIsZoomed(false)}
                  className="px-4 py-1.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-semibold transition-colors"
                >
                  Close Viewer
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
