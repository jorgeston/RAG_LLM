# RAG Microservice with Langfuse Observability

## 📜 Project Objective

This project is a Python-based **Retrieval-Augmented Generation (RAG)** microservice designed to ingest documents, answer queries based on their content, and provide deep observability into the entire process using Langfuse.

The solution is built on a modern, containerized, and fully open-source stack, enabling a 100% local and private RAG pipeline from document ingestion to answer generation.

---

## 🛠️ Tech Stack & Key Concepts

| Component          | Technology                                         | Purpose                                                                 |
| :------------------ | :------------------------------------------------- | :---------------------------------------------------------------------- |
| **API Framework** | FastAPI                                            | For building a high-performance, asynchronous, and robust web service.      |
| **LLM Serving** | Ollama with `gemma:2b`                             | To serve an open-source Large Language Model locally.                   |
| **Embeddings** | `all-MiniLM-L6-v2` (via Hugging Face)              | To generate powerful text embeddings locally, ensuring privacy and zero cost. |
| **Vector Database** | ChromaDB                                           | As an in-memory vector store for fast prototyping and development.      |
| **AI Orchestration** | LangChain                                          | To structure the RAG pipeline (load, split, retrieve, generate).          |
| **Observability** | Langfuse                                           | For deep, nested tracing and debugging of the RAG pipeline's logic.     |
| **Containerization** | Docker & Docker Compose                            | To package and deploy the entire multi-service application with a single command. |

---

## 🚀 Getting Started

Follow these steps to set up and run the entire environment on your local machine.

### 1. Prerequisites

* **Git** installed.
* **Docker** and **Docker Compose** installed and running.

### 2. Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/jorgeston/RAG_LLM.git
    cd RAG_LLM
    ```

2.  **Create the environment file:**
    This project requires API keys to connect to the Langfuse dashboard. Create a file named `.env` in the project root. You can copy the provided template:
    ```bash
    cp .env.template .env
    ```
    Next, edit the `.env` file and add your keys obtained from [Langfuse Cloud](https://cloud.langfuse.com/).

    *(You will need to create a `.env.template` file with the content below for this step to work).*

    **.env.template:**
    ```env
    # Langfuse Credentials
    # Get these from your project settings in Langfuse Cloud
    LANGFUSE_PUBLIC_KEY="pk-lf-..."
    LANGFUSE_SECRET_KEY="sk-lf-..."
    LANGFUSE_HOST="[https://cloud.langfuse.com](https://cloud.langfuse.com)"
    ```

### 3. Execution

1.  **Launch all services with Docker Compose:**
    This single command will build the API's Docker image, pull the Ollama image, and start both containers in a connected network.
    ```bash
    docker-compose up --build
    ```

2.  **Download the LLM (One-Time Step):**
    The first time you run the service, Ollama needs to download the `gemma:2b` model. Open a **new terminal window** and run the following command:
    ```bash
    docker-compose exec ollama ollama run gemma:2b
    ```
    Wait for the download to complete. Once finished, the model is stored in a persistent Docker volume and will not need to be downloaded again.

The service is now running and accessible at `http://localhost:8000`.

---

## 🔌 API Endpoints

You can interact with the API via the auto-generated interactive documentation at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

### `GET /health`
Checks the service's health status.
* **Success Response (200 OK):**
    ```json
    { "status": "ok" }
    ```

### `POST /ingest`
Ingests and processes a document. Uses `multipart/form-data` to handle file uploads.
* **Parameters:**
    * `file`: The document to be processed (PDF, TXT, HTML, etc.).
    * `document_type`: A string identifying the file type (e.g., `pdf`).
* **`curl` Example:**
    ```bash
    curl -X POST -F "file=@/path/to/your/document.pdf" -F "document_type=pdf" http://localhost:8000/ingest
    ```
* **Success Response (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Successfully ingested and processed document.pdf",
      "chunks_created": 123
    }
    ```

### `POST /query`
Sends a query to the RAG system based on the last ingested document.
* **Request Body:**
    ```json
    { "question": "Your question here" }
    ```
* **`curl` Example:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"question": "What is the maximum line length in Python?"}' http://localhost:8000/query
    ```
* **Success Response (200 OK):**
    ```json
    {
      "answer": "The generated answer from the LLM.",
      "sources": [
        { "page": 0, "text": "A relevant snippet from the source document..." }
      ]
    }
    ```

---

## 🧪 Testing

This project includes a suite of unit tests to ensure the API layer is functioning correctly. The tests use `pytest` and `pytest-mock` to test endpoint logic in isolation.

To run the tests, follow these steps on your local machine (outside of Docker):

1.  **Create and activate a local virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run pytest:**
    From the root directory of the project, simply run:
    ```bash
    pytest
    ```
    All tests should pass, confirming the API endpoints are correctly set up.

---

## 🧠 Architectural Decisions & Trade-offs

* **Local-First & Open-Source Stack:** The decision was made to use a fully local stack (Ollama, Hugging Face Embeddings) instead of relying on paid, proprietary APIs. This approach prioritizes **data privacy** (documents never leave the local environment), **zero cost**, and **full control** over every component. The trade-off is that inference performance is dependent on local hardware.

* **Improved `/ingest` Endpoint:** The ingestion endpoint was intentionally designed to accept `multipart/form-data` (file uploads) rather than a JSON payload containing the document's content. While a deviation from the initial schema, this is a **significant practical improvement**, as it is more efficient and robust for handling documents of any size and format, avoiding issues with JSON payload size limits.

* **Deep vs. Shallow Observability:** Instead of merely tracing the top-level API endpoints, a **granular instrumentation** of the RAG pipeline was implemented using Langfuse's context managers. This creates nested spans for the `retrieval` and `synthesis-generation` steps, providing deep visibility that is crucial for debugging RAG quality issues, such as hallucinations or irrelevant context.

* **Robust Container Environment:** The `Dockerfile` includes the installation of system-level dependencies (`libgl1`, `poppler`, `tesseract-ocr`). This makes the ingestion process more resilient by enabling the `unstructured` library to correctly process complex file formats like PDFs and scanned documents, preventing common runtime errors inside a minimal container environment.

---

## 🔮 Future Improvements

* **Persistent Vector Store:** Configure ChromaDB to persist its data to a Docker volume, allowing the knowledge base to survive container restarts.
* **Multi-Document Management:** Evolve the API to handle a persistent library of multiple documents, likely by associating chunks with a unique `document_id`.
* **Asynchronous Tracing:** For very high-throughput scenarios, the Langfuse exporting process could be made fully asynchronous to avoid any potential blocking on the main application thread. 