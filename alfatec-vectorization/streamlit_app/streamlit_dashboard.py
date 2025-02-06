import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from datetime import datetime

# Configuración de variables de entorno para Azure OpenAI
os.environ['AZURE_OPENAI_API_KEY'] = "8AAvuF9tB7LKLH59KdteT82TkBNUWCbTQJJvpgeeY03UiBVnDcz4JQQJ99ALACYeBjFXJ3w3AAABACOGVEun"
os.environ['AZURE_OPENAI_ENDPOINT'] = "https://aijustice.openai.azure.com/"
os.environ['AZURE_OPENAI_API_VERSION'] = "2023-05-151"

# Configuración de embeddings
embedding_model = AzureOpenAIEmbeddings(model="text-embedding-3-large")

# Ruta del índice FAISS
FAISS_INDEX_PATH = "/app/faiss_index"

st.title("📊 Emails Vectorizados - Búsqueda Semántica")

if os.path.exists(FAISS_INDEX_PATH):
    st.success("✅ Índice FAISS cargado correctamente")

    # Cargar FAISS
    faiss_index = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)

    # Ordenar por fecha
    all_docs = faiss_index.docstore._dict.values()
    sorted_docs = sorted(all_docs, key=lambda d: datetime.strptime(d.metadata["date"], "%Y-%m-%d %H:%M:%S"), reverse=True)

    # Mostrar los 300 más recientes
    st.subheader("📬 Últimos 300 correos:")
    for i, doc in enumerate(sorted_docs[:300]):
        st.write(f"**📅 Fecha:** {doc.metadata['date']} - **📩 Asunto:** {doc.metadata['subject']}")
        st.write(f"📤 **Remitente:** {doc.metadata['sender']}")
        st.write(f"📥 **Destinatarios:** {doc.metadata['recipients']}")
        st.write("---")

    query = st.text_input("🔍 Ingrese su búsqueda:")
    if query:
        results = faiss_index.similarity_search_with_score(query, k=5)
        st.subheader("🔎 Resultados:")
        for i, (doc, score) in enumerate(results):
            st.write(f"### Resultado {i+1} (Score: {score:.2f})")
            st.write(f"📩 **Asunto:** {doc.metadata['subject']}")
            st.write(f"📜 **Contenido:** {doc.page_content[:500]}...")
            st.write("---")
else:
    st.warning("⚠️ Índice FAISS no encontrado.")
