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
