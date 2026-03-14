export interface User {
  id: string;
  email: string;
  role: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface Repository {
  id: string;
  url: string;
  name: string;
}

export interface Scan {
  id: string;
  repo_id: string;
  status: 'queued' | 'running' | 'complete' | 'failed';
  files_scanned: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface Finding {
  id: string;
  scan_id: string;
  fingerprint: string;
  vulnerability_type: string;
  cwe_id?: string | null;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'informational';
  confidence: 'high' | 'medium' | 'low';
  file_path: string;
  line_number: number;
  code_snippet: string;
  description: string;
  attack_scenario: string;
  remediation: string;
  status: 'open' | 'false_positive' | 'resolved';
  created_at: string;
}

export interface FindingsListResponse {
  findings: Finding[];
  total: number;
}

export interface DeltaResponse {
  new: Finding[];
  fixed: Finding[];
  persisting: Finding[];
}

export interface RepoHistory {
  repo: Repository;
  scans: Scan[];
}

export interface ScanStatus {
  id: string;
  status: string;
  files_scanned: number;
  started_at?: string | null;
  completed_at?: string | null;
}
