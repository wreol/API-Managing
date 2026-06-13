export interface User {
  id: string;
  email: string;
  display_name: string;
  oauth_provider: string | null;
  email_verified: boolean;
}

export interface ApiKey {
  id: string;
  provider: string;
  label: string;
  masked_key: string;
  tags: string[];
  status: 'ok' | 'needs_update' | 'error';
  created_at: string;
}

export interface UsageSummary {
  total_calls: number;
  total_tokens: number;
  total_cost: number;
  by_provider: ProviderUsage[];
}

export interface ProviderUsage {
  provider: string;
  calls: number;
  tokens: number;
  cost: number;
  percentage: number;
}

export interface UsageTrendPoint {
  date: string;
  calls: number;
  tokens: number;
  cost: number;
}

export interface AlertRule {
  id: string;
  key_id: string | null;
  provider: string | null;
  type: 'budget' | 'call_count';
  threshold: number;
  notify_email: string;
  is_active: boolean;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  triggered_at: string;
  threshold_pct: number;
  message: string;
  is_read: boolean;
}

export interface KeyShare {
  id: string;
  key_id: string;
  shared_by: string;
  shared_with: string;
  permission: 'read' | 'use';
  created_at: string;
}

export interface ProviderInfo {
  name: string;
  label: string;
  is_custom: boolean;
  auth_type: string;
}
