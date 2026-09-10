const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? "/api" : "http://127.0.0.1:8000/api");

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("finagent_token");
}

export function setAuthToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("finagent_token", token);
  }
}

export function clearAuthToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("finagent_token");
  }
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (data: any) => apiFetch<{ access_token: string; user: any }>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  register: (data: any) => apiFetch<{ access_token: string; user: any }>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  getMe: () => apiFetch<any>("/auth/me"),
  updatePreferences: (data: any) => apiFetch<any>("/auth/preferences", { method: "PUT", body: JSON.stringify(data) }),

  // Expenses
  getExpenses: (params?: Record<string, any>) => {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
      });
    }
    const qStr = query.toString();
    return apiFetch<any[]>(`/expenses${qStr ? `?${qStr}` : ""}`);
  },
  createExpense: (data: any) => apiFetch<any>("/expenses", { method: "POST", body: JSON.stringify(data) }),
  deleteExpense: (id: string) => apiFetch<any>(`/expenses/${id}`, { method: "DELETE" }),
  importCSV: (formData: FormData) => apiFetch<any>("/expenses/import", { method: "POST", body: formData }),

  // Budgets
  getBudgets: () => apiFetch<any[]>("/budgets"),
  createBudget: (data: any) => apiFetch<any>("/budgets", { method: "POST", body: JSON.stringify(data) }),
  updateBudget: (id: string, data: any) => apiFetch<any>(`/budgets/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteBudget: (id: string) => apiFetch<any>(`/budgets/${id}`, { method: "DELETE" }),

  // Analytics
  getSummary: () => apiFetch<any>("/analytics/summary"),
  getMonthlyAnalytics: (monthsBack = 6) => apiFetch<any[]>(`/analytics/monthly?months_back=${monthsBack}`),
  getCategoryAnalytics: () => apiFetch<any[]>("/analytics/categories"),
  getSpendingTrends: (daysBack = 30) => apiFetch<any[]>(`/analytics/trends?days_back=${daysBack}`),

  // Agent
  chat: (message: string, context?: any) => apiFetch<any>("/agent/chat", { method: "POST", body: JSON.stringify({ message, context }) }),
  analyze: (text: string) => apiFetch<any>("/agent/analyze", { method: "POST", body: JSON.stringify({ text }) }),
  getAgentEvents: (limit = 50) => apiFetch<any[]>(`/agent/events?limit=${limit}`),
  triggerProactiveScan: () => apiFetch<any>("/agent/proactive/trigger", { method: "POST" }),

  // Alerts
  getAlerts: (resolved?: boolean) => {
    const q = resolved !== undefined ? `?resolved=${resolved}` : "";
    return apiFetch<any[]>(`/alerts${q}`);
  },
  resolveAlert: (id: string) => apiFetch<any>(`/alerts/${id}/resolve`, { method: "POST" }),

  // Reports
  generateMonthlyReport: (month?: number, year?: number) => {
    const q = month && year ? `?month=${month}&year=${year}` : "";
    return apiFetch<any>(`/reports/monthly${q}`, { method: "POST" });
  },
  getMonthlyReports: () => apiFetch<any[]>("/reports/monthly"),
};
