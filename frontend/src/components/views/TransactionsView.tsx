import React, { useState, useEffect } from 'react';
import { Search, Download, ArrowLeftRight, AlertTriangle, X } from 'lucide-react';
import { Transaction } from '../../types';
import { api } from '../../services/api';
import { formatINR } from '../../utils/formatters';
import { useVoice } from '../../voice/VoiceContext';

interface TransactionsViewProps {
  onSelectTab?: (tab: string) => void;
}

export const TransactionsView: React.FC<TransactionsViewProps> = ({ onSelectTab }) => {
  const { activeVoiceFilter, clearVoiceFilter } = useVoice();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    api.getTransactions().then((data) => {
      setTransactions(data);
      setIsLoading(false);
    });
  }, []);

  const categories = [
    'All',
    'Food & Dining',
    'Utilities',
    'Travel & Transport',
    'Shopping',
    'Subscriptions',
    'Groceries',
    'Income',
    'Health & Fitness',
    'Entertainment',
    'Electronics',
  ];

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Food & Dining':
        return '#06B6D4';
      case 'Shopping':
        return '#F59E0B';
      case 'Utilities':
        return '#8B5CF6';
      case 'Travel & Transport':
        return '#EC4899';
      case 'Subscriptions':
        return '#D946EF';
      case 'Income':
        return '#10B981';
      case 'Groceries':
        return '#10B981';
      case 'Electronics':
        return '#4F46E5';
      default:
        return '#7C7896';
    }
  };

  const filtered = transactions.filter((tx) => {
    if (activeVoiceFilter) {
      if (activeVoiceFilter.merchant && !tx.merchant.toLowerCase().includes(activeVoiceFilter.merchant.toLowerCase())) {
        return false;
      }
      if (activeVoiceFilter.category && !tx.category.toLowerCase().includes(activeVoiceFilter.category.toLowerCase())) {
        return false;
      }
    }

    const matchesSearch =
      tx.merchant.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (tx.anomalyReason && tx.anomalyReason.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'All' || tx.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const exportCSV = () => {
    const headers = 'ID,Date,Merchant,Category,Amount,Type,Channel,IsAnomaly,AnomalyReason\n';
    const rows = filtered
      .map(
        (t) =>
          `"${t.id}","${t.dateStr || t.date}","${t.merchant}","${t.category}",${t.amount},"${t.type || 'expense'}","${
            t.channel || 'UPI'
          }","${t.isAnomaly ? 'YES' : 'NO'}","${t.anomalyReason || ''}"`
      )
      .join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'finsight_transactions.csv';
    a.click();
  };

  const flaggedCount = transactions.filter((t) => t.isAnomaly).length;

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Top Header Card */}
      <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-b from-violet-500/25 to-violet-800/40 border-t border-white/[0.25] border-b border-black/40 flex items-center justify-center text-violet-300 shadow-md">
              <ArrowLeftRight className="w-4 h-4" />
            </div>
            <h2 className="text-[20px] font-extrabold text-metallic-silver tracking-tight">
              All Transactions Ledger
            </h2>
            {flaggedCount > 0 && (
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/35 text-[11.5px] font-bold text-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.25)]">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                {flaggedCount} Anomalies
              </span>
            )}
          </div>
          <p className="text-[12.5px] text-[#8E8AA5] mt-1">
            Showing <strong className="text-white tabular-nums font-semibold">{filtered.length}</strong> records from verified PostgreSQL database
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#7C7896] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search merchant, category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="glass-inset-tray border border-white/[0.08] focus:border-violet-500/50 rounded-xl pl-8 pr-3 py-1.5 text-[12.5px] text-white placeholder-[#625E7E] focus:outline-none transition-all w-60 shadow-inner"
            />
          </div>

          <button
            onClick={exportCSV}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-b from-violet-600/40 via-violet-700/50 to-indigo-900/60 border-t border-white/[0.22] border-b border-black/50 text-white text-[12.5px] font-bold shadow-[0_2px_8px_rgba(0,0,0,0.4),0_0_12px_rgba(139,92,246,0.3)] hover:brightness-110 active:scale-95 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-violet-300" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Active Voice Filter */}
      {activeVoiceFilter && (
        <div className="flex items-center gap-2 p-3 rounded-2xl glass-card-3d border-violet-500/35 shadow-md">
          <span className="text-[12.5px] font-semibold text-violet-300">
            Filtered by voice:
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-b from-violet-600 to-indigo-700 border-t border-white/[0.3] text-[12px] font-bold text-white shadow-md">
            <span>{activeVoiceFilter.merchant || activeVoiceFilter.category}</span>
            <button
              onClick={clearVoiceFilter}
              className="w-4 h-4 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors ml-0.5"
              title="Remove filter"
            >
              <X className="w-2.5 h-2.5 text-white" />
            </button>
          </span>
          <button
            onClick={clearVoiceFilter}
            className="text-[12px] text-[#8E8AA5] hover:text-white ml-auto transition-colors font-medium"
          >
            Clear filter
          </button>
        </div>
      )}

      {/* Category Filter Bar */}
      <div className="glass-inset-tray p-1.5 rounded-2xl flex items-center gap-1 overflow-x-auto pb-1.5 flex-shrink-0 scrollbar-none shadow-inner border border-white/[0.04]">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-xl text-[12px] font-bold whitespace-nowrap transition-all ${
              selectedCategory === cat
                ? 'glass-pill-active text-white'
                : 'text-[#8E8AA5] hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Transactions Table */}
      <div className="max-w-[1200px] rounded-2xl glass-card-3d overflow-hidden shadow-lg border border-slate-800/80">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-[#0E1322] border-b border-slate-800/80 text-slate-400 uppercase text-[11px] font-bold tracking-wider">
              <tr>
                <th className="py-3.5 px-5 w-28">Date</th>
                <th className="py-3.5 px-5">Merchant / Counterparty</th>
                <th className="py-3.5 px-5 w-48">Category</th>
                <th className="py-3.5 px-5 w-28">Channel</th>
                <th className="py-3.5 px-5 text-right w-36">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 text-[13px]">
                    Loading real transactions from database...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 text-[13px]">
                    No transactions match your search filter.
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => {
                  const isIncome = tx.amount > 0 || tx.type === 'income';

                  return (
                    <tr
                      key={tx.id}
                      className={`hover:bg-slate-800/30 transition-colors ${
                        tx.isAnomaly ? 'bg-amber-500/[0.04]' : ''
                      }`}
                    >
                      <td className="py-3 px-5 text-[12px] text-slate-400 font-mono font-medium whitespace-nowrap">
                        {tx.dateStr || tx.date}
                      </td>
                      <td className="py-3 px-5">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] font-semibold text-slate-100">
                            {tx.merchant}
                          </span>
                          {tx.isAnomaly && (
                            <span
                              className="flex items-center gap-1 text-[10px] font-bold text-amber-300 bg-amber-500/20 border border-amber-500/35 px-1.5 py-0.5 rounded shadow-sm"
                              title={tx.anomalyReason || 'Statistical anomaly detected'}
                            >
                              <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                              <span>{tx.anomalyReason || 'AI Flag'}</span>
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-5">
                        <span
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border border-white/[0.06]"
                          style={{
                            backgroundColor: `${getCategoryColor(tx.category)}15`,
                            color: getCategoryColor(tx.category),
                          }}
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: getCategoryColor(tx.category) }}
                          />
                          {tx.category}
                        </span>
                      </td>
                      <td className="py-3 px-5 text-[12px] text-slate-400 font-medium">
                        {tx.channel || 'UPI'}
                      </td>
                      <td className="py-3 px-5 text-right font-bold text-[13.5px] tabular-nums font-mono whitespace-nowrap">
                        <span className={isIncome ? 'text-emerald-400' : 'text-slate-100'}>
                          {isIncome ? `+${formatINR(Math.abs(tx.amount))}` : formatINR(tx.amount)}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
