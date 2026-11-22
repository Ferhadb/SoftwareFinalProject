/**
 * SpendSmart Dashboard Controller
 * Connects UI actions to SpendSmartApi and updates charts & lists.
 */
const Dashboard = (() => {
  let categoryChartInstance = null;
  let trendChartInstance = null;

  function getCurrentMonth() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    return `${year}-${month}`;
  }

  let selectedMonth = getCurrentMonth();

  async function init() {
    if (!SpendSmartApi.getToken()) {
      return; // Handled by auth.js redirect
    }

    const monthInput = document.getElementById("month-input");
    if (monthInput) {
      monthInput.value = selectedMonth;
    }

    await refreshAll();
  }

  async function refreshAll() {
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
      const summary = await SpendSmartApi.getSummary(selectedMonth);
      document.getElementById("summary-total").innerText = `$${Number(summary.total || 0).toFixed(2)}`;
      document.getElementById("summary-count").innerText = `${summary.count || 0} transactions`;
      document.getElementById("summary-average").innerText = `$${Number(summary.average || 0).toFixed(2)}`;
      document.getElementById("summary-top-category").innerText = summary.top_category || "—";
    } catch (_) {
      // Graceful fallback for unseeded or early environments
    }
  }

  // --- Quick Add Expense ---
  async function handleAddExpense(e) {
    e.preventDefault();
    const input = document.getElementById("expense-text-input");
    const errorEl = document.getElementById("quick-add-error");
    const btn = document.getElementById("btn-add-expense");

    const text = input.value.trim();
    if (!text) return;

    errorEl.classList.add("hidden");
    btn.disabled = true;
    btn.innerText = "Adding...";

    try {
      await SpendSmartApi.addExpenseFromText(text);
      input.value = "";
      await refreshAll();
    } catch (err) {
      errorEl.innerText = err.message || "Failed to add expense";
      errorEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.innerText = "Add Expense";
    }
  }

  // --- Expenses List ---
  async function loadExpenses() {
    const tbody = document.getElementById("expenses-tbody");
    const countBadge = document.getElementById("expenses-count-badge");
    try {
      const expenses = await SpendSmartApi.getExpenses(selectedMonth);
      countBadge.innerText = `${expenses.length} items`;

      if (!expenses || expenses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No expenses found for ${selectedMonth}</td></tr>`;
        return;
      }

      tbody.innerHTML = expenses
        .map(
          (item) => `
        <tr>
          <td>${item.occurred_on || "—"}</td>
          <td>
            <strong>${escapeHtml(item.description)}</strong>
            ${item.merchant && item.merchant !== item.description ? `<br><small class="text-muted">${escapeHtml(item.merchant)}</small>` : ""}
          </td>
          <td>
            <span class="badge">${item.category}</span>
            <span class="badge badge-source">${item.category_source || "auto"}</span>
          </td>
          <td><strong>$${Number(item.amount).toFixed(2)}</strong></td>
          <td>
            <button class="btn btn-sm btn-outline" onclick="Dashboard.openEditExpenseModal(${item.id}, '${escapeHtml(item.description)}', ${item.amount}, '${item.category}')">Edit</button>
            <button class="btn btn-sm btn-danger-outline" onclick="Dashboard.handleDeleteExpense(${item.id})">Delete</button>
          </td>
        </tr>
      `
        )
        .join("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Could not load expenses.</td></tr>`;
    }
  }

  async function handleDeleteExpense(id) {
    if (!confirm("Are you sure you want to delete this expense?")) return;
    try {
      await SpendSmartApi.deleteExpense(id);
      await refreshAll();
    } catch (err) {
      alert(err.message || "Failed to delete expense");
    }
  }

  // --- Edit Expense Modal ---
  function openEditExpenseModal(id, desc, amount, category) {
    document.getElementById("edit-expense-id").value = id;
    document.getElementById("edit-expense-desc").innerText = desc;
    document.getElementById("edit-expense-amount").innerText = `$${Number(amount).toFixed(2)}`;
    document.getElementById("edit-expense-category").value = category;
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
      alert(err.message || "Failed to update category");
    }
  }

  // --- Budgets ---
  async function loadBudgets() {
    const list = document.getElementById("budgets-list");
    try {
      const statuses = await SpendSmartApi.getBudgetStatus(selectedMonth);
      if (!statuses || statuses.length === 0) {
        list.innerHTML = `<p class="empty-state">No budgets set. Click "+ Set Budget" to create one.</p>`;
        return;
      }

      list.innerHTML = statuses
        .map((b) => {
          const percent = Math.min(b.percent || 0, 100);
          let progressClass = "progress-ok";
          if (b.level === "warning") progressClass = "progress-warning";
          if (b.level === "exceeded") progressClass = "progress-exceeded";

          return `
          <div class="budget-item">
            <div class="budget-item-header">
              <span><strong>${b.category}</strong> (${b.percent || 0}%)</span>
              <span>$${Number(b.spent || 0).toFixed(2)} / $${Number(b.limit).toFixed(2)}</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill ${progressClass}" style="width: ${percent}%;"></div>
            </div>
          </div>
        `;
        })
        .join("");
    } catch (_) {
      list.innerHTML = `<p class="empty-state">Could not load budgets.</p>`;
    }
  }

  function openBudgetModal() {
    document.getElementById("budget-modal").classList.remove("hidden");
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
      alert(err.message || "Failed to save budget");
    }
  }

  // --- Alerts ---
  async function loadAlerts() {
    const container = document.getElementById("alerts-container");
    const list = document.getElementById("alerts-list");

    try {
      const alerts = await SpendSmartApi.getAlerts();
      if (!alerts || alerts.length === 0) {
        container.classList.add("hidden");
        return;
      }

      // Filter to current month alerts or show recent
      container.classList.remove("hidden");
      list.innerHTML = alerts
        .slice(0, 5)
        .map(
          (a) => `
        <div class="alert-badge-item">
          <span>⚠️ <strong>${a.category}</strong> budget threshold crossed: <strong>${a.level}%</strong> reached</span>
          <span class="badge">${a.month}</span>
        </div>
      `
        )
        .join("");
    } catch (_) {
      container.classList.add("hidden");
    }
  }

  // --- Charts (Chart.js) ---
  async function loadCategoryAnalytics() {
    try {
      const data = await SpendSmartApi.getByCategory(selectedMonth);
      const ctx = document.getElementById("category-chart");
      if (!ctx) return;

      const labels = data.map((d) => d.category);
      const values = data.map((d) => Number(d.total));

      if (categoryChartInstance) {
        categoryChartInstance.destroy();
      }

      categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: labels.length ? labels : ["No Expenses"],
          datasets: [
            {
              data: values.length ? values : [1],
              backgroundColor: [
                "#3b82f6",
                "#10b981",
                "#f59e0b",
                "#ef4444",
                "#8b5cf6",
                "#ec4899",
                "#06b6d4",
                "#94a3b8",
              ],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "right" },
          },
        },
      });
    } catch (_) {}
  }

  async function loadTrendAnalytics() {
    try {
      const trend = await SpendSmartApi.getTrend(6);
      const ctx = document.getElementById("trend-chart");
      if (!ctx) return;

      const labels = trend.map((t) => t.month);
      const values = trend.map((t) => Number(t.total));

      if (trendChartInstance) {
        trendChartInstance.destroy();
      }

      trendChartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Monthly Total ($)",
              data: values,
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.1)",
              fill: true,
              tension: 0.3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true },
          },
        },
      });
    } catch (_) {}
  }

  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.innerText = str;
    return div.innerHTML;
  }

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
