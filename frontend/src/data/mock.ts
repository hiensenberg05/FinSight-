/**
 * Single source of truth for FinSight
 * Both Screen A (Voice Assistant) and Screen B (Overview) import from this file.
 * Nothing is hardcoded in individual components.
 */

// Currency formatting helper strictly adhering to en-IN (Indian lakh grouping)
export const formatINR = (value: number, includeDecimals = false): string => {
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: includeDecimals ? 2 : 0,
    maximumFractionDigits: includeDecimals ? 2 : 0,
  });
  return formatter.format(value);
};

// Raw Number formatter with en-IN grouping (without ₹ symbol)
export const formatNumberINR = (value: number): string => {
  return new Intl.NumberFormat('en-IN').format(value);
};

// User Profile
export const userProfile = {
  name: 'Aarav Mehta',
  initials: 'AM',
  plan: 'Personal Plan',
};

// Core Financial Totals
export const financialSummary = {
  totalBalance: 124500,
  balanceTrend: '2.4%',
  incomeThisMonth: 65000,
  incomeTrend: '6.3%',
  spendingThisMonth: 48320,
  spendingTrend: '12.1%',
  upcomingBills: 3200,
  upcomingBillsCount: 3,
  investments: 234920,
  investmentsTrend: '12%',
  healthScore: 78,
  healthScoreDelta: '+6 this month',
  healthStatus: 'Good' as const,
  healthDescription: "You're on track! Keep your spending in check to reach 80+.",
};

// Computed savings and savings rate
export const savedThisMonth = financialSummary.incomeThisMonth - financialSummary.spendingThisMonth; // 16,680
export const savingsRate = Math.round((savedThisMonth / financialSummary.incomeThisMonth) * 100); // 26%
export const savingsRateTrend = '4 pp';

// 6 Core Categories summing exactly to 48,320
export interface CategorySpend {
  name: string;
  percentage: number;
  amount: number;
  color: string;
}

export const categoryBreakdown: CategorySpend[] = [
  { name: 'Housing', percentage: 32, amount: 15462, color: '#8B5CF6' },       // Violet
  { name: 'Food & Dining', percentage: 18, amount: 8698, color: '#06B6D4' },  // Cyan
  { name: 'Transport', percentage: 12, amount: 5798, color: '#EC4899' },      // Pink
  { name: 'Shopping', percentage: 14, amount: 6765, color: '#F59E0B' },       // Amber
  { name: 'Subscriptions', percentage: 8, amount: 3866, color: '#D946EF' },   // Magenta
  { name: 'Others', percentage: 16, amount: 7731, color: '#3B82F6' },         // Blue
];

// Helper to calculate relative date labels
export const getRelativeDate = (daysAgo: number): string => {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

// Helper for formatted today's date
export const getTodayFormatted = (): string => {
  return new Date().toLocaleDateString('en-IN', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

// 30 Deterministic seeded daily spend values summing to exactly 48,320
// Max day is under 6,000. Yesterday is index 28 (highlighted).
const dailySpendRaw = [
  1911, 977, 1352, 1274, 2044, 1955, 2278, 1070, 1572, 984,
  1267, 1698, 979, 1238, 1914, 1757, 1270, 1823, 2154, 949,
  2148, 1987, 1450, 1173, 2375, 1444, 1079, 1085, 3208, 1905
];

export interface DailySpendPoint {
  dayIndex: number;
  dateLabel: string;
  amount: number;
  isYesterday: boolean;
  isToday: boolean;
}

export const dailySpendingTrend: DailySpendPoint[] = dailySpendRaw.map((amount, idx) => {
  const daysAgo = 29 - idx;
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);

  return {
    dayIndex: idx + 1,
    dateLabel: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    amount,
    isYesterday: daysAgo === 1,
    isToday: daysAgo === 0,
  };
});

// Shared Recent Transactions
export interface Transaction {
  id: string;
  merchant: string;
  category: string;
  amount: number; // negative for expenses, positive for income
  daysAgo: number;
  dateStr: string;
  initial: string;
  badgeBg: string;
  channel?: string;
  isAnomaly?: boolean;
  anomalyReason?: string;
  type?: 'expense' | 'income';
}

export const transactionsList: Transaction[] = [
  {
    id: 'tx-1',
    merchant: 'Zomato',
    category: 'Food & Dining',
    amount: -628,
    daysAgo: 1,
    dateStr: getRelativeDate(1),
    initial: 'Z',
    badgeBg: '#E23744',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-2',
    merchant: 'Swiggy',
    category: 'Food & Dining',
    amount: -450,
    daysAgo: 2,
    dateStr: getRelativeDate(2),
    initial: 'S',
    badgeBg: '#FC8019',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-3',
    merchant: 'Urban Company',
    category: 'Home Services',
    amount: -1200,
    daysAgo: 3,
    dateStr: getRelativeDate(3),
    initial: 'U',
    badgeBg: '#252536',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-4',
    merchant: 'Spotify',
    category: 'Subscriptions',
    amount: -119,
    daysAgo: 4,
    dateStr: getRelativeDate(4),
    initial: 'S',
    badgeBg: '#1DB954',
    channel: 'Card',
    type: 'expense',
  },
  {
    id: 'tx-5',
    merchant: 'Air India',
    category: 'Travel',
    amount: -12430,
    daysAgo: 5,
    dateStr: getRelativeDate(5),
    initial: 'A',
    badgeBg: '#D9383A',
    channel: 'Card',
    type: 'expense',
  },
];

// Exact Anomaly Transaction for Croma Retail (Shared between Ledger & Predictive page)
export const cromaAnomalyTransaction: Transaction = {
  id: 'tx-croma-anomaly',
  merchant: 'Croma Retail Electronics',
  category: 'Shopping',
  amount: -2400,
  daysAgo: 14,
  dateStr: getRelativeDate(14),
  initial: 'C',
  badgeBg: '#00838F',
  channel: 'Card',
  isAnomaly: true,
  anomalyReason: 'Unusual electronics debit: 4.2x typical shopping category average',
  type: 'expense',
};

// Full 60-day Ledger Transactions (Deriving dates relative to today)
export const allLedgerTransactions: Transaction[] = [
  ...transactionsList,
  {
    id: 'tx-6',
    merchant: 'Blinkit',
    category: 'Groceries',
    amount: -840,
    daysAgo: 7,
    dateStr: getRelativeDate(7),
    initial: 'B',
    badgeBg: '#F7CB15',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-7',
    merchant: 'Uber India',
    category: 'Transport',
    amount: -380,
    daysAgo: 10,
    dateStr: getRelativeDate(10),
    initial: 'U',
    badgeBg: '#111111',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-8',
    merchant: 'Salary Credit',
    category: 'Income',
    amount: 65000,
    daysAgo: 12,
    dateStr: getRelativeDate(12),
    initial: 'S',
    badgeBg: '#10B981',
    channel: 'NEFT',
    type: 'income',
  },
  cromaAnomalyTransaction,
  {
    id: 'tx-10',
    merchant: 'Starbucks Coffee',
    category: 'Food & Dining',
    amount: -420,
    daysAgo: 17,
    dateStr: getRelativeDate(17),
    initial: 'S',
    badgeBg: '#00704A',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-11',
    merchant: 'Tata Power Electricity',
    category: 'Bills & Utilities',
    amount: -1850,
    daysAgo: 21,
    dateStr: getRelativeDate(21),
    initial: 'T',
    badgeBg: '#003366',
    channel: 'NetBanking',
    type: 'expense',
  },
  {
    id: 'tx-12',
    merchant: 'Amazon India',
    category: 'Shopping',
    amount: -1499,
    daysAgo: 24,
    dateStr: getRelativeDate(24),
    initial: 'A',
    badgeBg: '#FF9900',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-13',
    merchant: 'Swiggy',
    category: 'Food & Dining',
    amount: -620,
    daysAgo: 27,
    dateStr: getRelativeDate(27),
    initial: 'S',
    badgeBg: '#FC8019',
    channel: 'UPI',
    isAnomaly: true,
    anomalyReason: 'Potential duplicate debit detected within 2-minute window',
    type: 'expense',
  },
  {
    id: 'tx-14',
    merchant: 'Cult.fit Gym',
    category: 'Health & Fitness',
    amount: -1200,
    daysAgo: 31,
    dateStr: getRelativeDate(31),
    initial: 'C',
    badgeBg: '#FF3278',
    channel: 'Card',
    type: 'expense',
  },
  {
    id: 'tx-15',
    merchant: 'Reliance Fresh',
    category: 'Groceries',
    amount: -2150,
    daysAgo: 36,
    dateStr: getRelativeDate(36),
    initial: 'R',
    badgeBg: '#006699',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-16',
    merchant: 'Airtel Broadband',
    category: 'Bills & Utilities',
    amount: -1050,
    daysAgo: 41,
    dateStr: getRelativeDate(41),
    initial: 'A',
    badgeBg: '#E40000',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-17',
    merchant: 'Salary Credit',
    category: 'Income',
    amount: 65000,
    daysAgo: 43,
    dateStr: getRelativeDate(43),
    initial: 'S',
    badgeBg: '#10B981',
    channel: 'NEFT',
    type: 'income',
  },
  {
    id: 'tx-18',
    merchant: 'Shell Petrol Station',
    category: 'Transport',
    amount: -1650,
    daysAgo: 47,
    dateStr: getRelativeDate(47),
    initial: 'S',
    badgeBg: '#FFD700',
    channel: 'Card',
    type: 'expense',
  },
  {
    id: 'tx-19',
    merchant: 'Myntra Fashion',
    category: 'Shopping',
    amount: -2890,
    daysAgo: 52,
    dateStr: getRelativeDate(52),
    initial: 'M',
    badgeBg: '#FF3F6C',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-20',
    merchant: 'Apollo Pharmacy',
    category: 'Health & Fitness',
    amount: -640,
    daysAgo: 56,
    dateStr: getRelativeDate(56),
    initial: 'A',
    badgeBg: '#008855',
    channel: 'UPI',
    type: 'expense',
  },
  {
    id: 'tx-21',
    merchant: 'BookMyShow',
    category: 'Entertainment',
    amount: -750,
    daysAgo: 59,
    dateStr: getRelativeDate(59),
    initial: 'B',
    badgeBg: '#C4242D',
    channel: 'UPI',
    type: 'expense',
  },
];

// Next upcoming bill for AI Assistant
export const nextUpcomingBill = {
  title: 'Electricity (Tata Power)',
  amount: 1850,
  dueInDays: 3,
  category: 'Bills & Utilities',
};

// Predictive Forecast Horizon Data (Relative to current month: 6 months actuals + 3 months forecast)
export const getForecastHorizonData = () => {
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const today = new Date();
  const currentMonthIdx = today.getMonth(); // 0 to 11

  const points = [];
  // 6 past months actuals
  const pastActuals = [50500, 53000, 56000, 51000, 54000, 48320];
  for (let i = 5; i >= 0; i--) {
    const d = new Date(today.getFullYear(), currentMonthIdx - i, 1);
    points.push({
      month: monthNames[d.getMonth()],
      actual: pastActuals[5 - i],
      forecast: null as number | null,
    });
  }

  // 3 forward projection months
  const forwardForecasts = [49500, 48200, 47800];
  for (let j = 1; j <= 3; j++) {
    const d = new Date(today.getFullYear(), currentMonthIdx + j, 1);
    points.push({
      month: monthNames[d.getMonth()],
      actual: null as number | null,
      forecast: forwardForecasts[j - 1],
    });
  }

  return points;
};

// Top UPI Merchants derived from mock transactions
export const topUpiMerchants = [
  { merchant: 'Swiggy', debits: 14, amount: 4850, category: 'Food & Dining' },
  { merchant: 'Uber India', debits: 11, amount: 3200, category: 'Transport' },
  { merchant: 'Blinkit', debits: 8, amount: 2640, category: 'Groceries' },
  { merchant: 'Zomato', debits: 6, amount: 2150, category: 'Food & Dining' },
  { merchant: 'Croma Retail Electronics', debits: 1, amount: 2400, category: 'Shopping' },
  { merchant: 'Tata Power Electricity', debits: 1, amount: 1850, category: 'Bills & Utilities' },
];

// Savings Goals
export interface SavingsGoal {
  id: string;
  name: string;
  saved: number;
  target: number;
  percentage: number;
  iconName: 'palm-tree' | 'laptop';
  gradientBg: string;
}

export const savingsGoalsList: SavingsGoal[] = [
  {
    id: 'goal-1',
    name: 'Goa Trip',
    saved: 30000,
    target: 75000,
    percentage: 40,
    iconName: 'palm-tree',
    gradientBg: 'from-amber-600/30 to-violet-600/30',
  },
  {
    id: 'goal-2',
    name: 'New Laptop',
    saved: 27000,
    target: 90000,
    percentage: 30,
    iconName: 'laptop',
    gradientBg: 'from-blue-600/30 to-indigo-600/30',
  },
];

// Computed Overall Goal Progress across all goals for Screen A Quick Insights
const totalGoalsSaved = savingsGoalsList.reduce((acc, g) => acc + g.saved, 0); // 57,000
const totalGoalsTarget = savingsGoalsList.reduce((acc, g) => acc + g.target, 0); // 1,65,000
export const overallGoalProgress = Math.round((totalGoalsSaved / totalGoalsTarget) * 100); // 35%
