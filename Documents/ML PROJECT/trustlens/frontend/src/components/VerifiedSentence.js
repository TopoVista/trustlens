function VerifiedSentence({ claim, label, score, color }) {
  const bgMap = {
    green: "var(--trust-supported-bg)",
    yellow: "var(--trust-unsupported-bg)",
    red: "var(--trust-contradicted-bg)",
  };

  const textMap = {
    green: "var(--trust-supported)",
    yellow: "var(--trust-unsupported)",
    red: "var(--trust-contradicted)",
  };

  return (
    <div
      title={`${label} (${Math.round(score * 100)}%)`}
      style={{
        background: bgMap[color],
        color: textMap[color],
        padding: "0.75rem 0.9rem",
        borderRadius: "var(--radius-sm)",
        marginBottom: "0.6rem",
        cursor: "help",
        fontSize: "var(--text-base)",
        lineHeight: "var(--line-normal)",
      }}
    >
    {claim}
    </div>
  );

}

export default VerifiedSentence;
