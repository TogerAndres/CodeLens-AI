# Propuesta original: LLM Cost Analyzer

> Documento de referencia con la idea completa (versión profesional, con
> RAG Simulator, Memory Compression, etc.) de la que este MVP es un recorte
> deliberado para entrar en 1-2 semanas. Útil si decides extender el
> proyecto hacia la v2 después de conseguir entrevistas.

Ver conversación con Claude del 24 de junio de 2026 para el documento
completo y el análisis de diferenciación frente a Langfuse, Helicone y
LLMeter que llevó a elegir "AI Repository Assistant" como dirección final.

Resumen de la decisión:
- Idea original: contador de tokens + calculadora de costos + optimizador
  de prompts + simulador RAG + dashboard.
- Problema: ya existen herramientas establecidas (Langfuse, Helicone,
  LLMeter) que hacen observabilidad de tokens/costos mejor que un MVP junior.
- Pivote: en vez de "monitorear tokens", construir algo que analiza
  repositorios de código reales (conecta con el perfil de Control RASS,
  NAVBOT, FITEG) y genera documentación optimizando el contexto enviado
  al LLM — eso sí es diferenciado para un junior.
- Recorte para 1-2 semanas: sin Tree-sitter, sin ChromaDB/embeddings, sin
  diagramas automáticos. Selección heurística de archivos clave en vez de
  RAG real. Eso queda documentado como roadmap v2 en el README principal.
