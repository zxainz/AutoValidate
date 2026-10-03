export interface ValidationResult {
  id?: number;
  job_id?: number;
  finding_id?: number;
  verdict: 'TRUE_POSITIVE' | 'FALSE_POSITIVE' | 'NEEDS_MANUAL_REVIEW';
  confidence_score: number;
  reasoning: string;
  feasibility_score: number;
  context_score: number;
  evidence_score: number;
  exploitation_difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  business_impact: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommended_action?: string;
  false_positive_reason?: string;
  created_at?: string;
}

export interface Finding {
  id: number;
  scan_source: 'nessus' | 'qualys' | 'burp' | 'generic';
  scanner_id?: string;
  title: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | 'Info';
  cve_list: string[];
  cvss_score?: number;
  target_host?: string;
  target_port?: number;
  target_url?: string;
  protocol?: string;
  vuln_type?: string;
  description?: string;
  solution?: string;
  raw_evidence?: string;
  raw_payload?: string;
  status: 'UNVERIFIED' | 'TRUE_POSITIVE' | 'FALSE_POSITIVE' | 'NEEDS_MANUAL_REVIEW';
  confidence_score?: number;
  created_at: string;
  latest_result?: ValidationResult;
}

export interface DashboardMetrics {
  total_findings: number;
  validated_findings: number;
  unverified_findings: number;
  true_positives: number;
  false_positives: number;
  needs_review: number;
  time_saved_hours: number;
  false_positive_rate: number;
  true_positive_rate: number;
  severity_counts: {
    Critical: number;
    High: number;
    Medium: number;
    Low: number;
  };
}

export interface ReportSummary {
  id: number;
  title: string;
  total_findings: number;
  true_positives: number;
  false_positives: number;
  needs_review: number;
  time_saved_hours: number;
  created_at: string;
  formats_available: string[];
}

export interface AIStatus {
  connected: boolean;
  status: string;
  message: string;
  model?: string;
}

export interface SettingsConfig {
  model_name: string;
  base_url: string;
  reasoning_effort: string;
  temperature: number;
  api_key_configured: boolean;
  masked_api_key: string;
  database_url: string;
}
