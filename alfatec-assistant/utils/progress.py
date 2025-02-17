import asyncio

if "progress_messages" not in globals():
    progress_messages = []

async def send_progress_message(message):
    """Agrega un mensaje de progreso y lo elimina automáticamente cuando la consulta termine."""
    global progress_messages
    progress_messages.append(message)
    
    # 🔥 Permitir que el frontend reciba el mensaje de estado rápidamente
    await asyncio.sleep(0.1)  # Solo medio segundo para asegurar la actualización del frontend

async def clear_progress_messages():
    """Elimina los mensajes de progreso para ocultar el spinner en el frontend."""
    global progress_messages
    progress_messages.clear()
