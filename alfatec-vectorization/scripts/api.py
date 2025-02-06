import os
import shutil
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings

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

@app.post("/query")
def query_vector_db(request: QueryRequest):
    """Endpoint para realizar búsquedas en la BD vectorial."""
    if not os.path.exists(FAISS_INDEX_PATH):
        raise HTTPException(status_code=404, detail="FAISS index not found")
    
    faiss_index = FAISS.load_local(FAISS_INDEX_PATH, embedding_model)
    results = faiss_index.similarity_search_with_score(request.query, k=request.k)
    
    response = [{
        "score": score,
        "metadata": doc.metadata
    } for doc, score in results]
    
    return {"results": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8506)
