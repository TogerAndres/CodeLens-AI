const API_BASE = import.meta.env.VITE_API_URL || "";

export async function analyzeRepo(repoUrl) {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Error analizando el repositorio");
  }

  return data;
}
