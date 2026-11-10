import { Account, Bill, Budget, CategorySpending, FinancialHealthMetrics, ForecastPoint, SavingsGoal, Transaction } from '../types';

const todayDate = new Date();
const currentMonthYear = todayDate.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });

export const mockHealthMetrics: FinancialHealthMetrics = {
  score: 76,
  rating: 'Excellent',
  summary: "You're spending within your means! Keep it up or set a savings goal.",
  availableBalance: 124500.50, // ₹1,24,500.50
  monthlySavings: 18650.00,    // +₹18,650.00
  pendingBills: 4200.00,       // ₹4,200.00
  period: currentMonthYear,
};

export const mockCategorySpending: CategorySpending[] = [
  { name: 'Food & Dining', amount: 14200, currency: '₹', percentage: 39, color: '#8B5CF6' },
  { name: 'Bills & Utilities', amount: 8500, currency: '₹', percentage: 24, color: '#F59E0B' },
  { name: 'Transportation', amount: 4800, currency: '₹', percentage: 13, color: '#06B6D4' },
  { name: 'Entertainment', amount: 4200, currency: '₹', percentage: 12, color: '#F43F5E' },
  { name: 'Shopping', amount: 3800, currency: '₹', percentage: 11, color: '#10B981' },
];

export const mockAccounts: Account[] = [
  {
    id: 'acc-1',
    name: 'Everyday account',
    bankName: 'HDFC Bank',
    accountNumberMask: '4821',
    accountType: 'checking',
    balance: 98250,
    currency: '₹',
    isConnected: true,
  },
  {
    id: 'acc-2',
    name: 'High-yield savings',
    bankName: 'SBI Bank',
    accountNumberMask: '9034',
    accountType: 'savings',
    balance: 26250.50,
    currency: '₹',
    isConnected: true,
  },
];

export const mockBudgets: Budget[] = [
  { id: 'bgt-1', category: 'Food & Dining', spent: 14200, limit: 18000, period: currentMonthYear },
  { id: 'bgt-2', category: 'Bills & Utilities', spent: 8500, limit: 12000, period: currentMonthYear },
  { id: 'bgt-3', category: 'Travel & transport', spent: 4800, limit: 8000, period: currentMonthYear },
  { id: 'bgt-4', category: 'Shopping', spent: 3800, limit: 7500, period: currentMonthYear },
];

export const mockBills: Bill[] = [
  { id: 'b-1', name: 'Netflix Premium 4K', category: 'Subscription', amount: 649, dueDate: 'Feb 10, 2025', daysLeft: 4, autoPay: true, status: 'due_soon' },
  { id: 'b-2', name: 'ACT Fibernet 300 Mbps', category: 'Broadband', amount: 1050, dueDate: 'Feb 14, 2025', daysLeft: 8, autoPay: true, status: 'scheduled' },
  { id: 'b-3', name: 'BESCOM Electricity Bill', category: 'Utilities', amount: 1450, dueDate: 'Feb 20, 2025', daysLeft: 14, autoPay: false, status: 'scheduled' },
  { id: 'b-4', name: 'Apartment Maintenance & Rent', category: 'Housing', amount: 18000, dueDate: 'Mar 01, 2025', daysLeft: 23, autoPay: false, status: 'scheduled' },
];

export const mockSavingsGoals: SavingsGoal[] = [
  {
    id: 'g-1',
    name: 'Vacation Fund',
    currentAmount: 36000,
    targetAmount: 60000,
    percentage: 60,
    color: '#06B6D4', // Cyan
  },
  {
    id: 'g-2',
    name: 'Emergency Fund',
    currentAmount: 85000,
    targetAmount: 100000,
    percentage: 85,
    color: '#EC4899', // Hot Pink
  },
];

export const mockRecentTransactions: Transaction[] = [
  {
    id: 'tx-1',
    date: 'Feb 3',
    merchant: 'Uber',
    category: 'Transport',
    amount: 350,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-2',
    date: 'Feb 2',
    merchant: 'Netflix',
    category: 'Subscription',
    amount: 649,
    type: 'expense',
    channel: 'Card',
  },
  {
    id: 'tx-3',
    date: 'Feb 2',
    merchant: 'Swiggy',
    category: 'Food & Dining',
    amount: 1480,
    type: 'expense',
    channel: 'UPI',
    isAnomaly: true,
    anomalyReason: '3.2x higher than typical weekend dinner orders',
  },
  {
    id: 'tx-4',
    date: 'Jan 31',
    merchant: 'TechCorp Salary',
    category: 'Income',
    amount: 85000,
    type: 'income',
    channel: 'Direct',
  },
  {
    id: 'tx-5',
    date: 'Jan 30',
    merchant: 'BESCOM Electricity',
    category: 'Bills & Utilities',
    amount: 1450,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-6',
    date: 'Jan 28',
    merchant: 'Blinkit',
    category: 'Groceries',
    amount: 680,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-7',
    date: 'Jan 26',
    merchant: 'Croma Electronics',
    category: 'Shopping',
    amount: 2400,
    type: 'expense',
    channel: 'Card',
    isAnomaly: true,
    anomalyReason: 'Unusual one-time electronics purchase',
  },
  {
    id: 'tx-8',
    date: 'Jan 24',
    merchant: 'Zomato',
    category: 'Food & Dining',
    amount: 840,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-9',
    date: 'Jan 22',
    merchant: 'ACT Fibernet',
    category: 'Bills & Utilities',
    amount: 1050,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-10',
    date: 'Jan 20',
    merchant: 'Zepto',
    category: 'Groceries',
    amount: 420,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-11',
    date: 'Jan 18',
    merchant: 'Shell Petrol Bunk',
    category: 'Transport',
    amount: 1200,
    type: 'expense',
    channel: 'UPI',
  },
  {
    id: 'tx-12',
    date: 'Jan 15',
    merchant: 'Freelance Tech Advisory',
    category: 'Income',
    amount: 35000,
    type: 'income',
    channel: 'Direct',
  },
];

export const mockForecastPoints: ForecastPoint[] = [
  { date: 'Nov 2024', predictedSpend: 31200, projectedBalance: 110000, upperConfidence: 33500, lowerConfidence: 29000 },
  { date: 'Dec 2024', predictedSpend: 34500, projectedBalance: 118000, upperConfidence: 37000, lowerConfidence: 32000 },
  { date: 'Jan 2025', predictedSpend: 30500, projectedBalance: 124500, upperConfidence: 32500, lowerConfidence: 28500 },
  { date: 'Feb 2025 (Projected)', predictedSpend: 35500, projectedBalance: 132000, upperConfidence: 38000, lowerConfidence: 33000 },
  { date: 'Mar 2025 (Projected)', predictedSpend: 33000, projectedBalance: 141000, upperConfidence: 36000, lowerConfidence: 30000 },
];

export const initialChatMessages = [
  {
    id: 'msg-1',
    sender: 'assistant' as const,
    text: "Based on your recent transactions, you've spent ₹8,450 on subscriptions in the past 3 months. Would you like to review and potentially cancel unused subscriptions to save money?",
    timestamp: 'Just now',
    quickActions: [
      { label: 'Review Subscriptions', action: 'review_subscriptions', primary: true },
      { label: 'May be later', action: 'dismiss', primary: false },
    ],
  },
  {
    id: 'msg-2',
    sender: 'user' as const,
    text: 'Show me my spending breakdown for this month.',
    timestamp: 'Just now',
  },
  {
    id: 'msg-3',
    sender: 'assistant' as const,
    text: "Here's your spending breakdown for this month:",
    timestamp: 'Just now',
    chartTitle: "Monthly Category Breakdown",
    chartData: mockCategorySpending,
  },
];
