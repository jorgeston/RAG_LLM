import pytest
from fastapi.testclient import TestClient
from app.main import app  # Importamos nuestra instancia de la app FastAPI

# Creamos un cliente de prueba que nos permite hacer llamadas a nuestra API
client = TestClient(app)

def test_health_check():
    """
    Prueba que el endpoint /health funciona y devuelve un estado 200 OK.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_query_endpoint_with_mock(mocker):
    """
    Prueba el endpoint /query usando un 'mock' para simular la respuesta del pipeline RAG.
    Esto nos permite probar la lógica de la API de forma rápida y aislada.
    """
    # 1. Definimos el resultado falso que queremos que nuestra función RAG devuelva
    mock_rag_result = {
        "result": "Esta es una respuesta simulada por el test.",
        "source_documents": [
            # Creamos un objeto 'mock' que se comporta como un documento de LangChain
            mocker.Mock(
                page_content="Texto de la fuente simulada.",
                metadata={"page": 1}
            )
        ]
    }

    # 2. Le decimos a pytest que reemplace la función real con nuestro resultado falso.
    # El string 'app.main.ejecutar_pipeline_rag_instrumentado' es la ruta a la función que queremos "engañar".
    mocker.patch(
        'app.main.ejecutar_pipeline_rag_instrumentado',
        return_value=mock_rag_result
    )

    # 3. Hacemos la llamada a la API
    user_question = {"question": "¿Funciona el mock?"}
    response = client.post("/query", json=user_question)

    # 4. Verificamos que la respuesta de la API es la que esperamos
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["answer"] == "Esta es una respuesta simulada por el test."
    assert len(response_data["sources"]) == 1
    assert response_data["sources"][0]["text"] == "Texto de la fuente simulada."
    assert response_data["sources"][0]["page"] == 1