import React from 'react';
import { Transaction } from '../../types';
import { SlidersHorizontal, ArrowUpRight } from 'lucide-react';

interface RecentTransactionsCardProps {
  transactions: Transaction[];
  onViewAll?: () => void;
}

export const RecentTransactionsCard: React.FC<RecentTransactionsCardProps> = ({
  transactions,
  onViewAll,
}) => {
  return (
    <div className="bg-[#0E1322] border border-slate-700/60 border-t-white/10 rounded-2xl p-5 shadow-panel ring-1 ring-inset ring-white/[0.04] transition-all duration-300 hover:border-purple-500/40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-slate-100 tracking-wide">
          Recent Transactions
        </h3>
        <button
          onClick={onViewAll}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
          title="Filter transactions"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Transactions Table */}
      <div className="w-full overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              <th className="pb-2 font-medium">Date</th>
              <th className="pb-2 font-medium">Merchant</th>
              <th className="pb-2 font-medium hidden sm:table-cell">Category</th>
              <th className="pb-2 font-medium text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {transactions.slice(0, 5).map((tx) => {
              const isIncome = tx.type === 'income';

              return (
                <tr
                  key={tx.id}
                  className="group hover:bg-slate-800/40 transition-colors"
                >
                  <td className="py-2 text-slate-400 text-[11px] whitespace-nowrap">
                    {tx.date}
                  </td>
                  <td className="py-2 font-medium text-slate-200 group-hover:text-white truncate max-w-[95px]">
                    {tx.merchant}
                  </td>
                  <td className="py-2 text-slate-400 text-[11px] hidden sm:table-cell truncate max-w-[85px]">
                    {tx.category}
                  </td>
                  <td
                    className={`py-2 text-right font-mono font-semibold text-[11px] whitespace-nowrap ${
                      isIncome ? 'text-emerald-400' : 'text-slate-200'
                    }`}
                  >
                    {isIncome ? '+' : '-'}₹{tx.amount.toLocaleString('en-IN')}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Link */}
      <div className="pt-2 mt-auto border-t border-slate-800/60 flex justify-end">
        <button
          onClick={onViewAll}
          className="text-[11px] font-medium text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors"
        >
          <span>View All</span>
          <ArrowUpRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
