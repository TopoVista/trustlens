function InputPanel({ query, onChange, onSubmit, disabled }) {
  return (
    <div
      style={{
        background: "#fff",
        padding: "1.5rem",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
        marginBottom: "1.5rem",
      }}
    >
      <label
        style={{
          display: "block",
          marginBottom: "0.5rem",
          color: "var(--color-text)",
          fontWeight: "bold",
        }}
      >
        Ask a question
      </label>

      <textarea
        value={query}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        placeholder="e.g. What are B-tree indexes?"
        disabled={disabled}
        style={{
          width: "100%",
          padding: "0.75rem",
          fontSize: "1rem",
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--color-border)",
          marginBottom: "1rem",
          resize: "none",
          fontFamily: "var(--font-main)",
        }}
      />

      <button
        onClick={onSubmit}
        disabled={disabled || !query.trim()}
        style={{
          padding: "0.6rem 1.2rem",
          background: "var(--trust-supported)",
          color: "#fff",
          border: "none",
          borderRadius: "var(--radius-sm)",
          cursor: disabled ? "not-allowed" : "pointer",
          opacity: disabled ? 0.6 : 1,
          fontWeight: "bold",
        }}
      >
        Analyze
      </button>
    </div>
  );
}

export default InputPanel;
