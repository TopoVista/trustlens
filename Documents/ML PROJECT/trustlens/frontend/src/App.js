import { useState } from "react";
import InputPanel from "./components/InputPanel";
import LoadingSkeleton from "./components/LoadingSkeleton";
import ConfidenceMeter from "./components/ConfidenceMeter";
import VerifiedSentence from "./components/VerifiedSentence";
import ViewToggle from "./components/ViewToggle";
import { analyzeQuery, getBaselineAnswer } from "./api";

function App() {
  const [error, setError] = useState(null);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("verified");

  const [baselineAnswer, setBaselineAnswer] = useState("");
  const [verifiedClaims, setVerifiedClaims] = useState([]);

  async function handleAnalyze() {
    setError(null);
    setLoading(true);
    setBaselineAnswer("");
    setVerifiedClaims([]);

    try {
      const [baseline, verified] = await Promise.all([
        getBaselineAnswer(query),
        analyzeQuery(query),
      ]);

      setBaselineAnswer(baseline.answer);
      setVerifiedClaims(verified.verified_claims);
    } catch (err) {
        console.error(err);
        setError(
          err.message || "Unable to reach the analysis server. Please try again."
        );
    }finally {
      setLoading(false);
    }
  }

  const faithfulness =
    verifiedClaims.length === 0
      ? 0
      : verifiedClaims.reduce((s, c) => s + c.score, 0) /
        verifiedClaims.length;

  return (
    <div
      style={{
        maxWidth: "720px",
        margin: "2rem auto",
        padding: "0 1rem",
        fontFamily: "var(--font-main)",
      }}
    >
      <h1 style={{ fontSize: "var(--text-2xl)", marginBottom: "0.25rem" }}>
       TrustLens
      </h1>

      <p
        style={{
        color: "var(--color-muted)",
        fontSize: "var(--text-sm)",
        marginBottom: "2rem",
      }}
      >
        Compare baseline vs verified answers
      </p>

      <InputPanel
        query={query}
        onChange={setQuery}
        onSubmit={handleAnalyze}
        disabled={loading}
      />

      {error && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem",
            background: "var(--trust-contradicted-bg)",
            color: "var(--trust-contradicted)",
            borderRadius: "var(--radius-sm)",
            fontSize: "var(--text-sm)",
          }}
        >
          {error}
        </div>
      )}


      {loading && <LoadingSkeleton />}

      {!loading && (baselineAnswer || verifiedClaims.length > 0) && (
        <div style={{ marginTop: "2rem" }}>
          <ViewToggle mode={mode} onChange={setMode} />

          {mode === "baseline" && (
            <div
              style={{
                background: "#fff",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--color-border)",
              }}
            >
              {baselineAnswer}
            </div>
          )}

          {mode === "verified" && (
            <>
              {verifiedClaims.map((c, i) => (
                <VerifiedSentence key={i} {...c} />
              ))}
              <ConfidenceMeter score={faithfulness} />
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
