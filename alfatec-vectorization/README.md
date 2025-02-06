## 🐳 2. Configuración de **Alfatec Vectorization**

📌 Este módulo usa **Docker** y  **Docker Compose** . Se encarga de:

1. **Vectorizar los emails** diariamente a las **5 AM** dentro del contenedor.
2. **Ejecutar un servicio Streamlit** para visualizar y buscar emails.
3. **Ejecutar una API FastAPI** para realizar consultas en la base de datos vectorial.

### 📂 Estructura del directorio:

```bash
alfatec/
│── alfatec-vectorization/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   ├── env/  # (Se crea dentro del contenedor con venv)
│   ├── faiss_index/  # (Se almacena la base de datos FAISS)
│   ├── scripts/
│   │   ├── vectorization.py  # (Proceso de vectorización)
│   │   ├── api.py  # (API para consultas en FAISS)
│   ├── streamlit_app/
│   │   ├── streamlit_dashboard.py  # (Interfaz de búsqueda en Streamlit)
│   ├── .gitignore
```

### 🔹 2.1 Configurar y construir el **Docker**

Antes de construir Docker, es necesario configurar el entorno virtual y las dependencias.

```bash
cd alfatec-vectorization
python -m venv env  # Crear entorno virtual
source env/bin/activate  # Activar entorno virtual (en Windows usar 'env\\Scripts\\activate')
poetry install  # Instalar dependencias
```

Luego, construimos y levantamos los contenedores:

```bash
docker-compose up --build -d
```

💡 Esto:

* Construye la imagen del contenedor.
* Arranca ambos servicios en  **modo detach (-d)** .
* Expone el servicio **Streamlit** en el puerto  **8505** .
* Expone la **API FastAPI** en el puerto  **8506** .

### 🔹 2.2 Acceder a los servicios

#### 📊 **Dashboard Streamlit**

Para visualizar la interfaz de búsqueda, abre en tu navegador:

```bash
http://localhost:8505
```

Desde aquí puedes:

* Realizar **búsquedas semánticas** en los emails vectorizados.
* Ver los **correos más recientes** ordenados por fecha.
* Obtener información detallada de los emails.

#### 🔍 **API FastAPI**

Para realizar consultas programáticas a la base de datos vectorial, accede a la documentación interactiva en:

```
http://localhost:8506/docs
```

✅ **Endpoint disponible**:

* `<span>/query</span>` - Permite realizar búsquedas en la base de datos FAISS.
  * Parámetros esperados:
    ```
    {
      "query": "texto a buscar",
      "k": 10
    }
    ```
  * `<span>query</span>`: Texto a buscar.
  * `<span>k</span>`: Número de resultados más relevantes a devolver (opcional, por defecto `<span>10</span>`).
  * Devuelve los resultados más relevantes en base a similitud.

Ejemplo de consulta usando `<span>curl</span>`:

```
curl -X 'POST' \
  'http://localhost:8506/query' \
  -H 'Content-Type: application/json' \
  -d '{"query": "Ejemplo de búsqueda", "k": 5}'
```

✅ **Formato de respuesta**:

```
{
  "results": [
    {
      "score": 0.89,
      "metadata": {
        "email_id": "123",
        "subject": "Ejemplo de asunto",
        "date": "2024-01-01"
      }
    }
  ]
}
```

### 🔹 2.3 Configurar **Crontab** dentro del contenedor

La vectorización se ejecuta diariamente a las **5 AM** dentro del  **Docker** . Se define en el **Dockerfile** y usa el entorno virtual del proyecto:

```dockerfile
# Agregar crontab dentro del contenedor
RUN echo "0 5 * * * root /app/env/bin/python /app/scripts/vectorization.py" > /etc/cron.d/vectorization_cron \
    && chmod 0644 /etc/cron.d/vectorization_cron \
    && crontab /etc/cron.d/vectorization_cron
```

### 🔹 2.4 Reiniciar los contenedores

Si necesitas reiniciar todo el sistema:

```bash
docker-compose down
docker-compose up -d
```

Si solo quieres reiniciar la API:

```bash
docker-compose restart vectorization_api
```

### 🔹 2.5 Ver logs de los servicios

Para revisar si el **dashboard Streamlit** está corriendo correctamente:

```bash
docker logs vectorization_service
```

Para revisar si la **API FastAPI** está corriendo correctamente:

```bash
docker logs vectorization_api
```

Si hay errores, revisa el estado de los contenedores:

```bash
docker ps
```

---

## 🔄 3. Actualización de Dependencias

Si necesitas actualizar dependencias en  **Alfatec Vectorization** :

```bash
cd alfatec-vectorization
source env/bin/activate
poetry update
```

Si es necesario reconstruir los contenedores tras una actualización:

```bash
docker-compose build
docker-compose up -d
```

---

## 🛑 4. Detener los Servicios

Si deseas detener todo:

```bash
docker-compose down
```

Si solo quieres detener  **Streamlit** :

```bash
docker stop vectorization_service
```

Si solo quieres detener la  **API FastAPI** :

```bash
docker stop vectorization_api
```
