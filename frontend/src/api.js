// Resolve API base URL with runtime environment detection.
// When running on a known production domain, always point at the production
// backend regardless of what VITE_API_URL was set to at build time.
const _host = typeof window !== "undefined" ? window.location.hostname : "";
const _isProdHost = _host.endsWith(".vercel.app") || _host === "trustlens-alpha.vercel.app";

const API_BASE = _isProdHost
  ? "https://trustlens-api.onrender.com"
  : (import.meta.env.VITE_API_URL || "http://localhost:8000");

let currentUserId = null;
let currentTokenGetter = null;

/**
 * Configure active authenticated user context for API requests.
 */
export function setAuthContext(userId, tokenGetter = null) {
  currentUserId = userId;
  currentTokenGetter = tokenGetter;
}

async function buildHeaders(customHeaders = {}) {
  const headers = { ...customHeaders };
  if (currentUserId) {
    headers["x-user-id"] = currentUserId;
  }
  if (currentTokenGetter && typeof currentTokenGetter === "function") {
    try {
      const token = await currentTokenGetter();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    } catch {}
  }
  return headers;
}

// --- Knowledge Intelligence Workspace APIs (Per-User Hard Disk Isolation) ---

export async function getUserStorageInfo() {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/me/storage`, { headers });
  if (!res.ok) throw new Error("Failed to fetch user storage metrics");
  return res.json();
}

export async function listWorkspaces() {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces`, { headers });
  if (!res.ok) throw new Error("Failed to fetch workspaces");
  return res.json();
}

export async function createWorkspace(name, description = "") {
  const headers = await buildHeaders({ "Content-Type": "application/json" });
  const res = await fetch(`${API_BASE}/api/workspaces`, {
    method: "POST",
    headers,
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error("Failed to create workspace");
  return res.json();
}

export async function getWorkspaceHealth(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/health`, { headers });
  if (!res.ok) throw new Error("Failed to fetch workspace health");
  return res.json();
}

export async function getWorkspaceDiscoveries(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/discoveries`, { headers });
  if (!res.ok) throw new Error("Failed to fetch discoveries");
  return res.json();
}

export async function uploadDocument(workspaceId, { title, filename, raw_content, file_type = "text", authority_level = "HIGH" }) {
  const headers = await buildHeaders({ "Content-Type": "application/json" });
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/documents`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      title,
      filename: filename || `${title.toLowerCase().replace(/\s+/g, "_")}.txt`,
      raw_content,
      file_type,
      authority_level,
    }),
  });
  if (!res.ok) {
    let msg = "Failed to ingest document";
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function getWorkspaceDocuments(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/documents`, { headers });
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function getWorkspaceClaims(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/claims`, { headers });
  if (!res.ok) throw new Error("Failed to fetch claims");
  return res.json();
}

export async function getWorkspaceEntities(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/entities`, { headers });
  if (!res.ok) throw new Error("Failed to fetch entities");
  return res.json();
}

export async function getWorkspaceTimeline(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/timeline`, { headers });
  if (!res.ok) throw new Error("Failed to fetch timeline");
  return res.json();
}

export async function getWorkspaceRules(workspaceId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/rules`, { headers });
  if (!res.ok) throw new Error("Failed to fetch rules");
  return res.json();
}

export async function addWorkspaceRule(workspaceId, { rule_type, rule_key, rule_value }) {
  const headers = await buildHeaders({ "Content-Type": "application/json" });
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/rules`, {
    method: "POST",
    headers,
    body: JSON.stringify({ rule_type, rule_key, rule_value }),
  });
  if (!res.ok) throw new Error("Failed to add semantic rule");
  return res.json();
}

export async function queryKnowledge(workspaceId, query) {
  const headers = await buildHeaders({ "Content-Type": "application/json" });
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/query`, {
    method: "POST",
    headers,
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    let msg = "Query execution failed";
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "ok";
  } catch {
    return false;
  }
}
