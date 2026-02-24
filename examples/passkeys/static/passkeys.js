import {
  startRegistration,
  startAuthentication,
} from "https://esm.sh/@simplewebauthn/browser@13";

if (/^\d+\.\d+\.\d+\.\d+$/.test(location.hostname)) {
  const el = document.getElementById("ip-warning");
  if (el) el.hidden = false;
}

function getToken() {
  return sessionStorage.getItem("access_token");
}

function saveTokens(data) {
  sessionStorage.setItem("access_token", data.access_token);
  if (data.refresh_token) {
    sessionStorage.setItem("refresh_token", data.refresh_token);
  }
}

function clearTokens() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  };
}

function setStatus(id, msg, ok = true) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = "status " + (ok ? "ok" : "err");
}

async function apiFetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
  return body;
}

function showSection(id) {
  ["auth-section", "passkey-section"].forEach((s) => {
    const el = document.getElementById(s);
    if (el) el.hidden = s !== id;
  });
}

async function loadPasskeys() {
  try {
    const passkeys = await apiFetch("/auth/passkeys", { headers: authHeaders() });
    const list = document.getElementById("passkey-list");
    if (!list) return;
    list.innerHTML = "";

    if (!passkeys.length) {
      list.innerHTML = "<li class='empty'>No passkeys registered yet.</li>";
      return;
    }

    passkeys.forEach((pk) => {
      const li = document.createElement("li");
      li.className = "passkey-item";

      const info = document.createElement("span");
      info.className = "passkey-info";
      const created = new Date(pk.created_at).toLocaleDateString();
      const used = pk.last_used_at
        ? new Date(pk.last_used_at).toLocaleDateString()
        : "never";
      info.textContent = `${pk.name} — added ${created}, last used ${used}`;

      const btn = document.createElement("button");
      btn.textContent = "Remove";
      btn.className = "btn-danger";
      btn.addEventListener("click", async () => {
        try {
          await fetch(`/auth/passkeys/${pk.id}`, {
            method: "DELETE",
            headers: authHeaders(),
          });
          setStatus("passkey-status", `Passkey "${pk.name}" removed.`);
          await loadPasskeys();
        } catch (err) {
          setStatus("passkey-status", err.message, false);
        }
      });

      li.appendChild(info);
      li.appendChild(btn);
      list.appendChild(li);
    });
  } catch (err) {
    setStatus("passkey-status", err.message, false);
  }
}

async function loadProfile() {
  try {
    const user = await apiFetch("/profile", { headers: authHeaders() });
    const el = document.getElementById("user-email");
    if (el) el.textContent = user.email;
    showSection("passkey-section");
    await loadPasskeys();
  } catch {
    clearTokens();
    showSection("auth-section");
  }
}

document.getElementById("register-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("reg-email").value;
  const password = document.getElementById("reg-password").value;
  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    saveTokens(data);
    setStatus("auth-status", "Registered and signed in.");
    await loadProfile();
  } catch (err) {
    setStatus("auth-status", err.message, false);
  }
});

document.getElementById("login-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    saveTokens(data);
    setStatus("auth-status", "Signed in.");
    await loadProfile();
  } catch (err) {
    setStatus("auth-status", err.message, false);
  }
});

document.getElementById("passkey-signin-btn")?.addEventListener("click", async () => {
  const email = document.getElementById("passkey-email").value.trim();
  try {
    const options = await apiFetch("/auth/passkeys/authenticate/begin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(email ? { email } : {}),
    });
    const credential = await startAuthentication({ optionsJSON: options });
    const data = await apiFetch("/auth/passkeys/authenticate/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential }),
    });
    saveTokens(data);
    setStatus("auth-status", "Signed in with passkey.");
    await loadProfile();
  } catch (err) {
    setStatus("auth-status", err.message, false);
  }
});

document.getElementById("add-passkey-btn")?.addEventListener("click", async () => {
  const name = document.getElementById("passkey-name").value.trim() || "My Passkey";
  try {
    const options = await apiFetch("/auth/passkeys/register/begin", {
      method: "POST",
      headers: authHeaders(),
    });
    const credential = await startRegistration({ optionsJSON: options });
    const passkey = await apiFetch("/auth/passkeys/register/complete", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ credential, name }),
    });
    setStatus("passkey-status", `Passkey "${passkey.name}" registered.`);
    await loadPasskeys();
  } catch (err) {
    setStatus("passkey-status", err.message, false);
  }
});

document.getElementById("signout-btn")?.addEventListener("click", async () => {
  try {
    await fetch("/auth/logout", { method: "POST", headers: authHeaders() });
  } finally {
    clearTokens();
    showSection("auth-section");
    setStatus("auth-status", "Signed out.");
  }
});

if (getToken()) {
  loadProfile();
} else {
  showSection("auth-section");
}
