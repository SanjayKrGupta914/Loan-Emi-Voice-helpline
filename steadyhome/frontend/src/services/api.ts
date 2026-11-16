const API_BASE = '/api';

export interface AuthUser {
  role: 'admin' | 'borrower';
  name: string;
  borrower_id?: string;
}

const TOKEN_KEY = 'steadyhome_token';
const USER_KEY = 'steadyhome_user';

export function getStoredAuth(): { token: string; user: AuthUser } | null {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const user = localStorage.getItem(USER_KEY);
    return token && user ? { token, user: JSON.parse(user) } : null;
  } catch (_) {
    return null;
  }
}

export function storeAuth(token: string, user: AuthUser) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/** fetch() that attaches the sign-in token and signs the user out when the server rejects it. */
async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const auth = getStoredAuth();
  const headers = new Headers(init.headers);
  if (auth) headers.set('Authorization', `Bearer ${auth.token}`);
  const res = await fetch(input, { ...init, headers });
  if (res.status === 401 && auth) {
    clearAuth();
    window.dispatchEvent(new Event('steadyhome-auth-expired'));
  }
  return res;
}

async function loginRequest(path: string, body: object) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Sign-in failed. Please try again.');
  return data as { token: string; user: AuthUser };
}

export const adminLogin = (username: string, password: string) =>
  loginRequest('/auth/admin-login', { username, password });

export const borrowerLogin = (borrowerId: string, dob: string, loanLastFour: string) =>
  loginRequest('/auth/borrower-login', {
    borrower_id: borrowerId,
    date_of_birth: dob,
    loan_last_four: loanLastFour,
  });

export async function fetchPortal() {
  const res = await authFetch(`${API_BASE}/portal/me`);
  if (!res.ok) throw new Error('Failed to load your loan details');
  return res.json();
}

export async function fetchDashboard() {
  const res = await authFetch(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error('Failed to fetch dashboard data');
  return res.json();
}

export async function fetchBorrowers(search?: string, status?: string) {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (status) params.append('status', status);
  const res = await authFetch(`${API_BASE}/borrowers?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch borrowers');
  return res.json();
}

export async function fetchBorrowerProfile(borrowerId: string) {
  const res = await authFetch(`${API_BASE}/borrowers/${borrowerId}`);
  if (!res.ok) throw new Error('Failed to fetch borrower profile');
  return res.json();
}

export async function fetchEMIs(status?: string, paymentMode?: string) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (paymentMode) params.append('payment_mode', paymentMode);
  const res = await authFetch(`${API_BASE}/emis?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch EMIs');
  return res.json();
}

export async function sendAgentMessage(sessionId: string, message: string, simulatedNow?: string) {
  const res = await authFetch(`${API_BASE}/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      simulated_now: simulatedNow
    }),
  });
  if (!res.ok) throw new Error('Agent communication failure');
  return res.json();
}

export async function resetAgentSession(sessionId: string) {
  const res = await authFetch(`${API_BASE}/agent/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error('Failed to reset session');
  return res.json();
}

export async function verifyBorrowerDirect(borrowerId: string, dob: string, loanLastFour: string) {
  const res = await authFetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      borrower_id: borrowerId,
      date_of_birth: dob,
      loan_last_four: loanLastFour
    }),
  });
  if (!res.ok) throw new Error('Verification request failed');
  return res.json();
}

export async function calculateLateFeeDirect(emiAmount: number, dueDate: string, status?: string) {
  const res = await authFetch(`${API_BASE}/late-fee/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      emi_amount: emiAmount,
      due_date: dueDate,
      payment_status: status || 'PENDING'
    }),
  });
  if (!res.ok) throw new Error('Late fee calculation failed');
  return res.json();
}

export async function fetchEscalations() {
  const res = await authFetch(`${API_BASE}/escalations`);
  if (!res.ok) throw new Error('Failed to fetch escalations');
  return res.json();
}

export async function fetchArchitecture() {
  const res = await authFetch(`${API_BASE}/architecture`);
  if (!res.ok) throw new Error('Failed to fetch architecture metadata');
  return res.json();
}

export async function fetchEvaluationTests() {
  const res = await authFetch(`${API_BASE}/evaluate/tests`);
  if (!res.ok) throw new Error('Failed to fetch test catalog');
  return res.json();
}

export async function runEvaluationSuite(testId?: string) {
  const url = testId ? `${API_BASE}/evaluate/run?test_id=${encodeURIComponent(testId)}` : `${API_BASE}/evaluate/run`;
  const res = await authFetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Evaluation execution failed');
  return res.json();
}

export async function fetchAdvisory(city?: string, useMock?: boolean) {
  const params = new URLSearchParams();
  if (city) params.append('city', city);
  if (useMock) params.append('use_mock', 'true');
  const res = await authFetch(`${API_BASE}/advisory?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch payment advisory');
  return res.json();
}

export async function fetchSystemSettings() {
  const res = await authFetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error('Failed to fetch settings');
  return res.json();
}

export async function updateSimulatedClock(isoString: string) {
  const res = await authFetch(`${API_BASE}/settings/clock`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ simulated_now: isoString }),
  });
  if (!res.ok) throw new Error('Failed to update simulated clock');
  return res.json();
}

export async function resetSimulatedClock() {
  const res = await authFetch(`${API_BASE}/settings/clock/reset`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reset clock');
  return res.json();
}


export async function fetchIntegrationsStatus() {
  const res = await authFetch(`${API_BASE}/integrations/status`);
  if (!res.ok) throw new Error('Failed to fetch integration status');
  return res.json();
}
