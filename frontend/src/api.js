// Vite replaces VITE_API_URL while building the bundle. Never hard-code a
// production backend here: Vercel preview and production builds must point at
// the endpoint configured for that deployment.
const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .trim()
  .replace(/\/+$/, "");

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
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(`Failed to fetch workspaces: ${detail}`);
  }
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

export async function getWorkspaceGraph(workspaceId, options = {}) {
  const headers = await buildHeaders();
  const params = new URLSearchParams();
  if (options.mode) params.set('mode', options.mode);
  if (options.minConfidence !== undefined) params.set('min_confidence', String(options.minConfidence));
  if (options.documentId) params.set('document_id', options.documentId);
  if (options.limit) params.set('limit', String(options.limit));
  const suffix = params.toString() ? `?${params}` : '';
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/graph${suffix}`, { headers });
  if (!res.ok) throw new Error('Failed to fetch workspace graph');
  return res.json();
}

export async function getWorkspaceGraphNode(workspaceId, nodeId) {
  const headers = await buildHeaders();
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/graph/nodes/${encodeURIComponent(nodeId)}`, { headers });
  if (!res.ok) throw new Error('Failed to fetch graph node details');
  return res.json();
}

export async function getWorkspaceGraphPath(workspaceId, source, target) {
  const headers = await buildHeaders();
  const params = new URLSearchParams({ source, target });
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/graph/path?${params}`, { headers });
  if (!res.ok) throw new Error('Failed to find a reasoning path');
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

/**
 * Run a workspace query over a POST-based SSE stream. Status messages are
 * transient pipeline updates; the final `result` event is the normal answer
 * contract consumed by the rest of the UI.
 */
export async function queryKnowledgeStream(workspaceId, query, onStatus = () => {}) {
  const headers = await buildHeaders({
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
  });
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/query/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({ query }),
  });
  if (res.status === 404) {
    // During a rolling Vercel/Render deployment the SPA can arrive before the
    // newly deployed API route. Preserve the established query workflow until
    // the streaming backend is available.
    onStatus("Running the verification path.");
    return queryKnowledge(workspaceId, query);
  }
  if (!res.ok || !res.body) {
    let msg = "Query stream failed";
    try { const body = await res.json(); msg = body.detail || msg; } catch {}
    throw new Error(msg);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result = null;

  const consumeEvent = (block) => {
    const lines = block.split("\n");
    const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim() || "message";
    const data = lines
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trim())
      .join("\n");
    if (!data) return;
    const payload = JSON.parse(data);
    if (event === "status") onStatus(payload.message || "Working on your evidence…");
    if (event === "result") result = payload;
    if (event === "error") throw new Error(payload.message || "Knowledge query failed.");
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let separator = buffer.indexOf("\n\n");
    while (separator !== -1) {
      consumeEvent(buffer.slice(0, separator));
      buffer = buffer.slice(separator + 2);
      separator = buffer.indexOf("\n\n");
    }
    if (done) break;
  }

  if (!result) throw new Error("Query stream ended before an answer was returned.");
  return result;
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
