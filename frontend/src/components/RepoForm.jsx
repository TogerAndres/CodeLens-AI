import { useState } from "react";

export default function RepoForm({ onSubmit, loading }) {
  const [value, setValue] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!value.trim() || loading) return;
    onSubmit(value.trim());
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <label htmlFor="repo-url" style={styles.label}>
        URL del repositorio público de GitHub
      </label>
      <div style={styles.row}>
        <span style={styles.prompt}>$</span>
        <input
          id="repo-url"
          type="text"
          placeholder="https://github.com/owner/repo"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={loading}
          style={styles.input}
        />
        <button type="submit" disabled={loading} style={styles.button}>
          {loading ? "Analizando…" : "Analizar"}
        </button>
      </div>
    </form>
  );
}

const styles = {
  form: { width: "100%", maxWidth: 720 },
  label: {
    display: "block",
    fontFamily: "var(--font-mono)",
    fontSize: 13,
    color: "var(--text-dim)",
    marginBottom: 10,
    letterSpacing: "0.02em",
  },
  row: {
    display: "flex",
    alignItems: "center",
    background: "var(--bg-input)",
    border: "1px solid var(--border)",
    borderRadius: 10,
    padding: "4px 6px 4px 16px",
    gap: 10,
  },
  prompt: {
    fontFamily: "var(--font-mono)",
    color: "var(--accent)",
    fontSize: 16,
    userSelect: "none",
  },
  input: {
    flex: 1,
    background: "transparent",
    border: "none",
    color: "var(--text)",
    fontFamily: "var(--font-mono)",
    fontSize: 15,
    padding: "12px 0",
  },
  button: {
    background: "var(--accent-gradient)",
    color: "#ffffff",
    border: "none",
    borderRadius: 8,
    padding: "12px 20px",
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
};
