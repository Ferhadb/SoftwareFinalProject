/**
 * SpendSmart Dashboard Controller
 * Connects UI actions to SpendSmartApi and renders the overview.
 */
const Dashboard = (() => {
  let trendChart = null;
  let trendData = [];
  const expensesById = new Map();

  const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
  const fmt = (v) => money.format(Number(v || 0));

  function getCurrentMonth() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  }

  function monthName(ym, short = false) {
    const [y, m] = ym.split("-").map(Number);
    return new Date(y, m - 1, 1).toLocaleDateString("en-US", short ? { month: "short" } : { month: "long", year: "numeric" });
  }

  let selectedMonth = getCurrentMonth();

  async function init() {
    if (!SpendSmartApi.getToken()) return; // auth.js redirects

    const monthInput = document.getElementById("month-input");
    if (monthInput) monthInput.value = selectedMonth;
    document.addEventListener("themechange", drawTrend);
    await refreshAll();
  }

  async function refreshAll() {
    document.getElementById("page-title").innerText = monthName(selectedMonth);
    await Promise.allSettled([
      loadSummary(),
      loadCategoryAnalytics(),
      loadTrendAnalytics(),
      loadBudgets(),
      loadExpenses(),
      loadAlerts(),
    ]);
  }

  function onMonthChange(newMonth) {
    if (!newMonth) return;
    selectedMonth = newMonth;
    refreshAll();
  }

  // --- Summary ---
  async function loadSummary() {
    try {
      const s = await SpendSmartApi.getSummary(selectedMonth);
      const count = s.count || 0;
      document.getElementById("summary-total").innerText = fmt(s.total);
      document.getElementById("summary-count").innerText = `${count} ${count === 1 ? "expense" : "expenses"}`;
      document.getElementById("summary-average").innerText = fmt(s.average);
      document.getElementById("summary-top-category").innerText = s.top_category || "—";
    } catch (_) {}
  }

  // --- Quick add ---
  async function handleAddExpense(e) {
    e.preventDefault();
    const input = document.getElementById("expense-text-input");
    const errorEl = document.getElementById("quick-add-error");
    const btn = document.getElementById("btn-add-expense");
    const text = input.value.trim();
    if (!text) return;

    errorEl.classList.add("hidden");
    btn.disabled = true;
    try {
      await SpendSmartApi.addExpenseFromText(text);
      input.value = "";
      await refreshAll();
    } catch (err) {
      errorEl.innerText = err.message || "Could not add the expense";
      errorEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      input.focus();
    }
  }

  // --- Expenses: printed as receipt lines ---
  function shortDate(iso) {
    if (!iso) return "";
    return new Date(`${iso}T00:00`).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
  }

  async function loadExpenses() {
    const list = document.getElementById("expenses-list");
    const countEl = document.getElementById("expenses-count-badge");
    const totalEl = document.getElementById("receipt-total");
    document.getElementById("receipt-month").innerText = monthName(selectedMonth);
    try {
      const expenses = (await SpendSmartApi.getExpenses(selectedMonth)) || [];
      countEl.innerText = String(expenses.length);
      totalEl.innerText = expenses.reduce((sum, x) => sum + Number(x.amount || 0), 0).toFixed(2);
      expensesById.clear();
      expenses.forEach((x) => expensesById.set(x.id, x));

      if (expenses.length === 0) {
        list.innerHTML = `<li class="empty">Nothing printed for ${monthName(selectedMonth)} yet</li>`;
        return;
      }

      list.innerHTML = expenses
        .map(
          (x) => `
        <li class="item">
          <span class="item-date">${escapeHtml(shortDate(x.occurred_on))}</span>
          <span class="item-desc" title="${escapeHtml(x.description)}">${escapeHtml(x.description)}</span>
          <span class="item-amt num">${Number(x.amount || 0).toFixed(2)}</span>
          <span class="item-cat">${escapeHtml(x.category)}<span class="source">${escapeHtml(x.category_source || "")}</span></span>
          <span class="item-actions">
            <button class="btn btn-ghost btn-icon" type="button" onclick="Dashboard.openEditExpenseModal(${Number(x.id)})" aria-label="Change category" title="Change category">
              <svg class="icon"><use href="#i-pencil"/></svg>
            </button>
            <button class="btn btn-ghost btn-icon danger" type="button" onclick="Dashboard.handleDeleteExpense(${Number(x.id)})" aria-label="Delete" title="Delete">
              <svg class="icon"><use href="#i-trash"/></svg>
            </button>
          </span>
        </li>`
        )
        .join("");
    } catch (_) {
      list.innerHTML = `<li class="empty">Could not load expenses</li>`;
    }
  }

  async function handleDeleteExpense(id) {
    const x = expensesById.get(id);
    if (!confirm(`Delete "${x ? x.description : "this expense"}"?`)) return;
    try {
      await SpendSmartApi.deleteExpense(id);
      await refreshAll();
    } catch (err) {
      alert(err.message || "Could not delete the expense");
    }
  }

  // --- Edit modal ---
  function openEditExpenseModal(id) {
    const x = expensesById.get(id);
    if (!x) return;
    document.getElementById("edit-expense-id").value = id;
    document.getElementById("edit-expense-desc").innerText = x.description;
    document.getElementById("edit-expense-amount").innerText = fmt(x.amount);
    document.getElementById("edit-expense-category").value = x.category;
    document.getElementById("edit-expense-modal").classList.remove("hidden");
  }

  function closeEditExpenseModal() {
    document.getElementById("edit-expense-modal").classList.add("hidden");
  }

  async function handleSaveExpenseCategory(e) {
    e.preventDefault();
    const id = document.getElementById("edit-expense-id").value;
    const category = document.getElementById("edit-expense-category").value;
    try {
      await SpendSmartApi.updateExpense(id, { category });
      closeEditExpenseModal();
      await refreshAll();
    } catch (err) {
      alert(err.message || "Could not change the category");
    }
  }

  // --- Budgets ---
  async function loadBudgets() {
    const list = document.getElementById("budgets-list");
    try {
      const statuses = (await SpendSmartApi.getBudgetStatus(selectedMonth)) || [];
      if (statuses.length === 0) {
        list.innerHTML = `<p class="empty">No budgets yet. Set a monthly limit for a category to track it here</p>`;
        return;
      }
      const levelText = { ok: "On track", warning: "Past 80% of the limit", exceeded: "Over the limit" };
      list.innerHTML = statuses
        .map((b) => {
          const pct = Number(b.percent || 0);
          const level = b.level || "ok";
          return `
          <div class="budget">
            <div class="budget-top">
              <span>${escapeHtml(b.category)}</span>
              <span class="figures num">${fmt(b.spent)} / ${fmt(b.limit)}</span>
            </div>
            <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}" aria-label="${escapeHtml(b.category)} budget used">
              <div class="meter-fill ${level}" style="width: ${Math.min(pct, 100)}%"></div>
            </div>
            <span class="budget-level ${level}"><span class="num">${pct.toFixed(0)}%</span> · ${levelText[level] || level}</span>
          </div>`;
        })
        .join("");
    } catch (_) {
      list.innerHTML = `<p class="empty">Could not load budgets</p>`;
    }
  }

  function openBudgetModal() {
    document.getElementById("budget-modal").classList.remove("hidden");
    document.getElementById("budget-limit").focus();
  }

  function closeBudgetModal() {
    document.getElementById("budget-modal").classList.add("hidden");
  }

  async function handleSaveBudget(e) {
    e.preventDefault();
    const category = document.getElementById("budget-category").value;
    const limit = parseFloat(document.getElementById("budget-limit").value);
    try {
      await SpendSmartApi.setBudget(category, limit);
      closeBudgetModal();
      await refreshAll();
    } catch (err) {
      alert(err.message || "Could not save the budget");
    }
  }

  // --- Alerts ---
  async function loadAlerts() {
    const container = document.getElementById("alerts-container");
    const list = document.getElementById("alerts-list");
    try {
      const alerts = (await SpendSmartApi.getAlerts()) || [];
      if (alerts.length === 0) {
        container.classList.add("hidden");
        return;
      }
      container.classList.remove("hidden");
      list.innerHTML = alerts
        .slice(0, 5)
        .map((a) => {
          const level = Number(a.level) >= 100 ? "exceeded" : "warning";
          const text = level === "exceeded" ? "went over its budget" : "passed 80% of its budget";
          return `
          <div class="alert-row">
            <span class="dot ${level}"></span>
            <span>${escapeHtml(a.category)} ${text}</span>
            <span class="when num">${escapeHtml(a.month || "")}</span>
          </div>`;
        })
        .join("");
    } catch (_) {
      container.classList.add("hidden");
    }
  }

  // --- By category: ranked list with thin bars ---
  async function loadCategoryAnalytics() {
    const list = document.getElementById("category-list");
    const meta = document.getElementById("category-meta");
    try {
      const data = ((await SpendSmartApi.getByCategory(selectedMonth)) || [])
        .map((d) => ({ ...d, total: Number(d.total) }))
        .sort((a, b) => b.total - a.total);
      meta.innerText = data.length ? `${data.length} ${data.length === 1 ? "category" : "categories"}` : "";
      if (data.length === 0) {
        list.innerHTML = `<li class="empty">Nothing spent in ${monthName(selectedMonth)}</li>`;
        return;
      }
      const max = data[0].total || 1;
      list.innerHTML = data
        .map(
          (d) => `
        <li class="share-row">
          <span>${escapeHtml(d.category)}</span>
          <span class="amount num">${fmt(d.total)}</span>
          <span class="share-bar"><span style="width: ${(d.total / max) * 100}%"></span></span>
        </li>`
        )
        .join("");
    } catch (_) {
      list.innerHTML = `<li class="empty">Could not load categories</li>`;
    }
  }

  // --- Trend: one line, the selected month marked ---
  async function loadTrendAnalytics() {
    try {
      trendData = (await SpendSmartApi.getTrend(6)) || [];
      drawTrend();
    } catch (_) {}
  }

  function drawTrend() {
    const ctx = document.getElementById("trend-chart");
    if (!ctx || typeof Chart === "undefined") return;
    const css = getComputedStyle(document.documentElement);
    const v = (name) => css.getPropertyValue(name).trim();
    const accent = v("--accent");
    const muted = v("--muted");
    const line = v("--line");

    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: trendData.map((t) => monthName(t.month, true)),
        datasets: [
          {
            data: trendData.map((t) => Number(t.total)),
            borderColor: accent,
            borderWidth: 2,
            tension: 0.35,
            fill: false,
            pointRadius: trendData.map((t) => (t.month === selectedMonth ? 4 : 0)),
            pointHoverRadius: 4,
            pointBackgroundColor: accent,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        plugins: {
          legend: { display: false },
          tooltip: {
            displayColors: false,
            callbacks: { label: (c) => fmt(c.parsed.y) },
          },
        },
        scales: {
          x: { grid: { display: false }, border: { display: false }, ticks: { color: muted, font: { family: "IBM Plex Mono", size: 12 } } },
          y: {
            beginAtZero: true,
            grid: { color: line },
            border: { display: false },
            ticks: { color: muted, maxTicksLimit: 5, font: { family: "IBM Plex Mono", size: 12 }, callback: (val) => `$${val}` },
          },
        },
      },
    });
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeBudgetModal();
      closeEditExpenseModal();
    }
  });

  document.addEventListener("DOMContentLoaded", init);

  return {
    init,
    refreshAll,
    onMonthChange,
    handleAddExpense,
    handleDeleteExpense,
    openEditExpenseModal,
    closeEditExpenseModal,
    handleSaveExpenseCategory,
    openBudgetModal,
    closeBudgetModal,
    handleSaveBudget,
  };
})();
