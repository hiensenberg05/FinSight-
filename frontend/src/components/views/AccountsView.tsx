import React, { useState, useEffect } from 'react';
import { Landmark, ArrowRight, ShieldCheck } from 'lucide-react';
import { Account } from '../../types';
import { api } from '../../services/api';

interface AccountsViewProps {
  onSelectTab?: (tab: string) => void;
  accounts?: Account[];
}

export const AccountsView: React.FC<AccountsViewProps> = ({ onSelectTab, accounts: initialAccounts }) => {
  const [accounts, setAccounts] = useState<Account[]>(initialAccounts || []);

  useEffect(() => {
    if (initialAccounts && initialAccounts.length > 0) {
      setAccounts(initialAccounts);
      return;
    }
    api.getAccounts().then(setAccounts);
  }, [initialAccounts]);

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Header Title & Subtitle */}
      <div>
        <h2 className="text-[26px] font-extrabold tracking-tight text-metallic-silver">Accounts</h2>
        <p className="text-[13px] text-[#8E8AA5] mt-0.5">Your financial accounts in unified view</p>
      </div>

      {/* Dynamic Account Cards - Glossy Apple 3D Surface */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {accounts.map((acc, index) => (
          <div 
            key={acc.id} 
            className="rounded-2xl glass-card-3d glass-card-3d-interactive p-5 flex flex-col justify-between shadow-lg min-h-[150px] border border-white/[0.08]"
          >
            <div className="flex items-start justify-between">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-b from-white/[0.08] to-black/40 border-t border-white/[0.25] border-b border-black/50 flex items-center justify-center text-[#7C7896] shadow-md">
                <Landmark className={`w-5 h-5 ${index % 2 === 0 ? 'text-violet-300' : 'text-cyan-300'}`} />
              </div>
              <div className="flex items-center gap-1.5 text-[11.5px] text-emerald-400 font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                <span>{acc.isConnected ? 'Connected' : 'Offline'}</span>
              </div>
            </div>

            <div className="mt-4">
              <span className="text-[12.5px] font-medium text-[#8E8AA5] block">{acc.name}</span>
              <h3 className="text-[28px] font-extrabold tabular-nums tracking-tight text-metallic-platinum mt-0.5 drop-shadow-sm">
                ₹{acc.balance.toLocaleString('en-IN')}
              </h3>
              <span className="text-[12px] text-[#8E8AA5] tabular-nums block mt-1">
                {acc.bankName} ··· {acc.accountNumberMask}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Return to overview link */}
      <div className="pt-2">
        <button
          onClick={() => onSelectTab?.('dashboard')}
          className="text-[12.5px] font-semibold text-violet-400 hover:text-violet-300 flex items-center gap-1 transition-colors"
        >
          <span>← Return to overview</span>
        </button>
      </div>
    </div>
  );
};
