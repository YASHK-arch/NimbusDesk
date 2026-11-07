export interface CompanySnapshot {
  name: string;
  tagline: string;
  currency: string;
  mrr: number;
  arr: number;
  cash_balance: number;
  monthly_burn: number;
  runway_months: number;
  total_paying_customers: number;
  blended_churn_monthly_pct: number;
  cac_blended: number;
  ltv_blended: number;
  current_free_users: number;
  support: {
    headcount: number;
    team_cost_monthly: number;
    paid_ticket_rate_per_user_month: number;
    cost_per_ticket: number;
    total_monthly_tickets: number;
  };
  infra: {
    current_monthly_cost: number;
    paid_user_cost_per_month: number;
    free_user_marginal_cost_per_month: number;
    database_cluster_utilization_pct: number;
  };
  funnel: {
    monthly_unique_visitors: number;
    visitor_to_trial_signup_pct: number;
    trial_to_paid_conversion_pct: number;
  };
  plans: Array<{
    plan_name: string;
    price_per_month: number;
    active_customers: number;
    mrr: number;
    churn_monthly_pct: number;
  }>;
  is_synthetic: boolean;
}

export interface TaskNode {
  id: string;
  owner: string;
  status: 'pending' | 'running' | 'done' | 'failed' | 'retrying';
  depends_on: string[];
  attempts?: number;
}

export interface DagPlan {
  nodes: TaskNode[];
  edges: Array<{ source: string; target: string }>;
}

export interface WorkflowEvent {
  ts: string;
  type: string;
  agent?: string;
  payload: Record<string, any>;
}

export interface Assumption {
  name: string;
  low: number;
  base: number;
  high: number;
  unit: string;
  provenance: 'verified_data' | 'external_research' | 'simulated_estimate' | 'ai_assumption';
  source_ref?: string;
  confidence: number;
  proposed_by?: string;
  challenged_by_skeptic: boolean;
}

export interface Finding {
  agent: string;
  task_id: string;
  claim: string;
  recommendation: 'proceed' | 'proceed_with_limits' | 'reject' | 'needs_more_info';
  assumptions: Assumption[];
  evidence: Array<{ source_type: string; source_ref: string; snippet: string }>;
  confidence: number;
  limitations: string[];
  status: string;
}

export interface DecisionReport {
  decision_id: string;
  question: string;
  generated_at: string;
  recommendation: string;
  confidence: string;
  disclaimer: string;
  synthetic_badge: boolean;
  llm_mode?: string;
  degraded_agent_banner?: string;
  sections: {
    executive_summary: {
      recommendation: string;
      confidence: string;
      primary_strategy: string;
      headline_thesis: string;
      llm_mode?: string;
      degraded_agent_banner?: string;
    };
    company_position: Record<string, any>;
    scenario_table: Array<{
      strategy: string;
      mrr_month_12_expected: number;
      mrr_month_12_conservative: number;
      mrr_month_12_optimistic: number;
      runway_months_12_expected: number;
      gross_margin_12_expected: number;
      support_headcount_12: number;
      net_contribution_12: number;
      net_contribution_24: number;
    }>;
    outcome_ranges?: Array<{
      strategy: string;
      n_iterations: number;
      seed: number;
      p_best: number;
      p_feasible: number;
      mrr_month_12: { p10: number; p50: number; p90: number };
      mrr_month_12_p10: number;
      mrr_month_12_p50: number;
      mrr_month_12_p90: number;
      runway_months_12: { p10: number; p50: number; p90: number };
      runway_months_12_p10: number;
      runway_months_12_p50: number;
      runway_months_12_p90: number;
      net_contribution_12: { p10: number; p50: number; p90: number };
      net_contribution_12_p10: number;
      net_contribution_12_p50: number;
      net_contribution_12_p90: number;
    }>;
    conflicts: Array<{
      id: string;
      type: string;
      agents: string[];
      disputed_item: string;
      resolved: boolean;
      resolution: string;
      simulation_ids: string[];
    }>;
    discussion_messages?: Array<{
      sender: string;
      recipient: string;
      kind: string;
      content: string;
      assumptions?: any[];
      timestamp: string;
    }>;
    sensitivity_tornado: Array<{
      assumption_name: string;
      unit: string;
      provenance: string;
      low_param: number;
      base_param: number;
      high_param: number;
      low_outcome: number;
      base_outcome: number;
      high_outcome: number;
      swing: number;
    }>;
    flip_point: {
      exists?: boolean;
      primary_strategy: string;
      competing_strategy: string;
      parameter_name: string;
      threshold: number | null;
      threshold_display: string;
      statement: string;
      flip_value?: number | null;
      tested_range?: [number, number];
      outcome_at_low?: number;
      outcome_at_high?: number;
      outcome_at_flip?: number;
    };
    assumption_ledger: Assumption[];
    risks: Array<{ category: string; description: string; mitigation: string }>;
    verification_summary: Array<{ check_name: string; status: string; detail: string }>;
    execution_plan: {
      phase_1_rollout: string;
      phase_2_evaluation: string;
      phase_3_decision_gate: string;
      metrics_to_monitor: string[];
    };
    run_log: Array<{
      task_id: string;
      agent: string;
      duration_sec: number;
      start_iso: string;
      finish_iso: string;
    }>;
  };
}
