const API_BASE = process.env.REACT_APP_API_BASE;

export async function analyzeQuery(query) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, k: 5 }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Analyze failed");
  }

  return res.json();
}

export async function getBaselineAnswer(query) {
  const res = await fetch(`${API_BASE}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, k: 5 }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Baseline failed");
  }

  return res.json();
}
