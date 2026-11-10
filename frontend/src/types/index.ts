export type VoiceState = 'idle' | 'listening' | 'thinking' | 'tool_execution' | 'speaking' | 'interrupted' | 'error' | 'processing';

export interface CategorySpending {
  name: string;
  amount: number;
  currency: string;
  percentage: number;
  color: string;
}

export interface Transaction {
  id: string;
  date: string;
  dateStr?: string;
  merchant: string;
  category: string;
  amount: number;
  type: 'expense' | 'income';
  channel?: 'UPI' | 'Card' | 'NetBanking' | 'Direct';
  isAnomaly?: boolean;
  anomalyReason?: string;
}

export interface SavingsGoal {
  id: string;
  name: string;
  currentAmount: number;
  targetAmount: number;
  percentage: number;
  color: string;
}

export interface ChatMessage {
  id: string;
  sender: 'assistant' | 'user';
  text: string;
  timestamp: string;
  actionChips?: string[];
  chartData?: CategorySpending[];
  chartTitle?: string;
  quickActions?: {
    label: string;
    action: string;
    primary?: boolean;
  }[];
  evidence?: EvidenceItem[];
  metadata?: any;
  actionProposal?: ActionProposal;
  simulationData?: SimulationData;
  portalEvidence?: PortalEvidenceData;
  executionStages?: ExecutionStage[];
}

export interface PortalEvidenceData {
  portal?: string;
  order_id?: string;
  consumer_id?: string;
  consumer_name?: string;
  restaurant?: string;
  product_name?: string;
  total_amount?: number;
  food_subtotal?: number;
  surge_fee?: number;
  packaging_fee?: number;
  hidden_delivery_fees?: number;
  due_date?: string;
  units_consumed_kwh?: number;
  payment_status?: string;
  items?: string[];
  url?: string;
  verified?: boolean;
  screenshot_base64?: string | null;
  provenance?: string;
}

export interface ExecutionStage {
  trace_id?: string;
  stage: string;
  label: string;
  status: 'in_progress' | 'completed' | 'failed';
  timestamp_ms: number;
  tool?: string;
  record_count?: number;
  evidence_count?: number;
}

export interface VoiceOperationsTrace {
  trace_id: string;
  session_id?: string;
  recorded_at: string;
  language?: string;
  latencies: {
    stt_ms?: number | null;
    intent_ms?: number;
    tool_ms?: number;
    generation_ttft_ms?: number;
    tts_first_audio_ms?: number;
    tts_ms?: number;
    total_turn_ms?: number;
  };
  provider_status: Record<string, string>;
  playback_started: boolean;
  end_to_first_audible_ms?: number | null;
  interruption_success?: boolean;
  barge_in_latency_ms?: number | null;
}

export interface EvidenceItem {
  transaction_id: string;
  account_reference: string;
  date: string;
  merchant: string;
  amount_minor: number;
  amount_formatted: string;
  currency: string;
  category: string;
  payment_mode?: string;
  source_import_id?: string;
  is_anomaly?: boolean;
  anomaly_reason?: string;
}

export interface ActionProposal {
  action_id: string;
  action_type: string;
  description: string;
  parameters: Record<string, any>;
  expires_at: string;
  ttl_seconds: number;
  status?: 'pending' | 'executed' | 'cancelled';
}

export interface SimulationData {
  simulation_type: string;
  category: string;
  reduction_percentage: number;
  historical_monthly_spend: number;
  simulated_monthly_spend: number;
  monthly_savings: number;
  annualized_savings: number;
  goal_impact?: {
    goal_id?: string;
    goal_name?: string;
    target_amount?: number;
    current_amount?: number;
    remaining_amount?: number;
    baseline_months_to_complete?: number;
    accelerated_months_to_complete?: number;
    months_saved?: number;
  };
  slider_bounds?: { min: number; max: number; step: number };
}

export interface ProactiveAlert {
  type: string;
  alert_id: string;
  alert_type?: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  detail: string;
  category?: string;
  created_at: string;
}

export interface FinancialHealthMetrics {
  score: number; // 0 - 100
  rating: 'Poor' | 'Fair' | 'Good' | 'Excellent';
  summary: string;
  availableBalance: number;
  monthlySavings: number;
  pendingBills: number;
  period: string;
}

export interface Account {
  id: string;
  name: string;
  bankName: string;
  accountNumberMask: string;
  accountType: 'savings' | 'checking' | 'credit';
  balance: number;
  currency: string;
  isConnected: boolean;
}

export interface Budget {
  id: string;
  category: string;
  spent: number;
  limit: number;
  period: string;
}

export interface Bill {
  id: string;
  name: string;
  category: string;
  amount: number;
  dueDate: string;
  daysLeft: number;
  autoPay: boolean;
  status: 'due_soon' | 'scheduled' | 'paid';
}

export interface ForecastPoint {
  date?: string;
  month?: string;
  predictedSpend?: number;
  projectedBalance?: number;
  upperConfidence?: number;
  lowerConfidence?: number;
  actualAmount?: number | null;
  predictedAmount?: number;
  lowerBound?: number;
  upperBound?: number;
}
