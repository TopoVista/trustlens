/**
 * TrustLens API client
 * Communicates with FastAPI backend using VITE_API_URL
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Run end-to-end verification pipeline:
 * Performs single grounded generation and claim-level NLI verification
 */
export async function analyzeQuery(query, k = 5) {
  const url = `${API_BASE}/analyze`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, k }),
  });

  if (!response.ok) {
    let errorMessage = "Analysis request failed";
    try {
      const errorJson = await response.json();
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      const text = await response.text();
      if (text) errorMessage = text;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Run Multi-Agent Vendor Risk & Compliance Assessment:
 * Orchestrates Ingestion, Parsing, Retrieval, Compliance Mapping,
 * Risk Scoring, Findings Report, and QA Claim Verification.
 */
export async function assessVendor(payload) {
  const url = `${API_BASE}/api/assess`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorMessage = "Multi-Agent assessment failed";
    try {
      const errorJson = await response.json();
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      const text = await response.text();
      if (text) errorMessage = text;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Ask the Interactive User Q&A Agent an ad-hoc question about the vendor
 */
export async function askVendorQuestion(vendor, question) {
  const url = `${API_BASE}/api/ask`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ vendor, question }),
  });

  if (!response.ok) {
    let errorMessage = "Q&A inquiry failed";
    try {
      const errorJson = await response.json();
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      const text = await response.text();
      if (text) errorMessage = text;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Check backend health & cold-start status
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(3000)
    });
    return res.ok;
  } catch {
    return false;
  }
}

