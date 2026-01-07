function LoadingSkeleton() {
  const blockStyle = {
    background: "#e5e7eb",
    height: "1rem",
    borderRadius: "4px",
    marginBottom: "0.75rem",
    animation: "pulse 1.5s infinite",
  };

  return (
    <div
      style={{
        background: "#fff",
        padding: "1.5rem",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
      }}
    >
      <div style={{ ...blockStyle, width: "60%" }} />
      <div style={{ ...blockStyle, width: "90%" }} />
      <div style={{ ...blockStyle, width: "80%" }} />
      <div style={{ ...blockStyle, width: "70%" }} />
    </div>
  );
}

export default LoadingSkeleton;
