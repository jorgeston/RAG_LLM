from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal

# --- Pydantic Models (Schemas) ---
# Modelo para la ingesta de documentos
class IngestRequest(BaseModel):
    content: str
    document_type: Literal['pdf', 'text', 'html', 'markdown']

class IngestResponse(BaseModel):
    status: Literal['success', 'error']
    message: str
    chunks_created: int

# Modelo para las consultas
class QueryRequest(BaseModel):
    question: str

class Source(BaseModel):
    page: int
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

# --- FastAPI App Instance ---
app = FastAPI(
    title="GenAI RAG Microservice",
    description="A RAG microservice with Langfuse observability.",
    version="0.1.0",
)

# --- API Endpoints ---
@app.get("/health")
def health_check():
    """Verifica que el servicio esté funcionando."""
    return {"status": "ok"}

@app.post("/ingest", response_model=IngestResponse)
def ingest_document(request: IngestRequest):
    """Endpoint para ingerir y procesar un documento."""
    # Lógica de ingesta irá aquí. Por ahora, es un dummy.
    print(f"Ingesting content of type: {request.document_type}")

    # Simulación
    chunks_creados = 15 

    return {
        "status": "success",
        "message": f"Successfully ingested content.",
        "chunks_created": chunks_creados
    }

@app.post("/query", response_model=QueryResponse)
def query_service(request: QueryRequest):
    """Endpoint para hacer una pregunta al sistema RAG."""
    # Lógica de consulta irá aquí. Por ahora, es un dummy.
    print(f"Received question: {request.question}")

    # Simulación
    respuesta_generada = "Esta es una respuesta generada por el LLM basada en los documentos."
    fuentes = [
        {"page": 5, "text": "Python es un lenguaje de programación interpretado..."},
        {"page": 12, "text": "Las listas son una de las estructuras de datos más versátiles..."}
    ]

    return {
        "answer": respuesta_generada,
        "sources": fuentes
    }