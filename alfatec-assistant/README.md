# 📘 Alfatec Assistant

## 🛠️ 1. Descripción

Alfatec Assistant es un sistema de asistencia basado en inteligencia artificial diseñado para facilitar la búsqueda y análisis de correos electrónicos en una base de datos vectorial. Utiliza tecnologías avanzadas de NLP y machine learning para proporcionar respuestas precisas y eficientes a consultas sobre correos electrónicos.

## 🚀 2. Funcionalidades

✅ **Clasificación de consultas**: Distingue entre consultas conversacionales y búsquedas en la base de datos de correos.
✅ **Búsqueda Semántica de Correos**: Realiza búsquedas en la base de datos vectorial mediante un servicio de API.
✅ **Interfaz Conversacional**: Capacidad de respuesta dinámica basada en un historial de conversaciones.
✅ **Acceso a Correos mediante API**: Se conecta a la API del servicio de vectorización en el puerto `<span>8506</span>` para obtener los correos relevantes.

## 📂 3. Estructura del Proyecto

```
alfatec-assistant/
│── app.py  # (Archivo principal de la aplicación Quart)
│── Dockerfile  # (Configuración del contenedor)
│── docker-compose.yml  # (Orquestación de servicios)
│── pyproject.toml  # (Gestión de dependencias con Poetry)
│── response_creator/
│   ├── response_creator.py  # (Generación de respuestas)
│   ├── prompts.py  # (Prompts para el procesamiento de consultas)
│── search_engine/
│   ├── search_engine.py  # (Búsqueda en la base de datos vectorial vía API)
│   ├── prompts.py  # (Prompts para procesamiento de consultas de búsqueda)
│── utils/
│   ├── chat_kernel.py  # (Lógica principal de procesamiento de consultas)
│   ├── chat_utils.py  # (Funciones auxiliares de chat y conexión con modelos de IA)
│   ├── prompts.py  # (Prompts usados en el asistente)
│── .env  # (Variables de entorno)
│── README.md  # (Este documento)
```

## 🔹 4. Configuración y Despliegue

### 4.1 Configurar Dependencias

Antes de construir los contenedores, es necesario instalar las dependencias del proyecto:

```
cd alfatec-assistant
python -m venv env  # Crear entorno virtual
source env/bin/activate  # Activar entorno virtual (Windows: `env\Scripts\activate`)
poetry install  # Instalar dependencias
```

### 4.2 Construcción y Ejecución con Docker

Ejecuta el siguiente comando para construir y desplegar el sistema con Docker:

```
docker-compose up --build -d
```

📌 Esto:

* Construye las imágenes necesarias.
* Levanta los servicios en **modo detach (-d)**.
* Expone la aplicación en el puerto **8504**.

### 4.3 Acceso a la Aplicación

Para acceder al asistente en el navegador:

```
http://localhost:8504
```

### 4.4 Acceso a la API de búsqueda de correos

El asistente consulta los correos a través del servicio API en `<span>http://localhost:8506/query</span>`.
Ejemplo de consulta:

```
curl -X 'POST' \
  'http://localhost:8506/query' \
  -H 'Content-Type: application/json' \
  -d '{"query": "Ejemplo de búsqueda", "k": 10}'
```

📌 **Parámetros del endpoint **`<span><strong>/query</strong></span>`:

* `<span>query</span>`: Texto de búsqueda.
* `<span>k</span>`: Número de resultados a retornar (opcional, por defecto 100).

📌 **Formato de respuesta**:

```
{
  "results": [
    {
      "score": 0.89,
      "metadata": { "sender": "example@email.com", "subject": "Asunto del correo" }
    },
    ...
  ]
}
```

## 🔄 5. Mantenimiento y Logs

### 5.1 Reiniciar la Aplicación

Para reiniciar la aplicación sin detener otros servicios:

```
docker-compose restart app
```

Para ver los logs en tiempo real:

```
docker logs -f app
```

### 5.2 Actualizar Dependencias

Si necesitas actualizar las dependencias, ejecuta:

```
cd alfatec-assistant
source env/bin/activate
poetry update
```

Si es necesario reconstruir los contenedores tras una actualización:

```
docker-compose build
```

## 🛑 6. Detener Servicios

Para detener todos los servicios:

```
docker-compose down
```

Para detener solo la aplicación del asistente:
