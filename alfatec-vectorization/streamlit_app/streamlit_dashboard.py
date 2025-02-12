import os
import streamlit as st
from dateutil import parser
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from datetime import datetime

# Configuraci  n de variables de entorno para Azure OpenAI
os.environ['AZURE_OPENAI_API_KEY'] = "8AAvuF9tB7LKLH59KdteT82TkBNUWCbTQJJvpgeeY03UiBVnDcz4JQQJ99ALACYeBjFXJ3w3AAABACOGVEun"
os.environ['AZURE_OPENAI_ENDPOINT'] = "https://aijustice.openai.azure.com/"
os.environ['AZURE_OPENAI_API_VERSION'] = "2023-05-151"

# Configuraci  n de embeddings
embedding_model = AzureOpenAIEmbeddings(model="text-embedding-3-large")

# Ruta del   ndice FAISS
FAISS_INDEX_PATH = "/app/faiss_index"

st.title(" ^=^s^j Emails Vectorizados - B  squeda Sem  ntica")

if os.path.exists(FAISS_INDEX_PATH):
    st.success(" ^|^e  ^mndice FAISS cargado correctamente")

    # Cargar FAISS
    faiss_index = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)

    # Ordenar por fecha
    all_docs = faiss_index.docstore._dict.values()



    # Diccionarios para traducir d  as y meses de espa  ol a ingl  s
    dias_es = {
        "lunes": "Monday", "martes": "Tuesday", "mi  rcoles": "Wednesday", "jueves": "Thursday",
        "viernes": "Friday", "s  bado": "Saturday", "domingo": "Sunday"
    }
    meses_es = {
        "enero": "January", "febrero": "February", "marzo": "March", "abril": "April",
        "mayo": "May", "junio": "June", "julio": "July", "agosto": "August",
        "septiembre": "September", "octubre": "October", "noviembre": "November", "diciembre": "December"
    }
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")  # Formato ISO
        except ValueError:
            pass
        # Reemplazar d  as y meses en espa  ol con ingl  s
        for es, en in dias_es.items():
            date_str = date_str.replace(es, en)
        for es, en in meses_es.items():
            date_str = date_str.replace(es, en)

        # Reemplazar "p. m." y "a. m." con "PM" y "AM"
        date_str = date_str.replace("p. m.", "PM").replace("a. m.", "AM")

        try:
            # Intentar parsear en ingl  s
            return parser.parse(date_str)
        except Exception as e:
            #st.warning(f" ^z   ^o No se pudo procesar la fecha: {date_str}. Error: {e}")
            return datetime.min  # Usar una fecha muy antigua como fallback
    sorted_docs = sorted(all_docs, key=lambda d: parse_date(d.metadata["date"]), reverse=True)

    # Mostrar los 300 m  s recientes
    st.subheader(" ^=^s   ^zltimos 300 correos:")
    for i, doc in enumerate(sorted_docs[:300]):
        st.write(f"**📌 Asunto:** {doc.metadata['subject']}")
        st.write(f"** ^=^s^e Fecha:** {doc.metadata['date']} - ** ^=^s  Asunto:** {doc.metadata['subject']}")
        st.write(f" ^=^s  **Remitente:** {doc.metadata['sender']}")
        st.write(f" ^=^s  **Destinatarios:** {doc.metadata['recipients']}")
        # Expander para mostrar el contenido completo del correo
        with st.expander(f"📜 Ver contenido del email ({len(doc.page_content)} caracteres)"):
            st.write(doc.page_content)  # Muestra el cuerpo completo
        st.write("---")

    #query = st.text_input(" ^=^t^m Ingrese su b  squeda:")
    #if query:
    #    results = faiss_index.similarity_search_with_score(query, k=5)
    #    st.subheader(" ^=^t^n Resultados:")
    #    for i, (doc, score) in enumerate(results):
    #        st.write(f"### Resultado {i+1} (Score: {score:.2f})")
    #        st.write(f" ^=^s  **Asunto:** {doc.metadata['subject']}")
    #        st.write(f" ^=^s^| **Contenido:** {doc.page_content[:500]}...")
    #        st.write("---")
else:
    st.warning(" ^z   ^o  ^mndice FAISS no encontrado.")