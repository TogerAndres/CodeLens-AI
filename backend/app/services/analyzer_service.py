"""
analyzer_service.py
Conteo de tokens y armado del "contexto" que se manda al LLM.
Usamos tiktoken (gratis, corre local) en vez de mandar el texto a un
endpoint externo solo para contar — eso evita gastar tokens reales
únicamente para medir tokens.
"""

import tiktoken

# cl100k_base es el encoding usado por GPT-4/3.5 y es una aproximación
# razonable para estimar tokens en cualquier LLM moderno (incluyendo Claude,
# que no expone un tokenizer público idéntico, pero el orden de magnitud
# es el que importa para este análisis).
#
# Carga perezosa (lazy): tiktoken descarga la tabla BPE desde un blob de
# Azure la PRIMERA vez que se usa, y eso puede fallar por restricciones de
# red en algunos hosts. Si falla, caemos a una heurística simple
# (~4 caracteres por token) en vez de tumbar el servidor.
_ENCODING = None
_ENCODING_FAILED = False


def _get_encoding():
    global _ENCODING, _ENCODING_FAILED
    if _ENCODING is None and not _ENCODING_FAILED:
        try:
            _ENCODING = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENCODING_FAILED = True
    return _ENCODING


def count_tokens(text: str) -> int:
    if not text:
        return 0
    encoding = _get_encoding()
    if encoding is not None:
        return len(encoding.encode(text))
    # Fallback: heurística ~4 caracteres por token (razonable para inglés/español)
    return len(text) // 4


def build_context(repo_meta: dict, stack: dict, files_content: dict) -> str:
    """
    Construye el bloque de texto que se le manda al LLM para generar el README.
    files_content: dict {path: contenido}
    """
    parts = [
        f"Repositorio: {repo_meta.get('full_name')}",
        f"Descripción actual: {repo_meta.get('description') or 'N/A'}",
        f"Lenguaje principal (GitHub): {repo_meta.get('language') or 'N/A'}",
        f"Stack detectado: {stack}",
        "",
        "Archivos clave:",
    ]
    for path, content in files_content.items():
        parts.append(f"\n--- {path} ---\n{content[:4000]}")  # corta archivos largos
    return "\n".join(parts)


def estimate_cost_usd(input_tokens: int, output_tokens: int,
                       price_in_per_million: float = 3.0,
                       price_out_per_million: float = 15.0) -> float:
    """
    Precios por defecto aproximan Claude Sonnet ($3/$15 por millón de tokens).
    Ajusta estos valores si usas otro modelo.
    """
    return round(
        (input_tokens / 1_000_000) * price_in_per_million
        + (output_tokens / 1_000_000) * price_out_per_million,
        4,
    )
