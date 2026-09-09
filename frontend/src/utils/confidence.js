/**
 * Convert a confidence value to the integer percentage shown in the UI.
 *
 * Legacy endpoints expose a 0–1 ratio, while workspace analysis returns an
 * already-scaled 0–100 percentage. Accept both contracts during the
 * transition so a valid 94.1 can never become 9410% in the interface.
 */
export function toConfidencePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;

  const percent = numeric >= 0 && numeric <= 1 ? numeric * 100 : numeric;
  return Math.round(Math.min(100, Math.max(0, percent)));
}
