const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// --- Knowledge Intelligence Workspace APIs ---

export async function listWorkspaces() {
  const res = await fetch(`${API_BASE}/api/workspaces`);
  if (!res.ok) throw new Error("Failed to fetch workspaces");
  return res.json();
}

export async function createWorkspace(name, description = "") {
  const res = await fetch(`${API_BASE}/api/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error("Failed to create workspace");
  return res.json();
}

export async function getWorkspaceHealth(workspaceId) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/health`);
  if (!res.ok) throw new Error("Failed to fetch workspace health");
  return res.json();
}

export async function getWorkspaceDiscoveries(workspaceId) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/discoveries`);
  if (!res.ok) throw new Error("Failed to fetch discoveries");
  return res.json();
}

export async function uploadDocument(workspaceId, { title, filename, raw_content, file_type = "text", authority_level = "HIGH" }) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function getWorkspaceClaims(workspaceId) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/claims`);
  if (!res.ok) throw new Error("Failed to fetch claims");
  return res.json();
}

export async function getWorkspaceEntities(workspaceId) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/entities`);
  if (!res.ok) throw new Error("Failed to fetch entities");
  return res.json();
}

export async function getWorkspaceTimeline(workspaceId) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/timeline`);
  if (!res.ok) throw new Error("Failed to fetch timeline");
  return res.json();
}

export async function getWorkspaceRules(workspaceId) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/rules`);
  if (!res.ok) throw new Error("Failed to fetch rules");
  return res.json();
}

export async function addWorkspaceRule(workspaceId, { rule_type, rule_key, rule_value }) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rule_type, rule_key, rule_value }),
  });
  if (!res.ok) throw new Error("Failed to add semantic rule");
  return res.json();
}

export async function queryKnowledge(workspaceId, query) {
  const res = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch {
    return false;
  }
}


