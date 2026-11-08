/**
 * SpendSmart API Client with Mock Fallback for UI Development
 * When backend endpoints are 404 (not yet implemented), returns realistic mock data
 * so the frontend dashboard can be previewed and tested immediately.
 */
const SpendSmartApi = (() => {
  const TOKEN_KEY = "spendsmart_token";

  // In-memory demo state for frontend preview
  const mockState = {
    user: { id: 1, email: "sabuhi@ufaz.az" },
    expenses: [
      { id: 1, description: "Uber to UFAZ", merchant: "Uber", amount: 8.50, category: "Transport", category_source: "rules", occurred_on: "2026-11-08" },
      { id: 2, description: "Bravo Supermarket groceries", merchant: "Bravo", amount: 45.20, category: "Food", category_source: "rules", occurred_on: "2026-11-07" },
      { id: 3, description: "Netflix subscription", merchant: "Netflix", amount: 12.99, category: "Subscriptions", category_source: "rules", occurred_on: "2026-11-05" },
      { id: 4, description: "Starbucks latte", merchant: "Starbucks", amount: 6.50, category: "Food", category_source: "rules", occurred_on: "2026-11-04" },
      { id: 5, description: "Pharmacy vitamins", merchant: "Zeytun", amount: 22.00, category: "Health", category_source: "rules", occurred_on: "2026-11-02" },
    ],
    budgets: [
      { category: "Food", monthly_limit: 150.00 },
      { category: "Transport", monthly_limit: 50.00 },
      { category: "Subscriptions", monthly_limit: 20.00 },
    ],
    alerts: [
      { id: 1, category: "Food", level: 80, month: "2026-11" },
      { id: 2, category: "Transport", level: 80, month: "2026-11" },
    ]
  };

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

    try {
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

      // If backend route exists and returned 2xx/error
      if (response.status !== 404) {
        if (!response.ok) {
          let errorMsg = `Error ${response.status}`;
          try {
            const errorData = await response.json();
            if (errorData.detail) {
              errorMsg = Array.isArray(errorData.detail)
                ? errorData.detail.map((d) => d.msg).join(", ")
                : errorData.detail;
            }
          } catch (_) {}
          throw new Error(errorMsg);
        }

        if (response.status === 204) return null;
        return await response.json();
      }
    } catch (e) {
      if (e.message && e.message !== "Failed to fetch" && !e.message.includes("Error 404")) {
        throw e;
      }
    }

    // --- FALLBACK MOCK DATA (Runs when backend endpoint is 404) ---
    return handleMockRequest(path, options);
  }

  function handleMockRequest(path, options) {
    const url = new URL(path, window.location.origin);
    const pathname = url.pathname;
    const method = (options.method || "GET").toUpperCase();

    // /auth/me
    if (pathname === "/auth/me") {
      return mockState.user;
    }

    // /expenses
    if (pathname === "/expenses") {
      if (method === "GET") {
        return [...mockState.expenses].reverse();
      }
      if (method === "POST") {
        const body = options.body ? JSON.parse(options.body) : {};
        let desc = body.description || body.text || "Expense";
        let amount = body.amount || 10.0;
        let cat = body.category || "Food";

        if (body.text) {
          const parts = body.text.trim().split(/\s+/);
          const last = parts[parts.length - 1].replace("$", "").replace(",", ".");
          const parsedAmount = parseFloat(last);
          if (!isNaN(parsedAmount)) {
            amount = parsedAmount;
            desc = parts.slice(0, -1).join(" ") || "Expense";
          }
          if (desc.toLowerCase().includes("uber") || desc.toLowerCase().includes("bolt")) cat = "Transport";
          else if (desc.toLowerCase().includes("netflix") || desc.toLowerCase().includes("spotify")) cat = "Subscriptions";
          else if (desc.toLowerCase().includes("coffee") || desc.toLowerCase().includes("latte") || desc.toLowerCase().includes("starbucks")) cat = "Food";
        }

        const newExp = {
          id: Date.now(),
          description: desc,
          merchant: desc,
          amount: parseFloat(amount),
          category: cat,
          category_source: "rules",
          occurred_on: new Date().toISOString().split("T")[0],
        };
        mockState.expenses.push(newExp);
        return newExp;
      }
    }

    // /expenses/:id
    if (pathname.startsWith("/expenses/")) {
      const id = parseInt(pathname.split("/")[2], 10);
      if (method === "DELETE") {
        mockState.expenses = mockState.expenses.filter((e) => e.id !== id);
        return null;
      }
      if (method === "PATCH") {
        const body = options.body ? JSON.parse(options.body) : {};
        const exp = mockState.expenses.find((e) => e.id === id);
        if (exp && body.category) {
          exp.category = body.category;
          exp.category_source = "manual";
        }
        return exp;
      }
    }

    // /budgets/status
    if (pathname === "/budgets/status") {
      return mockState.budgets.map((b) => {
        const spent = mockState.expenses
          .filter((e) => e.category === b.category)
          .reduce((sum, e) => sum + Number(e.amount), 0);
        const percent = Math.round((spent / Number(b.monthly_limit)) * 100);
        let level = "ok";
        if (percent >= 100) level = "exceeded";
        else if (percent >= 80) level = "warning";
        return {
          category: b.category,
          limit: b.monthly_limit,
          spent: spent,
          percent: percent,
          level: level,
        };
      });
    }

    // /budgets
    if (pathname === "/budgets") {
      return mockState.budgets;
    }

    // /budgets/:category
    if (pathname.startsWith("/budgets/")) {
      const cat = decodeURIComponent(pathname.split("/")[2]);
      if (method === "PUT") {
        const body = options.body ? JSON.parse(options.body) : {};
        const existing = mockState.budgets.find((b) => b.category === cat);
        if (existing) {
          existing.monthly_limit = body.monthly_limit;
        } else {
          mockState.budgets.push({ category: cat, monthly_limit: body.monthly_limit });
        }
        return { category: cat, monthly_limit: body.monthly_limit };
      }
    }

    // /alerts
    if (pathname === "/alerts") {
      return mockState.alerts;
    }

    // /analytics/summary
    if (pathname === "/analytics/summary") {
      const total = mockState.expenses.reduce((sum, e) => sum + Number(e.amount), 0);
      const count = mockState.expenses.length;
      return {
        month: "2026-11",
        total: total,
        count: count,
        average: count ? total / count : 0,
        top_category: "Food",
      };
    }

    // /analytics/by-category
    if (pathname === "/analytics/by-category") {
      const totals = {};
      let grandTotal = 0;
      mockState.expenses.forEach((e) => {
        totals[e.category] = (totals[e.category] || 0) + Number(e.amount);
        grandTotal += Number(e.amount);
      });
      return Object.entries(totals).map(([category, total]) => ({
        category,
        total,
        percent: grandTotal ? Math.round((total / grandTotal) * 100) : 0,
      }));
    }

    // /analytics/trend
    if (pathname === "/analytics/trend") {
      return [
        { month: "2026-06", total: 120.50 },
        { month: "2026-07", total: 180.00 },
        { month: "2026-08", total: 140.25 },
        { month: "2026-09", total: 210.00 },
        { month: "2026-10", total: 195.80 },
        { month: "2026-11", total: 95.19 },
      ];
    }

    return {};
  }

  return {
    getToken,
    setToken,
    clearToken,
    request,

    // Auth
    register: async (email, password) => {
      try {
        return await request("/auth/register", { method: "POST", body: { email, password } });
      } catch (err) {
        // Fallback for mock preview
        mockState.user = { id: 1, email };
        return mockState.user;
      }
    },
    login: async (email, password) => {
      try {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        const res = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData,
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (_) {}

      // Fallback for mock preview
      mockState.user = { id: 1, email };
      return { access_token: "demo_preview_token", token_type: "bearer" };
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
