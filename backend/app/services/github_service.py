"""
github_service.py
Encapsula toda la comunicación con la API REST de GitHub.

Nota: sin token, GitHub limita a 60 requests/hora por IP.
Con un Personal Access Token (variable GITHUB_TOKEN), el límite sube a 5000/hora.
Crea uno en https://github.com/settings/tokens (no necesita scopes especiales
para repos públicos, solo "public_repo" si quieres leer privados tuyos).
"""

import os
import base64
import re
import requests

GITHUB_API = "https://api.github.com"

# Archivos que nos dicen mucho sobre el stack tecnológico de un repo.
# Si existen en la raíz (o cerca), los priorizamos para enviar al LLM.
KEY_FILES = [
    "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
    "composer.json", "Gemfile", "pom.xml", "build.gradle",
    "Dockerfile", "docker-compose.yml", "go.mod", "Cargo.toml",
    "tsconfig.json", "vite.config.js", "vite.config.ts", "README.md",
]

# Motivo legible por el que cada archivo clave fue seleccionado.
# Se usa para mostrarle al usuario "por qué" se eligió cada archivo,
# no solo "cuáles" se eligieron.
KEY_FILE_REASONS = {
    "package.json": "Dependencias (Node.js)",
    "requirements.txt": "Librerías Python",
    "pyproject.toml": "Librerías Python (Poetry)",
    "Pipfile": "Librerías Python (Pipenv)",
    "composer.json": "Dependencias (PHP)",
    "Gemfile": "Dependencias (Ruby)",
    "pom.xml": "Dependencias (Java/Maven)",
    "build.gradle": "Dependencias (Java/Gradle)",
    "Dockerfile": "Configuración de infraestructura",
    "docker-compose.yml": "Configuración de infraestructura",
    "go.mod": "Dependencias (Go)",
    "Cargo.toml": "Dependencias (Rust)",
    "tsconfig.json": "Configuración de TypeScript",
    "vite.config.js": "Configuración del frontend",
    "vite.config.ts": "Configuración del frontend",
    "README.md": "Documentación del proyecto",
}

# Nombres de archivo que delatan un punto de entrada de la aplicación.
ENTRYPOINT_PATTERN = re.compile(r"(app|main|index|server|run)\.")

# Extensiones de código relevantes para conteo y muestreo
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb",
    ".php", ".c", ".cpp", ".cs", ".html", ".css", ".sql", ".rs",
}


def _headers():
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_repo_url(url: str):
    """Extrae (owner, repo) de una URL de GitHub. Lanza ValueError si no es válida."""
    url = url.strip().rstrip("/")
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        raise ValueError("URL de GitHub no válida. Usa el formato https://github.com/owner/repo")
    return match.group(1), match.group(2)


def get_repo_metadata(owner: str, repo: str) -> dict:
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=_headers(), timeout=15)
    if resp.status_code == 404:
        raise ValueError("Repositorio no encontrado (¿es privado o no existe?)")
    if resp.status_code == 403:
        raise ValueError("Límite de la API de GitHub alcanzado. Configura GITHUB_TOKEN para subir el límite.")
    resp.raise_for_status()
    data = resp.json()
    return {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "default_branch": data.get("default_branch", "main"),
        "stars": data.get("stargazers_count", 0),
        "language": data.get("language"),
        "size_kb": data.get("size", 0),
    }


def get_file_tree(owner: str, repo: str, branch: str) -> list:
    """Devuelve el árbol completo de archivos (recursivo) del repo."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=_headers(), timeout=20,
    )
    resp.raise_for_status()
    tree = resp.json().get("tree", [])
    # Solo nos interesan los blobs (archivos), no los árboles (carpetas)
    return [item for item in tree if item.get("type") == "blob"]


def get_file_content(owner: str, repo: str, path: str) -> str:
    """Descarga y decodifica el contenido de un archivo individual."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
        headers=_headers(), timeout=15,
    )
    if resp.status_code != 200:
        return ""
    data = resp.json()
    if data.get("encoding") == "base64" and data.get("content"):
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def _reason_for_key_file(path: str) -> str:
    base = os.path.basename(path)
    for key, reason in KEY_FILE_REASONS.items():
        if base == key or path.endswith(key):
            return reason
    return "Archivo de configuración"


def _reason_for_code_file(path: str) -> str:
    base = os.path.basename(path)
    if ENTRYPOINT_PATTERN.search(base):
        if any(seg in path for seg in ("frontend", "client", "src/components", "ui")):
            return "Punto de entrada (frontend)"
        return "Punto de entrada"
    return "Código fuente relevante"


def select_files_for_context(file_tree: list, max_files: int = 8, max_file_size: int = 20000):
    """
    Elige un subconjunto representativo de archivos para mandarle al LLM,
    sin necesidad de embeddings/RAG: prioriza archivos de configuración
    (KEY_FILES) y luego archivos de código relativamente pequeños.
    Esto evita mandar el repo completo y dispara directo el costo en tokens.

    Devuelve una lista de dicts {path, reason} para que el frontend pueda
    mostrar, de forma transparente, qué archivos se usaron y por qué cada
    uno fue elegido (en vez de solo un conteo "8 de 54 archivos").
    """
    paths = [f["path"] for f in file_tree if f.get("size", 0) <= max_file_size]

    key_matches = [p for p in paths if any(p.endswith(k) or p == k for k in KEY_FILES)]
    code_matches = [
        p for p in paths
        if os.path.splitext(p)[1] in CODE_EXTENSIONS and p not in key_matches
    ]
    # Heurística simple: priorizamos archivos "principales" (app, main, index, server, run)
    code_matches.sort(key=lambda p: (
        0 if ENTRYPOINT_PATTERN.search(os.path.basename(p)) else 1,
        p.count("/"),  # archivos más cerca de la raíz primero
    ))

    selected_paths = (key_matches + code_matches)[:max_files]

    selected = []
    for p in selected_paths:
        reason = _reason_for_key_file(p) if p in key_matches else _reason_for_code_file(p)
        selected.append({"path": p, "reason": reason})
    return selected


def detect_stack(file_tree: list) -> dict:
    """Detección de stack por presencia de archivos clave, sin parsear AST (Tree-sitter queda para v2)."""
    paths = {f["path"] for f in file_tree}
    names = {os.path.basename(p) for p in paths}

    stack = {"backend": [], "frontend": [], "database": [], "infra": [], "other": []}

    checks = [
        ("requirements.txt", "backend", "Python"),
        ("pyproject.toml", "backend", "Python (Poetry)"),
        ("manage.py", "backend", "Django"),
        ("package.json", "frontend", "Node.js / JavaScript"),
        ("composer.json", "backend", "PHP"),
        ("Gemfile", "backend", "Ruby"),
        ("go.mod", "backend", "Go"),
        ("Cargo.toml", "backend", "Rust"),
        ("pom.xml", "backend", "Java (Maven)"),
        ("build.gradle", "backend", "Java/Kotlin (Gradle)"),
        ("Dockerfile", "infra", "Docker"),
        ("docker-compose.yml", "infra", "Docker Compose"),
        ("vite.config.js", "frontend", "Vite"),
        ("vite.config.ts", "frontend", "Vite"),
        ("tailwind.config.js", "frontend", "Tailwind CSS"),
        ("next.config.js", "frontend", "Next.js"),
    ]
    for filename, bucket, label in checks:
        if filename in names:
            stack[bucket].append(label)

    ext_counts = {}
    for p in paths:
        ext = os.path.splitext(p)[1]
        if ext:
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

    if any(ext in (".sql",) for ext in ext_counts):
        stack["database"].append("SQL")

    # Dedup conservando orden
    for k in stack:
        seen = set()
        deduped = []
        for v in stack[k]:
            if v not in seen:
                deduped.append(v)
                seen.add(v)
        stack[k] = deduped

    return stack
