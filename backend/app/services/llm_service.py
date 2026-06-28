import os
import json
from google import genai

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Falta GEMINI_API_KEY en las variables de entorno."
            )
        _client = genai.Client(api_key=api_key)
    return _client


SYSTEM_PROMPT = """
Eres un asistente que analiza repositorios de código y genera documentación
técnica clara y profesional.

REGLAS ESTRICTAS contra alucinaciones (síguelas siempre, sin excepción):
1. NUNCA inventes, asumas ni infieras tecnologías, librerías, frameworks,
   patrones de arquitectura o componentes que no estén explícitamente
   presentes en el "Stack detectado" o en el contenido de los archivos
   que se te entregan a continuación.
2. Solo puedes mencionar una herramienta, librería o tecnología si aparece
   textualmente en el nombre de un archivo, en una ruta, en un import,
   en una dependencia declarada (package.json, requirements.txt, etc.) o
   en el contenido provisto. Si no aparece, no la menciones.
3. Si no tienes suficiente información en los archivos analizados para
   responder algo con certeza (por ejemplo, el propósito exacto de un
   módulo, o si el proyecto usa cierta tecnología), dilo explícitamente
   usando la frase exacta:
   "No fue posible confirmar esta información con los archivos analizados."
   No "rellenes" ese vacío con una suposición razonable: es preferible
   admitir la incertidumbre que afirmar algo no verificado.
4. No generalices a partir de proyectos similares que conozcas. Describe
   ÚNICAMENTE lo que está demostrado en el contexto entregado, aunque el
   resultado sea más corto o menos impresionante.
5. Si detectas una posible tecnología pero no estás seguro porque el
   archivo relevante no fue incluido en el contexto, indícalo como
   "no confirmado" en vez de afirmarlo como un hecho.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:

{
  "readme_md": "...",
  "summary": "...",
  "key_modules": ["..."],
  "suggested_improvements": ["..."]
}

No incluyas texto antes ni después del JSON. No uses bloques de código
Markdown (```), responde solo el objeto JSON crudo.
"""


def generate_repo_documentation(context: str,
                                model: str = "gemini-2.5-flash") -> dict:

    client = _get_client()

    response = client.models.generate_content(
        model=model,
        contents=f"{SYSTEM_PROMPT}\n\n{context}",
    )

    raw_text = response.text.strip()

    # Si Gemini devuelve ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "")
        raw_text = raw_text.replace("```", "")
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except Exception:
        parsed = {
            "readme_md": raw_text,
            "summary": "No se pudo convertir la respuesta a JSON.",
            "key_modules": [],
            "suggested_improvements": [],
        }

    usage = {}

    if hasattr(response, "usage_metadata") and response.usage_metadata:
        usage = {
            "input_tokens": getattr(
                response.usage_metadata,
                "prompt_token_count",
                0
            ),
            "output_tokens": getattr(
                response.usage_metadata,
                "candidates_token_count",
                0
            ),
        }

    return {
        "result": parsed,
        "usage": usage,
    }