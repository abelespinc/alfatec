import asyncio

if "progress_messages" not in globals():
    progress_messages = []

async def send_progress_message(message):
    """Agrega un mensaje de progreso y lo mantiene en la lista durante unos segundos."""
    global progress_messages
    progress_messages.append(message)
    await asyncio.sleep(5)  # Mantiene el mensaje más tiempo para que el frontend lo reciba
