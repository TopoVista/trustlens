function ViewToggle({ mode, onChange }) {
  const buttonStyle = (active) => ({
    padding: "0.4rem 0.8rem",
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--color-border)",
    background: active ? "#fff" : "#f3f4f6",
    cursor: "pointer",
    fontWeight: active ? "bold" : "normal",
  });

  return (
    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
      <button style={buttonStyle(mode === "baseline")} onClick={() => onChange("baseline")}>
        Baseline
      </button>
      <button style={buttonStyle(mode === "verified")} onClick={() => onChange("verified")}>
        Verified
      </button>
    </div>
  );
}

export default ViewToggle;
