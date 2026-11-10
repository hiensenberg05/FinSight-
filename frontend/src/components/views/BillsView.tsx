import React, { useState, useEffect } from 'react';
import { CalendarCheck, AlertCircle, Plus } from 'lucide-react';
import { PremiumCard } from '../common/PremiumCard';
import { Bill } from '../../types';
import { api } from '../../services/api';

interface BillsViewProps {
  bills?: Bill[];
}

export const BillsView: React.FC<BillsViewProps> = ({ bills: initialBills }) => {
  const [bills, setBills] = useState<Bill[]>(initialBills || []);

  useEffect(() => {
    if (initialBills && initialBills.length > 0) {
      setBills(initialBills);
      return;
    }
    api.getBills().then(setBills);
  }, [initialBills]);

  const toggleAutoPay = async (id: string) => {
    const target = bills.find((b) => b.id === id);
    if (!target) return;
    const newAutoPay = !target.autoPay;
    setBills(bills.map((b) => (b.id === id ? { ...b, autoPay: newAutoPay } : b)));
    await api.toggleBillAutoPay(id, newAutoPay);
  };

  const totalUpcoming = bills.reduce((acc, b) => acc + b.amount, 0);

  return (
    <div className="h-full overflow-y-auto space-y-4 pr-1 scroll-smooth">
      {/* Top Banner - Glossy Apple 3D Surface */}
      <PremiumCard className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-bold text-violet-400 uppercase tracking-widest block mb-1">
            Recurring Commitments
          </span>
          <h2 className="text-[22px] font-extrabold text-metallic-silver tracking-tight">
            Upcoming Bills & Subscriptions
          </h2>
          <p className="text-[12.5px] text-[#8E8AA5] mt-0.5">
            Total commitments next 30 days: <strong className="text-metallic-silver tabular-nums font-extrabold">₹{totalUpcoming.toLocaleString('en-IN')}</strong>
          </p>
        </div>

        <button
          onClick={() => alert('New recurring bill pattern auto-detected from statement uploads.')}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-b from-violet-600/40 via-violet-700/50 to-indigo-900/60 border-t border-white/[0.25] border-b border-black/50 text-white text-[12.5px] font-bold shadow-[0_2px_10px_rgba(0,0,0,0.5),0_0_12px_rgba(139,92,246,0.3)] hover:brightness-110 active:scale-95 transition-all"
        >
          <Plus className="w-3.5 h-3.5 text-violet-300" />
          <span>Add Recurring Bill</span>
        </button>
      </PremiumCard>

      {/* Bills Cards List */}
      <div className="space-y-3">
        {bills.map((bill) => (
          <PremiumCard
            key={bill.id}
            className={`p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
              bill.daysLeft <= 5 ? 'border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.15)]' : ''
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm shadow-md ${
                  bill.daysLeft <= 5
                    ? 'bg-amber-500/20 text-amber-300 border-t border-white/[0.25] border-b border-black/40'
                    : 'bg-gradient-to-b from-white/[0.08] to-black/40 border-t border-white/[0.25] border-b border-black/40 text-violet-300'
                }`}
              >
                {bill.daysLeft <= 5 ? (
                  <AlertCircle className="w-5 h-5 text-amber-400" />
                ) : (
                  <CalendarCheck className="w-5 h-5 text-violet-400" />
                )}
              </div>

              <div>
                <div className="flex items-center gap-2.5">
                  <h4 className="text-[14.5px] font-bold text-white">{bill.name}</h4>
                  <span className="text-[11px] text-[#8E8AA5] bg-white/[0.05] border border-white/[0.08] px-2.5 py-0.5 rounded-lg font-medium">
                    {bill.category}
                  </span>
                </div>
                <p className="text-[12px] text-[#8E8AA5] mt-0.5">
                  Due on <strong className="text-white font-semibold">{bill.dueDate}</strong> ({bill.daysLeft} days remaining)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-5 justify-between sm:justify-end">
              <span className="text-[17px] tabular-nums font-extrabold text-metallic-platinum">
                ₹{bill.amount.toLocaleString('en-IN')}
              </span>

              <button
                onClick={() => toggleAutoPay(bill.id)}
                className={`text-[12px] font-bold px-3.5 py-1.5 rounded-xl border transition-all ${
                  bill.autoPay
                    ? 'glass-pill-active text-white'
                    : 'glass-inset-tray border-white/[0.08] text-[#8E8AA5] hover:text-white'
                }`}
              >
                {bill.autoPay ? '✓ Auto-Pay Enabled' : 'Manual Payment'}
              </button>
            </div>
          </PremiumCard>
        ))}
      </div>
    </div>
  );
};
