# GenAI Engineer Take-Home Assignment: Python RAG Microservice with Langufuse Observability

---

## Objective

Design and implement a Python-based Retrieval-Augmented Generation (RAG) microservice that ingests provided documents, answers queries using an LLM, and includes full observability via Langufuse.

---

## Provided Material

**Documents:**

- [Think Python](https://allendowney.github.io/ThinkPython/index.html)
- [PEP 8](https://peps.python.org/pep-0008/)

---

## Requirements

### 1. Indexing

- load the documents and split them into logical chunks.  
- Generate embeddings for each chunk.  
- Store embeddings in a vector index of your choice.

### 2. API Endpoints (FastAPI)

- `GET /health` → returns 200 OK.  
- `POST /ingest` → triggers the ingestion:

  ```json
  {
    "content": "<document content or URL>",
    "document_type": "<pdf | text | html | markdown>"
  }
  ```

  and returns:

  ```json
  {
    "status": "success|error",
    "message": "<status message>",
    "chunks_created": <number>
  }
  ```

- `POST /query` → accepts:

  ```json
  { "question": "<text>" }
  ```

  and returns:

  ```json
  {
    "answer": "<generated answer>",
    "sources": [
      { "page": <number>, "text": "<passage text>" },
      …
    ]
  }
  ```

### 3. LLM Integration with langrapgh/langchain

- Use a configurable LLM for answer synthesis (e.g. OpenAI API).  
- Store configuration (API keys, endpoints) in environment variables.

### 4. Langufuse, Langsmith, etc. Observability

- Instrument spans for these operations:  
  - Document ingestion and chunking  
  - Embedding computation  
  - Similarity search  
  - LLM inference calls  
- Emit structured logs for incoming requests, errors, and significant events.  
- Record and expose metrics (e.g. request counts, latency histograms, error rates).

---

## Deliverables

Provide a public GitHub repository containing:

- **Service Code:** Python implementation with type hints and modular structure.  
- **Git History:** Commits showing incremental development.  
- **Dockerfile:** Builds the microservice image.  
- **docker-compose.yml:** Orchestrates the API, vector-store service(s), and any additional services you deem necessary.  
- **README.md:** Instructions for building, running, and testing, including:
  - Required environment variables, etc  
- **Extra credit:** Unit tests for ingestion and query logic.

---

## Important Notes

**Human Review Process:** This assignment will be evaluated by human reviewers, not automated systems. **Failing to meet the exact endpoint schemas will NOT result in automatic failures.** You are permitted to make thoughtful modifications to the API design if you believe they improve the overall solution.

**Justification is Key:** If you deviate from the provided schemas or requirements, simply explain:
- Why you made the change
- How your approach is better or more appropriate
- What trade-offs or benefits your design provides

**Focus on Excellence:** The spirit of this test is to see how you tackle the RAG problem and create the best possible solution. We value:
- Thoughtful architectural decisions
- Well-reasoned trade-offs
- Creative solutions to technical challenges
- Clear communication of your design choices

Don't be afraid to innovate or improve upon the base requirements if you can justify your decisions.

---

## Evaluation Criteria

- **Functionality:** Answers are accurate, context-grounded, and sources are correctly returned.  
- **Code Quality:** Readability, modular design, error handling, and use of type hints.  
- **Observability:** Comprehensive Langufuse spans, structured logging, and meaningful metrics.  
- **Deployment:** Docker and Compose setup runs successfully with a single command.  
- **Documentation:** Clear and complete README enabling immediate evaluation.

---

## Timeline & Submission

- **Timeframe:** 2 days  
- **Submission:** Public GitHub repository link with all required materials.
