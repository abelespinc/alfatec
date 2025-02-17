import os
import regex as re
import json
import time
from typing import List, Dict
from dotenv import load_dotenv
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from utils.chat_utils import SemanticQueryEngine
from response_creator.prompts import SUMMARIZE_EMAILS_PROMPT

class ResponseCreator:
    MAX_EMAILS = 100  # Límite máximo de correos procesados
    MAX_CARACT = 4000 # Límite máximo de caracteres del body

    def __init__(self, filtered_emails: List[Dict], query: str):
        """
        Inicializa la clase con los correos filtrados y la consulta inicial del usuario.
        
        :param filtered_emails: Lista de correos relevantes obtenidos de la búsqueda.
        :param query: Consulta inicial del usuario.
        """
        try:

            self.filtered_emails = filtered_emails[:self.MAX_EMAILS]  # Limitar los correos procesados
        
            # Truncar el campo "body" de cada correo al máximo de caracteres permitidos
            for email in self.filtered_emails:
                if "body" in email and isinstance(email["body"], str):
                    email["body"] = email["body"][:self.MAX_CARACT]  # Recortar a 4000 caracteres
                
            self.query = query

            # Inicializar funciones semánticas con prompts predefinidos
            self.summarize_function = SemanticQueryEngine(
                model_name="gpt-4o",
                context=SUMMARIZE_EMAILS_PROMPT,
                history_limit=1,
                chat_history=[]  # No necesita historial compartido
            )

        except AttributeError as e:
            print(f"[ERROR] AttributeError en ResponseCreator: {e}")
        except Exception as e:
            print(f"[ERROR] Excepción en ResponseCreator: {e}")


    async def summarize_emails(self) -> str:
        """
        Genera un resumen de los correos filtrados.

        :return: Resumen en formato de texto.
        """
        try:
            start_time = time.time()  # ⏳ Inicio del resumen

            email_text = json.dumps(self.filtered_emails, ensure_ascii=False)
            prompt_input = f"Consulta: {self.query}\nCorreos: {email_text}"
            response = await self.summarize_function.request_with_rate_limit(prompt_input)
            print("Response inicial:", response)

            # Limpieza inicial básica
            response = response.replace("```html", "").replace("```", "").strip()

            # Eliminar espacios innecesarios y <br> redundantes entre texto y tablas
            response = re.sub(r"(<br>\s*){2,}(?=<table)", r"<br>", response)  # Antes de una tabla
            response = re.sub(r"(<\/thead>|<\/tr>|<\/table>)\s*<br>", r"\1", response)
            response = re.sub(r"<br>\s*(<tr>|<\/tr>|<th>|<\/th>|<td>|<\/td>)", r"\1", response)

            print("Response final:", response)

            end_time = time.time()  # ⏳ Fin del resumen
            print(f"[RESPONSE CREATOR] Tiempo en generar resumen de emails: {end_time - start_time:.2f} segundos")

            return response

        except Exception as e:
            print(f"Error al generar resumen: {e}")
            return "No se pudo generar el resumen."
