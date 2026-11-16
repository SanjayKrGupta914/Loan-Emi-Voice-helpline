export interface DashboardStats {
  total_borrowers: number;
  active_loans: number;
  pending_emis: number;
  successful_payments: number;
  total_collections: number;
  human_escalations: number;
  simulated_clock: string;
}

export interface CollectionTrend {
  month: string;
  collected: number;
  pending: number;
}

export interface PaymentModeDist {
  name: string;
  count: number;
}

export interface LoanStatusDist {
  status: string;
  count: number;
}

export interface RecentInteraction {
  id: number;
  session_id: string;
  borrower_id: string;
  event_type: string;
  agent_name: string;
  timestamp: string;
  details: string;
}

export interface EscalationItem {
  escalation_id: string;
  borrower_id: string | null;
  intent: string;
  reason: string;
  payment_mode: string | null;
  status: string;
  timestamp: string;
  conversation_summary?: string;
}

export interface BorrowerItem {
  borrower_id: string;
  name: string;
  date_of_birth: string;
  phone: string;
  email: string;
  borrower_status: string;
  address?: string;
  loan_id: string | null;
  loan_amount: number;
  loan_status: string;
  emi_amount: number;
  next_due_date: string;
}

export interface EMIItem {
  emi_id: string;
  loan_id: string;
  borrower_id: string;
  emi_amount: number;
  due_date: string;
  payment_status: string;
  payment_mode: string;
  days_overdue: number;
  late_fee: number;
  can_process_online: boolean;
  paid_date?: string | null;
}

export interface ChatMessageItem {
  role: 'system' | 'agent' | 'customer' | 'tool';
  content: string;
  spoken_text?: string;
  agent_name: string;
  timestamp: string;
  metadata?: any;
}

export interface ToolLogItem {
  tool_name: string;
  arguments: Record<string, any>;
  result: Record<string, any>;
  agent_name: string;
  timestamp: string;
}

export interface ConversationStateItem {
  session_id: string;
  borrower_id?: string | null;
  borrower_name?: string | null;
  verified: boolean;
  payment_mode?: string | null;
  intent_tag?: string | null;
  now_override: string;
  days_overdue: number;
  transfer_reason?: string | null;
  loan_status?: string | null;
  verification_attempts: number;
  clarification_attempts: number;
  active_agent: string;
  loan_id?: string | null;
  emi_amount?: number | null;
  due_date?: string | null;
  late_fee: number;
  is_escalated: boolean;
  escalation_id?: string | null;
  awaiting_confirmation: boolean;
  disclaimer_played: boolean;
  messages: ChatMessageItem[];
  tool_logs: ToolLogItem[];
}

export interface TestCaseItem {
  id: string;
  category: string;
  name: string;
  user_story: string;
  input_scenario: string;
  expected_outcome: string;
  test_type: string;
  params: Record<string, any>;
  actual_outcome?: any;
  tool_calls?: any[];
  status?: 'PASSED' | 'FAILED';
  passed?: boolean;
  executed_at?: string;
}

