export interface User {
  id: string;
  email: string;
  display_name: string;
  oauth_provider: string | null;
  email_verified: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ApiKey {
  id: string;
  provider: string;
  label: string;
  masked_key: string;
  tags: string[];
  status: string;
  is_active: boolean;
}

export interface KeyDetail {
  id: string;
  provider: string;
  label: string;
  masked_key: string;
  tags: string[] | null;
  is_active: boolean;
  status: string;
}

export interface KeyCopyResponse {
  key_value: string;
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
}

export interface UsageTrendPoint {
  period: string;
  calls: number;
  tokens: number;
  cost: number;
}

export interface KeyBreakdown {
  key_id: string;
  key_label: string;
  provider: string;
  calls: number;
  tokens: number;
  cost: number;
}

export interface AlertRule {
  id: string;
  type: string;
  threshold: number;
  provider: string | null;
  key_id: string | null;
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
  email_sent: boolean;
}

export interface KeyShare {
  id: string;
  key_id: string;
  shared_by_email: string;
  shared_with_email: string;
  permission: string;
}

export interface ProviderInfo {
  name: string;
  label: string;
  is_custom: boolean;
}
