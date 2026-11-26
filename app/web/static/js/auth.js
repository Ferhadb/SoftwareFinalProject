/**
 * SpendSmart Auth Manager
 * Manages user session, header display, and auth lifecycle.
 */
const SpendSmartAuth = (() => {
  async function init() {
    const navArea = document.getElementById("nav-user-area");
    if (!navArea) return;

    const token = SpendSmartApi.getToken();
    if (!token) {
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
      return;
    }

    try {
      const user = await SpendSmartApi.getMe();
      navArea.innerHTML = userArea(user.email || "user@spendsmart.local");
    } catch (e) {
      // If error occurs, keep token in dev mode
      navArea.innerHTML = userArea("demo@spendsmart.local");
    }
  }

  function userArea(email) {
    return `
      <span class="user-email">${escapeHtml(email)}</span>
      <button class="btn btn-ghost btn-icon" type="button" onclick="SpendSmartAuth.logout()" aria-label="Sign out" title="Sign out">
        <svg class="icon"><use href="#i-logout"/></svg>
      </button>`;
  }

  async function login(email, password) {
    const data = await SpendSmartApi.login(email, password);
    SpendSmartApi.setToken(data.access_token);
    return data;
  }

  async function register(email, password) {
    return await SpendSmartApi.register(email, password);
  }

  function logout() {
    SpendSmartApi.clearToken();
    window.location.href = "/login";
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.innerText = str;
    return div.innerHTML;
  }

  document.addEventListener("DOMContentLoaded", init);

  return {
    init,
    login,
    register,
    logout,
    getToken: SpendSmartApi.getToken,
  };
})();
