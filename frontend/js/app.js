// API Configuration
const API_BASE_URL = "http://localhost:5000/api";

// State Management
let currentTokens = {
  accessToken: localStorage.getItem("auth_access_token") || null,
  refreshToken: localStorage.getItem("auth_refresh_token") || null,
};
let currentUser = JSON.parse(localStorage.getItem("auth_user") || "null");

// DOM Elements
const authSection = document.getElementById("auth-section");
const dashboardSection = document.getElementById("dashboard-section");
const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const alertContainer = document.getElementById("alert-container");

// Role Selection in Register
let selectedRole = "member";
document.querySelectorAll(".role-card").forEach((card) => {
  card.addEventListener("click", () => {
    document.querySelectorAll(".role-card").forEach((c) => c.classList.remove("selected"));
    card.classList.add("selected");
    selectedRole = card.getAttribute("data-role");
  });
});

// Tab Switching
tabLogin.addEventListener("click", () => {
  tabLogin.classList.add("active");
  tabRegister.classList.remove("active");
  loginForm.style.display = "block";
  registerForm.style.display = "none";
  clearAlert();
});

tabRegister.addEventListener("click", () => {
  tabRegister.classList.add("active");
  tabLogin.classList.remove("active");
  loginForm.style.display = "none";
  registerForm.style.display = "block";
  clearAlert();
});

// Alert Helper
function showAlert(message, type = "error") {
  alertContainer.innerHTML = `
    <div class="alert alert-${type}">
      <span>${type === "error" ? "⚠️" : "✅"}</span>
      <span>${message}</span>
    </div>
  `;
}

function clearAlert() {
  alertContainer.innerHTML = "";
}

// Health check to update status badge
async function checkSystemHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    const data = await res.json();
    const badge = document.getElementById("server-status-badge");
    const dbEngineBadge = document.getElementById("db-engine-badge");
    if (badge && data.status === "online") {
      badge.innerHTML = `<span class="status-dot"></span> Backend: Online (Port 5000)`;
      badge.className = "badge badge-green";
    }
    if (dbEngineBadge && data.db_engine) {
      dbEngineBadge.innerText = `DB: ${data.db_engine}`;
    }
  } catch (err) {
    const badge = document.getElementById("server-status-badge");
    if (badge) {
      badge.innerHTML = `<span class="status-dot" style="background:#f43f5e"></span> Backend: Offline`;
      badge.className = "badge";
      badge.style.color = "#f43f5e";
    }
  }
}

// Register Handler
registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearAlert();

  const username = document.getElementById("reg-username").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const confirmPassword = document.getElementById("reg-confirm-password").value;

  if (password !== confirmPassword) {
    showAlert("Passwords do not match.");
    return;
  }

  const submitBtn = registerForm.querySelector("button[type='submit']");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Securing & Registering...</span>`;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username,
        email,
        password,
        role: selectedRole
      })
    });

    const data = await res.json();
    if (!res.ok) {
      showAlert(data.message || "Registration failed.");
    } else {
      handleAuthSuccess(data.user, data.tokens);
    }
  } catch (err) {
    showAlert("Could not connect to the backend server. Make sure port 5000 is running.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
      Create Encrypted Account
    `;
  }
});

// Login Handler
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearAlert();

  const identifier = document.getElementById("login-identifier").value.trim();
  const password = document.getElementById("login-password").value;

  const submitBtn = loginForm.querySelector("button[type='submit']");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Authenticating JWT...</span>`;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password })
    });

    const data = await res.json();
    if (!res.ok) {
      showAlert(data.message || "Invalid credentials.");
    } else {
      handleAuthSuccess(data.user, data.tokens);
    }
  } catch (err) {
    showAlert("Could not reach backend API at port 5000.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg>
      Sign In Securely
    `;
  }
});

// Successful Auth Handler
function handleAuthSuccess(user, tokens) {
  currentUser = user;
  currentTokens = {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token
  };

  localStorage.setItem("auth_user", JSON.stringify(user));
  localStorage.setItem("auth_access_token", tokens.access_token);
  localStorage.setItem("auth_refresh_token", tokens.refresh_token);

  showDashboard();
}

// Display Authenticated Dashboard
function showDashboard() {
  authSection.style.display = "none";
  dashboardSection.style.display = "block";

  document.getElementById("user-name-display").innerText = currentUser.username;
  document.getElementById("dash-username").innerText = currentUser.username;
  document.getElementById("dash-email").innerText = currentUser.email;
  document.getElementById("dash-role").innerText = currentUser.role.toUpperCase();
  document.getElementById("dash-status").innerText = currentUser.is_active ? "Active & Verified" : "Suspended";
  document.getElementById("dash-created").innerText = currentUser.created_at ? new Date(currentUser.created_at).toLocaleString() : "N/A";

  // Display raw JWT token snippet
  document.getElementById("jwt-token-display").innerText = currentTokens.accessToken || "No token available";
  document.getElementById("refresh-token-display").innerText = currentTokens.refreshToken || "No refresh token available";

  // Load audit logs if admin
  if (currentUser.role === "admin") {
    document.getElementById("admin-section").style.display = "block";
    loadAdminData();
  } else {
    document.getElementById("admin-section").style.display = "none";
  }
}

// Refresh Token Request
async function refreshAccessToken() {
  if (!currentTokens.refreshToken) {
    alert("No refresh token stored.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: currentTokens.refreshToken })
    });

    const data = await res.json();
    if (res.ok) {
      currentTokens.accessToken = data.tokens.access_token;
      currentTokens.refreshToken = data.tokens.refresh_token;
      localStorage.setItem("auth_access_token", data.tokens.access_token);
      localStorage.setItem("auth_refresh_token", data.tokens.refresh_token);
      
      document.getElementById("jwt-token-display").innerText = currentTokens.accessToken;
      document.getElementById("refresh-token-display").innerText = currentTokens.refreshToken;
      alert("Token refreshed successfully! Check the renewed JWT signature.");
    } else {
      alert("Refresh failed: " + data.message);
      logout();
    }
  } catch (err) {
    alert("Network error while refreshing token.");
  }
}

// Verify Profile with JWT on Server
async function verifySessionProfile() {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/profile`, {
      headers: {
        "Authorization": `Bearer ${currentTokens.accessToken}`
      }
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Session Valid! Server verified token for user: ${data.user.username}\nRole: ${data.user.role}\nClaims: sub=${data.token_claims.sub}`);
    } else {
      alert(`Token Verification Failed: ${data.message}`);
    }
  } catch (e) {
    alert("Error verifying session with backend.");
  }
}

// Load Admin Database logs
async function loadAdminData() {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/users`, {
      headers: {
        "Authorization": `Bearer ${currentTokens.accessToken}`
      }
    });
    const data = await res.json();
    if (res.ok) {
      const logsBody = document.getElementById("audit-logs-body");
      logsBody.innerHTML = "";
      data.audit_logs.forEach((log) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${log.id}</td>
          <td><strong>${log.username}</strong></td>
          <td><span class="badge ${log.event_type.includes('FAIL') ? 'badge-blue' : 'badge-green'}">${log.event_type}</span></td>
          <td><code>${log.ip_address}</code></td>
          <td>${new Date(log.created_at).toLocaleTimeString()}</td>
        `;
        logsBody.appendChild(row);
      });
    }
  } catch (err) {
    console.error("Failed to load admin data:", err);
  }
}

// Logout Handler
async function logout() {
  if (currentTokens.accessToken) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${currentTokens.accessToken}` }
      });
    } catch (e) {}
  }

  localStorage.removeItem("auth_user");
  localStorage.removeItem("auth_access_token");
  localStorage.removeItem("auth_refresh_token");
  currentUser = null;
  currentTokens = { accessToken: null, refreshToken: null };

  dashboardSection.style.display = "none";
  authSection.style.display = "block";
  clearAlert();
  showAlert("Logged out successfully.", "success");
}

// Attach Button Actions
document.getElementById("btn-logout").addEventListener("click", logout);
document.getElementById("btn-refresh-token").addEventListener("click", refreshAccessToken);
document.getElementById("btn-verify-session").addEventListener("click", verifySessionProfile);

// Startup Initialization
window.addEventListener("DOMContentLoaded", () => {
  checkSystemHealth();
  setInterval(checkSystemHealth, 10000);

  if (currentUser && currentTokens.accessToken) {
    showDashboard();
  }
});
