import React from 'react';
import { 
  financialSummary, 
  savedThisMonth, 
  savingsRate, 
  categoryBreakdown, 
  dailySpendingTrend, 
  allLedgerTransactions, 
  savingsGoalsList, 
  nextUpcomingBill, 
  cromaAnomalyTransaction,
  formatINR,
  formatNumberINR
} from '../data/mock';

export type IntentType =
  | 'spending_breakdown'
  | 'category_spend'
  | 'anomalies'
  | 'goal_status'
  | 'bills_due'
  | 'navigate'
  | 'filter_transactions'
  | 'transfer'
  | 'transfer_confirm'
  | 'transfer_cancel'
  | 'unknown';

export interface IntentResult {
  type: IntentType;
  spokenText: string;
  followUpChips: string[];
  targetPage?: string;
  filterPayload?: { category?: string; merchant?: string };
  transferPayload?: { payee: string; amount: number };
  card?: React.ReactNode;
  chartData?: any[];
  chartTitle?: string;
  quickActions?: string[];
}

/**
 * Keyword and regex pattern matcher for voice queries.
 * Zero-network dependency, deterministic, and instant (<10ms).
 */
export function parseIntent(
  rawTranscript: string,
  pendingTransfer?: { payee: string; amount: number } | null
): IntentResult {
  const text = rawTranscript.trim().toLowerCase();

  // 1. Pending transfer confirmation check
  if (pendingTransfer) {
    if (text.includes('yes') || text.includes('confirm') || text.includes('proceed') || text.includes('send it') || text.includes('pay')) {
      return {
        type: 'transfer_confirm',
        spokenText: `Transfer of ₹${pendingTransfer.amount.toLocaleString('en-IN')} to ${pendingTransfer.payee} has been confirmed and scheduled.`,
        followUpChips: ['View updated balance', 'Show recent transactions', 'Spending breakdown'],
      };
    }
    if (text.includes('no') || text.includes('cancel') || text.includes('stop') || text.includes('abort')) {
      return {
        type: 'transfer_cancel',
        spokenText: `Transfer of ₹${pendingTransfer.amount.toLocaleString('en-IN')} to ${pendingTransfer.payee} was cancelled.`,
        followUpChips: ['Spending breakdown', 'Upcoming bills', 'Check balance'],
      };
    }
  }

  // 2. Transfer intent: "transfer 5000 to rahul", "send 2500 to priya", "pay 1200 to urban company"
  const transferMatch = text.match(/(?:transfer|send|pay)\s+(?:₹|rs\.?|inr)?\s*([\d,]+)\s+(?:to|for)\s+([a-zA-Z\s]+)/i);
  if (transferMatch) {
    const rawAmt = transferMatch[1].replace(/,/g, '');
    const amount = parseInt(rawAmt, 10) || 1000;
    const payee = transferMatch[2].trim().replace(/\b\w/g, (c) => c.toUpperCase());

    return {
      type: 'transfer',
      spokenText: `Please confirm a transfer of ₹${amount.toLocaleString('en-IN')} to ${payee} from your Everyday account.`,
      followUpChips: ['Confirm transfer', 'Cancel transfer', 'Change amount'],
      transferPayload: { payee, amount },
    };
  }

  // 3. Navigation intents: "go to transactions", "show budgets", "open settings", "go to overview", "predictive"
  if (text.includes('go to transactions') || text.includes('open transactions') || text.includes('show transactions') || text.includes('view transactions') || text.includes('view all transactions')) {
    return {
      type: 'navigate',
      targetPage: 'transactions',
      spokenText: 'Opening your transactions ledger. Showing all recent records across the last 60 days.',
      followUpChips: ['Filter by Swiggy', 'Filter by Shopping', 'Show anomalies'],
    };
  }

  if (text.includes('go to budgets') || text.includes('show budgets') || text.includes('open budgets') || text.includes('view budgets') || text.includes('suggest budget')) {
    return {
      type: 'navigate',
      targetPage: 'budgets',
      spokenText: 'Navigating to category budgets. Your total spending is currently 12% below last month.',
      followUpChips: ['Food & Dining budget', 'Adjust limit', 'Back to Home'],
    };
  }

  if (text.includes('predictive') || text.includes('forecast') || text.includes('cash flow forecast') || text.includes('analytics')) {
    return {
      type: 'navigate',
      targetPage: 'predictive',
      spokenText: 'Opening predictive analytics. Your 3-month projected cash flow forecast is on track.',
      followUpChips: ['Show detected anomaly', 'Top frequent merchants', 'Go to Home'],
    };
  }

  if (text.includes('go to accounts') || text.includes('show accounts') || text.includes('open accounts') || text.includes('bank accounts')) {
    return {
      type: 'navigate',
      targetPage: 'accounts',
      spokenText: `Your total balance across all accounts is ${formatINR(financialSummary.totalBalance)}.`,
      followUpChips: ['View transactions', 'Transfer money', 'Back to Home'],
    };
  }

  if (text.includes('go to goals') || text.includes('show goals') || text.includes('my goals') || text.includes('savings goals')) {
    return {
      type: 'navigate',
      targetPage: 'goals',
      spokenText: 'Here are your active savings goals. You are 40% towards Goa Trip and 30% towards New Laptop.',
      followUpChips: ['Add to Goa Trip', 'New goal', 'Back to Home'],
    };
  }

  if (text.includes('go to settings') || text.includes('open settings') || text.includes('voice settings')) {
    return {
      type: 'navigate',
      targetPage: 'settings',
      spokenText: 'Opening system settings. You can configure your profile, voice engine, and demo mode here.',
      followUpChips: ['Enable Demo Mode', 'Change voice language', 'Back to Home'],
    };
  }

  if (text.includes('go home') || text.includes('go to home') || text.includes('overview') || text.includes('dashboard')) {
    return {
      type: 'navigate',
      targetPage: 'dashboard',
      spokenText: 'Here is your financial overview dashboard with your balance, spending trend, and category breakdown.',
      followUpChips: ['Spending breakdown', 'Upcoming bills', 'Check anomalies'],
    };
  }

  // 4. Filter transactions by merchant or category
  if (text.includes('filter') || text.includes('transactions for') || text.includes('orders for') || text.includes('show me swiggy') || text.includes('show me zomato')) {
    let merchant: string | undefined;
    let category: string | undefined;

    if (text.includes('swiggy')) merchant = 'Swiggy';
    else if (text.includes('zomato')) merchant = 'Zomato';
    else if (text.includes('croma')) merchant = 'Croma Retail';
    else if (text.includes('spotify')) merchant = 'Spotify';
    else if (text.includes('air india')) merchant = 'Air India';
    else if (text.includes('urban company')) merchant = 'Urban Company';
    else if (text.includes('uber')) merchant = 'Uber';
    else if (text.includes('food')) category = 'Food & Dining';
    else if (text.includes('shopping')) category = 'Shopping';
    else if (text.includes('travel')) category = 'Travel';
    else if (text.includes('utilities') || text.includes('bills')) category = 'Bills & Utilities';

    if (merchant || category) {
      return {
        type: 'filter_transactions',
        targetPage: 'transactions',
        filterPayload: { merchant, category },
        spokenText: `Filtering your transactions ledger for ${merchant || category}.`,
        followUpChips: ['Clear filter', 'Export CSV', 'Back to Home'],
      };
    }
  }

  // 5. Category spend query: "how much on food", "how much did I spend on shopping", "transport spend"
  for (const cat of categoryBreakdown) {
    const catNameLower = cat.name.toLowerCase();
    const keywords = catNameLower.split('&').map((k) => k.trim());
    const matchesCat = keywords.some((kw) => text.includes(kw));

    if (matchesCat && (text.includes('spend') || text.includes('spent') || text.includes('how much') || text.includes('cost') || text.includes('breakdown') || text.includes('share'))) {
      return {
        type: 'category_spend',
        spokenText: `You have spent ${formatINR(cat.amount)} on ${cat.name} this month, representing ${cat.percentage}% of your total expenditure.`,
        followUpChips: [`Compare ${cat.name} with last month`, 'Show transactions in this category', 'Overall spending breakdown'],
        card: {
          categoryName: cat.name,
          amount: cat.amount,
          percentage: cat.percentage,
          color: cat.color,
        } as any,
      };
    }
  }

  // 6. Anomalies query: "any anomalies", "unusual transactions", "fraud", "flagged spend", "suspicions"
  if (text.includes('anomal') || text.includes('unusual') || text.includes('fraud') || text.includes('flagged') || text.includes('suspicio') || text.includes('spike') || text.includes('irregular') || text.includes('fishy') || text.includes('strange')) {
    return {
      type: 'anomalies',
      spokenText: `We detected an unusual debit of ${formatINR(Math.abs(cromaAnomalyTransaction.amount))} at ${cromaAnomalyTransaction.merchant} on ${cromaAnomalyTransaction.dateStr}.`,
      followUpChips: ['View in ledger', 'Mark as expected', 'Show spending breakdown'],
      card: {
        anomaly: cromaAnomalyTransaction,
      } as any,
    };
  }

  // 7. Goals query: "goa trip goal", "laptop goal", "how are my savings goals", "goal progress"
  if (text.includes('goal') || text.includes('goa') || text.includes('laptop') || text.includes('trip') || text.includes('saving')) {
    const isGoa = text.includes('goa') || text.includes('trip');
    const isLaptop = text.includes('laptop');
    const targetGoal = isLaptop ? savingsGoalsList[1] : savingsGoalsList[0];

    return {
      type: 'goal_status',
      spokenText: `Your ${targetGoal.name} goal has reached ${formatINR(targetGoal.saved)} of ${formatINR(targetGoal.target)} (${targetGoal.percentage}%). Estimated completion is in 4 months.`,
      followUpChips: ['Add ₹5,000 to goal', 'Show other goals', 'Go to Goals page'],
      card: {
        goal: targetGoal,
      } as any,
    };
  }

  // 8. Upcoming bills query: "what bills are due", "upcoming bills", "electricity bill", "next bill"
  if (text.includes('bill') || text.includes('due') || text.includes('utility') || text.includes('electricity') || text.includes('broadband')) {
    return {
      type: 'bills_due',
      spokenText: `Your next bill is ${nextUpcomingBill.title} for ${formatINR(nextUpcomingBill.amount)}, due in ${nextUpcomingBill.dueInDays} days. You have 3 bills totaling ${formatINR(financialSummary.upcomingBills)}.`,
      followUpChips: ['Pay Electricity bill', 'View all upcoming bills', 'Spending breakdown'],
      card: {
        nextBill: nextUpcomingBill,
        totalBills: financialSummary.upcomingBills,
        billsCount: financialSummary.upcomingBillsCount,
      } as any,
    };
  }

  // 9. Overall spending breakdown query: "spending breakdown", "how much did I spend", "expenses this month", "show breakdown"
  if (text.includes('spending') || text.includes('breakdown') || text.includes('expense') || text.includes('how much') || text.includes('total spend') || text.includes('money')) {
    return {
      type: 'spending_breakdown',
      spokenText: `You have spent ${formatINR(financialSummary.spendingThisMonth)} across 6 categories this month, which is 12% lower than last month.`,
      followUpChips: ['Compare with last month', 'Which category grew most?', 'Show Food & Dining'],
      card: {
        total: financialSummary.spendingThisMonth,
        categories: categoryBreakdown,
      } as any,
    };
  }

  // 10. Fallback / Unknown
  return {
    type: 'unknown',
    spokenText: 'I can help with spending breakdowns, category expenses, upcoming bills, goals, and transfers. Try asking "How much did I spend on food?"',
    followUpChips: ['Spending breakdown', 'How much on food?', 'Any anomalies?'],
  };
}
