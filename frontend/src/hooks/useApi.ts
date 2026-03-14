const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3006';

function getToken(): string | null {
  return localStorage.getItem('token');
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  // Auth
  register: (email: string, password: string) =>
    fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(handleResponse<any>),

  login: (email: string, password: string) =>
    fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(handleResponse<any>),

  // Scans
  createScan: (repo_url: string) =>
    fetch(`${API_BASE}/scans`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ repo_url }),
    }).then(handleResponse<any>),

  getScanStatus: (scanId: string) =>
    fetch(`${API_BASE}/scans/${scanId}/status`, {
      headers: authHeaders(),
    }).then(handleResponse<any>),

  getScanFindings: (scanId: string, filters?: { severity?: string; status?: string; confidence?: string }) => {
    const params = new URLSearchParams();
    if (filters?.severity) params.set('severity', filters.severity);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.confidence) params.set('confidence', filters.confidence);
    const qs = params.toString();
    return fetch(`${API_BASE}/scans/${scanId}/findings${qs ? `?${qs}` : ''}`, {
      headers: authHeaders(),
    }).then(handleResponse<any>);
  },

  // Findings
  triageFinding: (findingId: string, status: string) =>
    fetch(`${API_BASE}/findings/${findingId}/triage`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ status }),
    }).then(handleResponse<any>),

  // Repos
  getRepoHistory: (repoId: string) =>
    fetch(`${API_BASE}/repos/${repoId}/history`, {
      headers: authHeaders(),
    }).then(handleResponse<any>),

  getRepoDelta: (repoId: string) =>
    fetch(`${API_BASE}/repos/${repoId}/delta`, {
      headers: authHeaders(),
    }).then(handleResponse<any>),

  // Health
  getHealth: () =>
    fetch(`${API_BASE}/health`).then(handleResponse<any>),
};

export default api;
