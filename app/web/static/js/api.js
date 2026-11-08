/**
 * SpendSmart API Client
 * Wraps all REST API calls and manages JWT headers.
 */
const SpendSmartApi = (() => {
  const TOKEN_KEY = "spendsmart_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  async function request(path, options = {}) {
    const headers = options.headers || {};
    const token = getToken();

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.body);
    }

    const response = await fetch(path, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      clearToken();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
      throw new Error("Session expired. Please log in again.");
    }

    if (!response.ok) {
      let errorMsg = `Error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMsg = errorData.detail.map(d => d.msg).join(", ");
          } else {
            errorMsg = errorData.detail;
          }
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  }

  return {
    getToken,
    setToken,
    clearToken,
    request,

    // Auth
    register: (email, password) => request("/auth/register", { method: "POST", body: { email, password } }),
    login: async (email, password) => {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });
      if (!res.ok) {
        let msg = "Invalid credentials";
        try {
          const data = await res.json();
          if (data.detail) msg = data.detail;
        } catch (_) {}
        throw new Error(msg);
      }
      return await res.json();
    },
    getMe: () => request("/auth/me"),

    // Expenses
    getExpenses: (month, category) => {
      const params = new URLSearchParams();
      if (month) params.append("month", month);
      if (category) params.append("category", category);
      const query = params.toString() ? `?${params.toString()}` : "";
      return request(`/expenses${query}`);
    },
    addExpenseFromText: (text) => request("/expenses", { method: "POST", body: { text } }),
    updateExpense: (id, updates) => request(`/expenses/${id}`, { method: "PATCH", body: updates }),
    deleteExpense: (id) => request(`/expenses/${id}`, { method: "DELETE" }),

    // Budgets
    getBudgets: () => request("/budgets"),
    getBudgetStatus: (month) => request(`/budgets/status${month ? `?month=${month}` : ""}`),
    setBudget: (category, monthly_limit) => request(`/budgets/${category}`, { method: "PUT", body: { monthly_limit } }),
    deleteBudget: (category) => request(`/budgets/${category}`, { method: "DELETE" }),

    // Alerts
    getAlerts: () => request("/alerts"),

    // Analytics
    getSummary: (month) => request(`/analytics/summary${month ? `?month=${month}` : ""}`),
    getByCategory: (month) => request(`/analytics/by-category${month ? `?month=${month}` : ""}`),
    getTrend: (months = 6) => request(`/analytics/trend?months=${months}`),
    getTopMerchants: (month, limit = 5) => request(`/analytics/top-merchants?month=${month}&limit=${limit}`),
  };
})();
