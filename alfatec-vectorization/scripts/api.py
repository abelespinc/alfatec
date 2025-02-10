import os
import shutil
import ast
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from utils.chat_utils import SemanticQueryEngine

# Configuración de Azure OpenAI
os.environ['AZURE_OPENAI_API_KEY'] = "8AAvuF9tB7LKLH59KdteT82TkBNUWCbTQJJvpgeeY03UiBVnDcz4JQQJ99ALACYeBjFXJ3w3AAABACOGVEun"
os.environ['AZURE_OPENAI_ENDPOINT'] = "https://aijustice.openai.azure.com/"
os.environ['AZURE_OPENAI_API_VERSION'] = "2023-05-15"

embedding_model = AzureOpenAIEmbeddings(model="text-embedding-3-large")
FAISS_INDEX_PATH = "/app/faiss_index"

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    k: int = 10  # Número de resultados a devolver (por defecto 10)

# Prompt para reformular consultas con LLM
REDIFINE_USER_INPUT_PROMPT = """
Te ha llegado una consulta sobre información guardada en una base de datos, y debes reformularla siguiendo las siguientes instrucciones:
- Reformula la pregunta extrayendo únicamente palabras clave, de forma que sea adecuada para una búsqueda vectorial.
- Focaliza la reformulación en la temática del contenido del correo.
- No focalices la reformulación en filtros de fechas, remitente, destinatario o archivos adjuntos.
- Si en la consulta se mencionan varios asuntos o temas, responde con una lista de los asuntos separados por comas en una lista de Python.

Nota: Responde únicamente con la lista de Python.

La consulta: {{$user_input}}
Contesta únicamente con la consulta reformulada en una nueva línea.
Tu respuesta:
"""

# Inicializar motor de reformulación de consultas
user_input_refiner = SemanticQueryEngine(
    model_name="gpt-4o",
    context=REDIFINE_USER_INPUT_PROMPT,
    history_limit=1,
    chat_history=[]  # No necesita historial compartido
)

def filter_llm_output(llm_output: str) -> str:
    """
    Limpia la salida del LLM eliminando caracteres innecesarios.

    Args:
        llm_output (str): La salida cruda del modelo LLM.

    Returns:
        str: La salida limpia y filtrada.
    """
    if not isinstance(llm_output, str):
        raise ValueError("Expected a string as input")

    unwanted_substrings = ["```python", "```", "python", "<br>"]

    for substring in unwanted_substrings:
        llm_output = llm_output.replace(substring, "")

    return llm_output.strip()

@app.post("/query")
async def query_vector_db(request: QueryRequest):
    """Endpoint para realizar búsquedas en la BD vectorial con reformulación de consulta."""
    
    if not os.path.exists(FAISS_INDEX_PATH):
        raise HTTPException(status_code=404, detail="FAISS index not found")

    # Reformular la consulta con el modelo LLM
    try:
        llm_response = await user_input_refiner.request_with_rate_limit(request.query)
        cleaned_query = filter_llm_output(llm_response)
        reformulated_queries = ast.literal_eval(cleaned_query)  # Convertir la salida en lista de Python
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reformulando la consulta: {str(e)}")
    
    # Cargar FAISS
    faiss_index = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)

    # Ejecutar la búsqueda con cada consulta reformulada y combinar resultados
    all_results = []
    for query in reformulated_queries:
        results = faiss_index.similarity_search_with_score(query, k=request.k)
        all_results.extend(results)

    # Eliminar duplicados y ordenar por score
    unique_results = {doc.metadata["eml_id"]: (score, doc.metadata) for doc, score in all_results}
    sorted_results = sorted(unique_results.values(), key=lambda x: x[0], reverse=True)

    response = [{"score": float(score), "metadata": metadata} for score, metadata in sorted_results]

    return {"results": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8506)
