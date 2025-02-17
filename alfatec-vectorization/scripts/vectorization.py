import os
import json
import time
import gc
import shutil
import logging
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from tqdm import tqdm
from openai import RateLimitError

# Configuración de logs
LOG_FILE = "/app/logs/vectorization.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuración de variables de entorno para Azure OpenAI
os.environ['AZURE_OPENAI_API_KEY'] = "8AAvuF9tB7LKLH59KdteT82TkBNUWCbTQJJvpgeeY03UiBVnDcz4JQQJ99ALACYeBjFXJ3w3AAABACOGVEun"
os.environ['AZURE_OPENAI_ENDPOINT'] = "https://aijustice.openai.azure.com/"
os.environ['AZURE_OPENAI_API_VERSION'] = "2023-05-151"

# Configuración de embeddings
embedding_model = AzureOpenAIEmbeddings(model="text-embedding-3-large")

# Rutas
PROCESSED_JSON_PATH = "/app/data_creation/processed_emails.json"
FAISS_INDEX_PATH = "/app/faiss_index"
TEMP_FAISS_INDEX_PATH = "/app/faiss_index_temp"

def load_emails():
    """Carga correos desde el JSON para vectorizar."""
    logging.info("📥 Cargando emails desde JSON...")
    with open(PROCESSED_JSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    texts, metadata_list = [], []
    for email in data["emails"]:
        texts.append(f"{email['subject']} {email['body'][:4000]}")
        metadata_list.append({
            "eml_id": email["eml_id"],
            "subject": email["subject"],
            "sender": email["sender"],
            "recipients": email["recipients"],
            "date": email["date"],
            "root_path": email["root_path"],
            "attachments": email["attachments"]
        })

    logging.info(f"✅ {len(texts)} emails cargados correctamente.")
    return texts, metadata_list

def iterate_in_blocks(lst, block_size):
    """Generador para procesar listas en bloques."""
    for i in range(0, len(lst), block_size):
        yield lst[i:i + block_size]

def vectorize_emails():
    """Vectoriza los emails y guarda en FAISS."""
    logging.info("🔄 Iniciando proceso de vectorización...")

    texts, metadata_list = load_emails()

    if not texts:
        logging.warning("⚠️ No se encontraron emails. Se cancela la vectorización.")
        return

    logging.info("📌 Creando índice FAISS temporal...")
    if os.path.exists(TEMP_FAISS_INDEX_PATH):
        shutil.rmtree(TEMP_FAISS_INDEX_PATH)

    block_size = 50
    total_blocks = (len(texts) + block_size - 1) // block_size
    
    faiss_index = None
    for i, (texts_block, metadata_block) in enumerate(tqdm(zip(iterate_in_blocks(texts, block_size), iterate_in_blocks(metadata_list, block_size)), total=total_blocks, desc="Vectorizando emails", unit="bloques")):
        while True:
            try:
                if i == 0:
                    faiss_index = FAISS.from_texts(texts_block, embedding_model, metadatas=metadata_block)  # ✅ Incluir metadatos
                else:
                    faiss_index.add_texts(texts_block, metadatas=metadata_block)
                break
            except RateLimitError:
                logging.warning("⚠️ Rate limit exceeded. Retrying in 30 minutes...")
                time.sleep(30 * 60)
    
    faiss_index.save_local(TEMP_FAISS_INDEX_PATH)
    logging.info("✅ Vectorización completada. Reemplazando índice antiguo...")

    if os.path.exists(FAISS_INDEX_PATH):
        shutil.rmtree(FAISS_INDEX_PATH)
    shutil.move(TEMP_FAISS_INDEX_PATH, FAISS_INDEX_PATH)

    logging.info("✅ Índice actualizado sin interrumpir el servicio.")
    gc.collect()

if __name__ == "__main__":
    vectorize_emails()
