"""
app.py
Punto de entrada de la API Flask.

Endpoint principal:
  POST /api/analyze
  body: {"repo_url": "https://github.com/owner/repo"}

Variables de entorno necesarias (ver .env.example):
  ANTHROPIC_API_KEY  -> para generar el README/resumen
  GITHUB_TOKEN        -> opcional, sube el rate limit de la API de GitHub
"""

import os
import time
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from app.services import github_service, analyzer_service, llm_service

load_dotenv()

app = Flask(__name__)
CORS(app)  # en producción, restringe esto al dominio real del frontend

MODEL_DISPLAY_NAMES = {
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
}


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze_repo():
    data = request.get_json(silent=True) or {}
    repo_url = data.get("repo_url", "")

    if not repo_url:
        return jsonify({"error": "Falta 'repo_url' en el body de la petición"}), 400

    started_at = time.perf_counter()

    try:
        owner, repo = github_service.parse_repo_url(repo_url)

        repo_meta = github_service.get_repo_metadata(owner, repo)
        file_tree = github_service.get_file_tree(owner, repo, repo_meta["default_branch"])
        stack = github_service.detect_stack(file_tree)

        selected_files = github_service.select_files_for_context(file_tree)
        selected_paths = [f["path"] for f in selected_files]
        files_content = {
            path: github_service.get_file_content(owner, repo, path)
            for path in selected_paths
        }

        context = analyzer_service.build_context(repo_meta, stack, files_content)
        context_tokens = analyzer_service.count_tokens(context)

        # Para comparar "costo sin optimizar" (repo completo) vs "costo optimizado"
        # (solo archivos clave), estimamos el tamaño total del repo en tokens.
        full_repo_size_chars = sum(f.get("size", 0) for f in file_tree)
        naive_token_estimate = full_repo_size_chars // 4  # heurística: ~4 chars/token

        model_name = "gemini-2.5-flash"
        llm_output = llm_service.generate_repo_documentation(context, model=model_name)

        prompt_tokens = llm_output["usage"].get("input_tokens", context_tokens)
        response_tokens = llm_output["usage"].get("output_tokens", 0)
        total_tokens = prompt_tokens + response_tokens

        cost_optimized = analyzer_service.estimate_cost_usd(prompt_tokens, response_tokens)
        cost_naive = analyzer_service.estimate_cost_usd(naive_token_estimate, 500)

        savings_pct = (
            round((1 - cost_optimized / cost_naive) * 100, 1)
            if cost_naive > 0 else 0
        )

        elapsed_seconds = round(time.perf_counter() - started_at, 1)

        return jsonify({
            "repo": repo_meta,
            "stack": stack,
            "files_analyzed": selected_files,
            "total_files_in_repo": len(file_tree),
            "model": {
                "id": model_name,
                "display_name": MODEL_DISPLAY_NAMES.get(model_name, model_name),
            },
            "analysis_time_seconds": elapsed_seconds,
            "tokens": {
                "context_sent_to_llm": context_tokens,
                "naive_full_repo_estimate": naive_token_estimate,
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,
            },
            "cost_usd": {
                "optimized": cost_optimized,
                "naive_estimate": cost_naive,
                "savings_percentage": savings_pct,
            },
            "documentation": llm_output["result"],
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Error interno analizando el repositorio", "detail": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
