import { useState } from "react";
import RepoForm from "./components/RepoForm.jsx";
import ResultsView from "./components/ResultsView.jsx";
import { analyzeRepo } from "./services/api.js";

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAnalyze(repoUrl) {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await analyzeRepo(repoUrl);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.inner}>
        <header style={styles.hero}>
          <span style={styles.eyebrow}>AI Repository Assistant</span>
          <h1 style={styles.title}>
            Pega un repo. <span style={styles.titleAccent}>Mira cuánto cuesta entenderlo.</span>
          </h1>
          <p style={styles.subtitle}>
            Analiza la estructura de un repositorio de GitHub, detecta su stack y genera
            documentación técnica con un LLM — enviando solo los archivos que importan,
            no el repo completo.
          </p>
        </header>

        <RepoForm onSubmit={handleAnalyze} loading={loading} />

        {error && <div style={styles.error}>⚠ {error}</div>}

        {loading && (
          <div style={styles.loadingBox}>
            <span style={styles.loadingDot} /> Leyendo árbol de archivos y generando documentación…
          </div>
        )}

        {data && <ResultsView data={data} />}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    padding: "64px 24px",
  },
  inner: {
    width: "100%",
    maxWidth: 720,
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
  },
  hero: { marginBottom: 36 },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    color: "var(--accent)",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  title: {
    fontSize: "clamp(28px, 4vw, 38px)",
    lineHeight: 1.2,
    margin: "10px 0 14px",
  },
  titleAccent: {
    backgroundImage: "var(--accent-gradient)",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
  },
  subtitle: {
    color: "var(--text-dim)",
    fontSize: 15,
    lineHeight: 1.6,
    maxWidth: 600,
    margin: 0,
  },
  error: {
    marginTop: 18,
    padding: "12px 16px",
    background: "rgba(224,101,79,0.12)",
    border: "1px solid var(--bad)",
    borderRadius: 8,
    color: "var(--bad)",
    fontSize: 14,
    maxWidth: 720,
  },
  loadingBox: {
    marginTop: 24,
    fontFamily: "var(--font-mono)",
    fontSize: 13,
    color: "var(--text-dim)",
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  loadingDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "var(--accent)",
    display: "inline-block",
  },
};
