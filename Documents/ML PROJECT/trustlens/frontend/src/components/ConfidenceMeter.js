function ConfidenceMeter({ score }) {
  const percentage = Math.round(score * 100);

  let color = "var(--trust-unsupported)";
  if (percentage >= 70) color = "var(--trust-supported)";
  if (percentage < 40) color = "var(--trust-contradicted)";

  return (
    <div
      style={{
        marginTop: "1.5rem",
        background: "#fff",
        padding: "1rem",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
      }}
    >
      <div
        style={{
          marginBottom: "0.5rem",
          fontWeight: "bold",
          color: "var(--color-text)",
        }}
      >
        Faithfulness: {percentage}%
      </div>

      <div
        style={{
          height: "10px",
          background: "#e5e7eb",
          borderRadius: "5px",
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: "100%",
            background: color,
            borderRadius: "5px",
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}

export default ConfidenceMeter;
