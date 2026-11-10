import React from 'react';
import { 
  TrendingDown, 
  Target, 
  Calendar, 
  Wallet, 
  ArrowLeftRight, 
  Zap, 
  Sparkles 
} from 'lucide-react';

interface QuickActionChipsProps {
  onSelectAction: (actionText: string) => void;
  selectedAction?: string | null;
}

export const QuickActionChips: React.FC<QuickActionChipsProps> = ({
  onSelectAction,
  selectedAction,
}) => {
  const chips = [
    { label: 'Spending', icon: TrendingDown, query: 'Show me my spending breakdown for this month.' },
    { label: 'Suggest Budget', icon: Target, query: 'Suggest an optimized monthly budget based on my transactions.' },
    { label: 'Upcoming Bills', icon: Calendar, query: 'What are my upcoming recurring bills and payments?' },
    { label: 'Current Saving Balance', icon: Wallet, query: 'What is my current savings balance and net savings rate?' },
    { label: 'UPI Spending', icon: Zap, query: 'How much did I spend through UPI this month, and who are my top merchants?' },
    { label: 'Transfer Analysis', icon: ArrowLeftRight, query: 'Analyze my internal transfers and account-to-account movements.' },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 py-2">
      {chips.map((chip) => {
        const Icon = chip.icon;
        const isSelected = selectedAction === chip.label;

        return (
          <button
            key={chip.label}
            onClick={() => onSelectAction(chip.query)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 border ${
              isSelected
                ? 'bg-purple-600/30 border-purple-500 text-white shadow-glow-purple'
                : 'bg-[#12182B] hover:bg-[#182038] border-slate-700/60 hover:border-purple-500/40 text-slate-300 hover:text-white'
            }`}
          >
            <Icon className="w-3.5 h-3.5 text-purple-400" />
            <span>{chip.label}</span>
          </button>
        );
      })}
    </div>
  );
};
