function fmtTokens(n) {
  return new Intl.NumberFormat("es-CO").format(n);
}

function fmtUSD(n) {
  return `$${n.toFixed(4)}`;
}

/** Barra comparativa horizontal: el elemento firma de esta interfaz.
 *  Representa visualmente cuántos tokens/costo se "queman" sin
 *  optimización vs. con el análisis selectivo de archivos. */
function CostBar({ label, tokens, maxTokens, cost, variant }) {
  const pct = maxTokens > 0 ? Math.max((tokens / maxTokens) * 100, 3) : 3;
  const color = variant === "naive" ? "var(--bad)" : "var(--good)";

  return (
    <div style={{ marginBottom: 18 }}>
      <div style={barStyles.labelRow}>
        <span style={barStyles.label}>{label}</span>
        <span style={barStyles.value}>
          {fmtTokens(tokens)} tokens · {fmtUSD(cost)}
        </span>
      </div>
      <div style={barStyles.track}>
        <div
          style={{
            ...barStyles.fill,
            width: `${pct}%`,
            background: color,
          }}
        />
      </div>
    </div>
  );
}

function StackBadges({ stack }) {
  const entries = Object.entries(stack).filter(([, v]) => v.length > 0);
  if (entries.length === 0) return null;

  return (
    <div style={resultStyles.stackWrap}>
      {entries.map(([category, items]) =>
        items.map((item) => (
          <span key={`${category}-${item}`} style={resultStyles.badge}>
            <span style={resultStyles.badgeCategory}>{category}</span>
            {item}
          </span>
        ))
      )}
    </div>
  );
}

/** Tarjeta pequeña usada en la fila de metadatos del análisis
 *  (tiempo, modelo, desglose de tokens). */
function StatCard({ label, value, sub }) {
  return (
    <div style={resultStyles.statCard}>
      <span style={resultStyles.statLabel}>{label}</span>
      <span style={resultStyles.statValue}>{value}</span>
      {sub && <span style={resultStyles.statSub}>{sub}</span>}
    </div>
  );
}

/** Lista transparente de qué archivos se enviaron al LLM y por qué
 *  cada uno fue seleccionado, en vez de solo un conteo "8 de 54". */
function FilesAnalyzedList({ files, totalInRepo }) {
  return (
    <section style={resultStyles.section}>
      <h3 style={resultStyles.sectionTitle}>Archivos analizados</h3>
      <p style={resultStyles.sectionNote}>
        {files.length} de {totalInRepo} archivos del repositorio fueron seleccionados y
        enviados al modelo como contexto.
      </p>
      <ul style={resultStyles.filesList}>
        {files.map((f) => (
          <li key={f.path} style={resultStyles.fileItem}>
            <span style={resultStyles.fileCheck}>✓</span>
            <span style={resultStyles.filePath}>{f.path}</span>
            <span style={resultStyles.fileReason}>{f.reason}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function ResultsView({ data }) {
  const {
    repo,
    stack,
    tokens,
    cost_usd,
    documentation,
    files_analyzed,
    total_files_in_repo,
    model,
    analysis_time_seconds,
  } = data;
  const maxTokens = Math.max(tokens.naive_full_repo_estimate, tokens.context_sent_to_llm);

  function downloadReadme() {
    const blob = new Blob([documentation.readme_md || ""], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "README_generado.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={resultStyles.wrap}>
      <header style={resultStyles.header}>
        <h2 style={resultStyles.repoName}>{repo.full_name}</h2>
        <p style={resultStyles.desc}>{repo.description || "Sin descripción en GitHub."}</p>
        <StackBadges stack={stack} />
      </header>

      <div style={resultStyles.statsRow}>
        {analysis_time_seconds != null && (
          <StatCard label="Tiempo de análisis" value={`${analysis_time_seconds}s`} />
        )}
        {model && <StatCard label="Modelo IA" value={model.display_name} />}
        <StatCard label="Prompt" value={`${fmtTokens(tokens.prompt_tokens)} tokens`} />
        <StatCard label="Respuesta" value={`${fmtTokens(tokens.response_tokens)} tokens`} />
        <StatCard label="Total" value={`${fmtTokens(tokens.total_tokens)} tokens`} />
      </div>

      <section style={resultStyles.section}>
        <h3 style={resultStyles.sectionTitle}>Ahorro de contexto</h3>
        <p style={resultStyles.sectionNote}>
          Analizando {files_analyzed.length} de {total_files_in_repo} archivos en vez del repo completo.
        </p>
        <CostBar
          label="Sin optimizar (repo completo)"
          tokens={tokens.naive_full_repo_estimate}
          maxTokens={maxTokens}
          cost={cost_usd.naive_estimate}
          variant="naive"
        />
        <CostBar
          label="Optimizado (archivos clave)"
          tokens={tokens.context_sent_to_llm}
          maxTokens={maxTokens}
          cost={cost_usd.optimized}
          variant="optimized"
        />
        <p style={resultStyles.savings}>
          Ahorro estimado: <strong>{cost_usd.savings_percentage}%</strong>
        </p>
      </section>

      <FilesAnalyzedList files={files_analyzed} totalInRepo={total_files_in_repo} />

      <section style={resultStyles.section}>
        <div style={resultStyles.readmeHeader}>
          <h3 style={resultStyles.sectionTitle}>README generado</h3>
          <button onClick={downloadReadme} style={resultStyles.downloadBtn}>
            ↓ Descargar .md
          </button>
        </div>
        <pre style={resultStyles.readmeBox}>{documentation.readme_md}</pre>
      </section>

      {documentation.key_modules?.length > 0 && (
        <section style={resultStyles.section}>
          <h3 style={resultStyles.sectionTitle}>Módulos clave</h3>
          <ul style={resultStyles.list}>
            {documentation.key_modules.map((m, i) => (
              <li key={i} style={resultStyles.listItem}>{m}</li>
            ))}
          </ul>
        </section>
      )}

      {documentation.suggested_improvements?.length > 0 && (
        <section style={resultStyles.section}>
          <h3 style={resultStyles.sectionTitle}>Sugerencias de mejora</h3>
          <ul style={resultStyles.list}>
            {documentation.suggested_improvements.map((s, i) => (
              <li key={i} style={resultStyles.listItem}>{s}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

const barStyles = {
  labelRow: {
    display: "flex",
    justifyContent: "space-between",
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    marginBottom: 6,
  },
  label: { color: "var(--text-dim)" },
  value: { color: "var(--text)" },
  track: {
    height: 10,
    background: "var(--bg-input)",
    borderRadius: 6,
    overflow: "hidden",
    border: "1px solid var(--border)",
  },
  fill: {
    height: "100%",
    borderRadius: 6,
  },
};

const resultStyles = {
  wrap: { width: "100%", maxWidth: 720, marginTop: 36 },
  header: { marginBottom: 28 },
  repoName: {
    fontFamily: "var(--font-mono)",
    fontSize: 22,
    margin: "0 0 6px",
    color: "var(--accent)",
  },
  desc: { color: "var(--text-dim)", margin: "0 0 14px", fontSize: 14 },
  stackWrap: { display: "flex", flexWrap: "wrap", gap: 8 },
  badge: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    border: "1px solid var(--border)",
    borderRadius: 20,
    padding: "5px 12px",
    color: "var(--text)",
    background: "var(--bg-raised)",
  },
  badgeCategory: { color: "var(--text-dim)", marginRight: 6 },
  statsRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
    gap: 10,
    marginBottom: 20,
  },
  statCard: {
    background: "var(--bg-raised)",
    border: "1px solid var(--border)",
    borderRadius: 10,
    padding: "12px 14px",
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  statLabel: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    color: "var(--text-dim)",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  statValue: { fontSize: 16, fontWeight: 600, color: "var(--text)" },
  statSub: { fontSize: 11, color: "var(--text-dim)" },
  section: {
    background: "var(--bg-raised)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: 24,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 15,
    margin: "0 0 6px",
    letterSpacing: "0.01em",
  },
  sectionNote: { color: "var(--text-dim)", fontSize: 13, marginTop: 0, marginBottom: 18 },
  savings: { fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--good)", margin: 0 },
  filesList: { listStyle: "none", margin: 0, padding: 0 },
  fileItem: {
    display: "flex",
    alignItems: "baseline",
    gap: 10,
    padding: "8px 0",
    borderBottom: "1px solid var(--border)",
    fontSize: 13,
  },
  fileCheck: { color: "var(--good)", fontFamily: "var(--font-mono)" },
  filePath: {
    fontFamily: "var(--font-mono)",
    color: "var(--text)",
    flex: 1,
    wordBreak: "break-all",
  },
  fileReason: { color: "var(--text-dim)", fontSize: 12, whiteSpace: "nowrap" },
  readmeHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  downloadBtn: {
    background: "transparent",
    border: "1px solid var(--border)",
    color: "var(--text)",
    borderRadius: 8,
    padding: "6px 12px",
    fontSize: 12,
    fontFamily: "var(--font-mono)",
    cursor: "pointer",
  },
  readmeBox: {
    background: "var(--bg-input)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: 16,
    fontFamily: "var(--font-mono)",
    fontSize: 12.5,
    lineHeight: 1.6,
    color: "var(--text)",
    whiteSpace: "pre-wrap",
    maxHeight: 400,
    overflowY: "auto",
  },
  list: { margin: 0, paddingLeft: 20, color: "var(--text)", fontSize: 14, lineHeight: 1.7 },
  listItem: { marginBottom: 4 },
};
