import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Literal

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader, UnstructuredFileLoader
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Modelos Pydantic (sin cambios) ---
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


# --- Configuración Inicial del RAG ---
# Esta sección es clave. La ponemos fuera de los endpoints para que no se reinicie con cada request.

# 1. Inicializamos el modelo de Embeddings
# Usaremos el de OpenAI, que es potente y estándar en la industria.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Inicializamos la Base de Datos Vectorial (en memoria)
# ChromaDB es ideal para desarrollo rápido. `persist_directory` es opcional para guardar en disco.
vectorstore = Chroma(embedding_function=embeddings, collection_name="document_collection")

# 3. Inicializamos el LLM que usaremos para responder preguntas
llm = ChatOllama(model="gemma:2b")

# 4. Creamos un Prompt Template para dar mejores instrucciones
prompt_template = """Usa las siguientes piezas de contexto para responder la pregunta al final.
Si no sabes la respuesta o el contexto no es suficiente, simplemente di que no puedes responder con la información proporcionada, no intentes inventar una respuesta.
Proporciona una respuesta concisa y directa.

Contexto: {context}

Pregunta: {question}

Respuesta útil:"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# 5. Creamos la Cadena de Recuperación y Respuesta (Retrieval Chain)
# Esta cadena une el LLM con la base de datos vectorial.
# "stuff" es un método simple que "rellena" el prompt con el contexto recuperado.
qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True, # Importante para devolver las fuentes
    chain_type_kwargs={"prompt": PROMPT}
)


# --- Aplicación FastAPI ---
app = FastAPI(
    title="GenAI RAG Microservice",
    description="Un microservicio RAG con FastAPI.",
    version="0.2.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...), document_type: str = Form(...)):
    """
    Endpoint para ingerir y procesar un documento.
    Ahora acepta un archivo subido y gestiona el estado global.
    """
    # Declaramos que vamos a modificar estas variables globales
    global vectorstore, qa_chain

    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Guardar temporalmente el archivo para que el loader pueda leerlo
    temp_file_path = f"./temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        # Limpiar la colección anterior para evitar la contaminación de contexto
        if vectorstore:
            vectorstore.delete_collection()

        # Cargar el documento con el loader apropiado
        if document_type == 'pdf':
            loader = PyPDFLoader(temp_file_path)
        else: # Para text, html, md, etc.
            loader = UnstructuredFileLoader(temp_file_path)
        
        documents = loader.load()

        # Dividir el documento en chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        # Crear el nuevo vectorstore con los nuevos chunks
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        # -------- ¡IMPORTANTE! --------
        # Actualizar la cadena QA para que use el nuevo vectorstore
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vectorstore.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        # --------------------------------

        return {
            "status": "success",
            "message": f"Successfully ingested and processed {file.filename}",
            "chunks_created": len(chunks)
        }
    except Exception as e:
        # Esto nos dará un error más detallado en la terminal si algo falla
        print(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Limpiar el archivo temporal
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/query", response_model=QueryResponse)
def query_service(request: QueryRequest):
    """
    Endpoint para hacer una pregunta al sistema RAG.
    """
    try:
        # Usamos la cadena QA para obtener la respuesta
        result = qa_chain({"query": request.question})
        
        # Extraemos la respuesta y las fuentes
        answer = result.get("result", "No se encontró una respuesta.")
        source_documents = result.get("source_documents", [])
        
        # Formateamos las fuentes para la respuesta de la API
        sources = []
        for doc in source_documents:
            # La página puede no estar siempre disponible, depende del tipo de documento
            page_num = doc.metadata.get('page', 0) 
            sources.append(Source(page=page_num, text=doc.page_content))

        return QueryResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))