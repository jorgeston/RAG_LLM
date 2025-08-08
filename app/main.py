import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Literal
from dotenv import load_dotenv

# --- LANGCHAIN & AI IMPORTS ---
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader
from langchain.prompts import PromptTemplate

# --- LANGFUSE IMPORTS (v3) ---
# Importaciones correctas basadas en la investigación del SDK v3
from langfuse import Langfuse, get_client
from langfuse import observe

# --- CONFIGURACIÓN INICIAL ---

# Cargar variables de entorno desde el archivo .env
# Asegúrate de tener LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, etc.
load_dotenv()

# Inicializa el cliente global de Langfuse.
# Cargará las credenciales desde las variables de entorno.
langfuse = Langfuse()

# --- MODELOS PYDANTIC (API Schemas) ---

class IngestResponse(BaseModel):
    status: Literal['success', 'error']
    message: str
    chunks_created: int

class QueryRequest(BaseModel):
    question: str

class Source(BaseModel):
    page: int
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

# --- CONFIGURACIÓN DEL MOTOR RAG ---
# Estos objetos se inicializan una vez al arrancar el servidor.

# 1. Modelo de Embeddings (Local y Gratuito)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Base de Datos Vectorial (Inicialmente vacía y en memoria)
vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="document_collection"
)

# 3. Modelo de Lenguaje (Local y Gratuito vía Ollama)
llm = ChatOllama(model="gemma:2b")

# 4. Plantilla de Prompt (Para dar instrucciones claras al LLM)
prompt_template = """Usa las siguientes piezas de contexto para responder la pregunta al final.
Si no sabes la respuesta o el contexto no es suficiente, simplemente di que no puedes responder con la información proporcionada, no intentes inventar una respuesta.
Proporciona una respuesta concisa y directa.

Contexto: {context}

Pregunta: {question}

Respuesta útil:"""
PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# 5. Cadena de Recuperación y Respuesta (Inicialmente con el vectorstore vacío)
qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

# --- APLICACIÓN FASTAPI ---

app = FastAPI(
    title="GenAI RAG Microservice",
    description="Un microservicio RAG con FastAPI, Ollama y observabilidad Langfuse.",
    version="1.0.0",
)

# --- LÓGICA DE RAG INSTRUMENTADA CON LANGFUSE ---

def ejecutar_pipeline_rag_instrumentado(query: str):
    """
    Ejecuta el pipeline RAG completo con instrumentación detallada usando gestores de contexto.
    Adaptado de la Sección 2.3 del documento de investigación sobre Langfuse v3.
    """
    lf_client = get_client()

    # Span Padre para todo el pipeline.
    with lf_client.start_as_current_span(name="rag-pipeline", input={"query": query}) as pipeline_span:
        
        # Span anidado para el paso de Recuperación (Retrieval).
        with lf_client.start_as_current_span(name="retrieval") as retrieval_span:
            retriever = vectorstore.as_retriever()
            documentos_recuperados = retriever.get_relevant_documents(query)
            
            # CRÍTICO: Registrar los documentos recuperados como la salida de este span.
            retrieval_span.update(
                output={"retrieved_docs": [doc.page_content for doc in documentos_recuperados]}
            )
        
        # Formatear el contexto para el prompt del LLM.
        contexto_formateado = "\n".join(f"- {doc.page_content}" for doc in documentos_recuperados)
        prompt_completo = PROMPT.format(context=contexto_formateado, question=query)

        # Generación anidada para la llamada al LLM.
        with lf_client.start_as_current_generation(
            name="synthesis-generation",
            model=llm.model,
            input=prompt_completo,
            model_parameters={"temperature": 0}
        ) as generation:
            # Usamos nuestra cadena QA para obtener la respuesta
            result = qa_chain({"query": query})
            respuesta_llm = result.get("result", "No se encontró una respuesta.")
            
            generation.update(output=respuesta_llm)
            pipeline_span.update(output={"final_answer": respuesta_llm})
            
            return result

# --- ENDPOINTS DE LA API ---

@app.get("/health")
def health_check():
    """Verifica que el servicio esté funcionando."""
    return {"status": "ok"}

@app.post("/ingest", response_model=IngestResponse)
@observe()
async def ingest_document(file: UploadFile = File(...), document_type: str = Form(...)):
    """Endpoint para ingerir, procesar y vectorizar un documento."""
    global vectorstore, qa_chain

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    temp_file_path = f"./temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        if vectorstore:
            vectorstore.delete_collection()

        if document_type == 'pdf':
            loader = PyPDFLoader(temp_file_path)
        else:
            loader = UnstructuredFileLoader(temp_file_path)
        
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vectorstore.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )

        return {
            "status": "success",
            "message": f"Successfully ingested and processed {file.filename}",
            "chunks_created": len(chunks)
        }
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/query", response_model=QueryResponse)
@observe()
def query_service(request: QueryRequest):
    """Endpoint que recibe una pregunta y ejecuta el pipeline RAG instrumentado."""
    try:
        result = ejecutar_pipeline_rag_instrumentado(request.question)
        
        answer = result.get("result", "No se encontró una respuesta.")
        source_documents = result.get("source_documents", [])
        
        sources = []
        for doc in source_documents:
            page_num = doc.metadata.get('page', 0)
            sources.append(Source(page=page_num, text=doc.page_content))

        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))