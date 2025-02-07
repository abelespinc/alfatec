import re
import os
import json
from itertools import product
from rapidfuzz import fuzz
from rapidfuzz import process
from datetime import datetime
from typing import List, Dict, Union, Tuple
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from search_engine.prompts import DETECT_SENDER_PROMPT, DETECT_RECIPIENTS_PROMPT, DETECT_DATE_PROMPT, EXTRACT_SUBJECT_PROMPT, EXTRACT_THEMES_PROMPT, EXTRACT_KEYWORDS_PROMPT, DETECT_ATTACHMENTS_PROMPT, DETECT_ATTACHMENT_NAMES_PROMPT
from utils.chat_utils import SemanticQueryEngine, MaxRetriesExceededError

class SearchEngine:
    def __init__(self):
        """
        Constructor para inicializar el motor de búsqueda con los datos de los correos.
        """
        # Correos
        json_file_path = "data_creation/processed_emails.json"
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.email_data = data.get("emails", [])


        self.detect_sender_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=DETECT_SENDER_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        self.detect_recipients_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=DETECT_RECIPIENTS_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        current_date = datetime.now().strftime("%Y-%m-%d")
        detect_date_prompt_act = DETECT_DATE_PROMPT.replace("{{current_date}}", current_date)
        self.detect_date_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=detect_date_prompt_act,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        self.extract_subject_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=EXTRACT_SUBJECT_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )
    
        self.extract_themes_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=EXTRACT_THEMES_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        self.extract_keywords_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=EXTRACT_KEYWORDS_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        self.detect_attachments_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=DETECT_ATTACHMENTS_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        self.detect_attachment_names_function = SemanticQueryEngine(
            model_name="gpt-4o",
            context=DETECT_ATTACHMENT_NAMES_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

    async def detect_sender(self, query: str) -> List[str]:
        """
        Detecta remitentes mencionados en la query.
        :param query: La consulta del usuario.
        :return: Una lista de remitentes (correos electrónicos) detectados en la consulta.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.detect_sender_function.request_with_rate_limit(query)

            #Intentar cargar la respuesta como lista JSON
            return json.loads(response)

        except Exception as e:
            print(f"Error detectando remitentes: {e}")
            return []            
        
    async def detect_recipients(self, query: str) -> List[str]:
        """
        Detecta destinatarios mencionados en la query del usuario.
        :param query: Texto ingresado por el usuario.
        :return: Lista de destinatarios detectados en formato de correo electrónico.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.detect_recipients_function.request_with_rate_limit(query)

            # Intentar cargar la respuesta como lista JSON
            return json.loads(response)
        except Exception as e:
            print(f"Error detectando destinatarios: {e}")
            return []
    
    async def detect_date_range(self, query: str) -> Union[Dict[str, str], None]:
        """
        Detecta fechas o rangos de fechas mencionados en la consulta del usuario.
        :param query: Texto ingresado por el usuario.
        :return: Diccionario con la información de la fecha o rango, o None si no se encuentra.
        """
        try:
            # Ejecutar el modelo con la consulta y la fecha actual
            response = await self.detect_date_function.request_with_rate_limit(query)

            # Intentar cargar la respuesta como diccionario JSON
            return json.loads(response)
        except Exception as e:
            print(f"Error detectando fechas: {e}")
            return {"type": "none"}

    async def extract_subject(self, query: str) -> Union[str, None]:
        """
        Extrae el asunto mencionado en la consulta del usuario.
        :param query: Texto ingresado por el usuario.
        :return: El asunto detectado como string o None si no se encuentra.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.extract_subject_function.request_with_rate_limit(query)

            # Intentar interpretar la respuesta como JSON para mayor seguridad
            subject = json.loads(response)
            return subject
        except Exception as e:
            print(f"Error extrayendo asunto: {e}")
            return None

    async def extract_themes(self, query: str) -> List[str]:
        """
        Extrae temas específicos mencionados en la consulta del usuario.
        :param query: Texto ingresado por el usuario.
        :return: Lista de temas detectados.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.extract_themes_function.request_with_rate_limit(query)

            # Intentar interpretar la respuesta como JSON
            themes = json.loads(response)
            return themes
        except Exception as e:
            print(f"Error extrayendo temas: {e}")
            return []

    async def extract_keywords(self, query: str) -> List[str]:
        """
        Extrae palabras clave específicas mencionadas en la consulta del usuario.
        :param query: Texto ingresado por el usuario.
        :return: Lista de palabras clave detectadas.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.extract_keywords_function.request_with_rate_limit(query)

            # Intentar interpretar la respuesta como JSON
            keywords = json.loads(response)
            return keywords
        except Exception as e:
            print(f"Error extrayendo palabras clave: {e}")
            return []

    async def detect_attachments(self, query: str) -> bool:
        """
        Detecta si el usuario solicita correos con documentos adjuntos.
        :param query: Texto ingresado por el usuario.
        :return: true si el usuario menciona adjuntos, false en caso contrario.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.detect_attachments_function.request_with_rate_limit(query)

            return response
        except Exception as e:
            print(f"Error detectando documentos adjuntos: {e}")
            return False

    async def detect_attachment_names(self, query: str) -> List[str]:
        """
        Detecta nombres de archivos adjuntos mencionados en la consulta del usuario.
        :param query: Texto ingresado por el usuario.
        :return: Lista de nombres de archivos detectados.
        """
        try:
            # Ejecutar el modelo con la consulta
            response = await self.detect_attachment_names_function.request_with_rate_limit(query)

            # Intentar cargar la respuesta como lista JSON
            return json.loads(response)
        except Exception as e:
            print(f"Error detectando nombres de documentos adjuntos: {e}")
            return []

    def search_faiss(self, query: str, k: int = 10) -> List[Dict]:
        """
        Realiza una búsqueda semántica en FAISS con la consulta completa.
        """
        try:
            url = "http://127.0.0.1:8506/query"
            data = {"query": query, "k": k}
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                return json.loads(response.text).get("results", [])
            else:
                print(f"Error en la búsqueda FAISS: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error en la conexión con FAISS: {e}")
            return []

    async def search(self, query: str, k: int) -> List[Dict]:
        """
        Realiza una búsqueda avanzada en los correos basándose en criterios tanto estructurados como semánticos.
        Genera múltiples búsquedas para todas las combinaciones posibles de "recipients", "themes" y "attachment_names".
        :param query: Consulta del usuario.
        :return: Lista de correos relevantes que cumplen los criterios.
        """
        try:
            print("===============================================================")
            print(f'Consulta del usuario:\n {query}')
            print("===============================================================")
            print("===# INICIO DEL PROCESO DE EXTRACCIÓN DE CRITERIOS DE BÚSQUEDA #===")
            
            # 1. Buscar en FAISS directamente con el `query`
            faiss_results = self.search_faiss(query=query, k=k)
       
            # 2. Extraer criterios de búsqueda con mini-agentes
            senders = await self.detect_sender(query)
            recipients = await self.detect_recipients(query)
            date_range = await self.detect_date_range(query)
            subject = await self.extract_subject(query)
            themes = await self.extract_themes(query)
            keywords = await self.extract_keywords(query)
            has_attachments = await self.detect_attachments(query)
            attachment_names = await self.detect_attachment_names(query)

            print("\n🔍 Criterios extraídos:")
            print(json.dumps({
                "senders": senders, "recipients": recipients, "date_range": date_range,
                "themes": themes, "keywords": keywords,
                "has_attachments": has_attachments, "attachment_names": attachment_names
            }, indent=4, ensure_ascii=False))
            

            # 3. Generar combinaciones de criterios
            print("\n===# GENERANDO COMBINACIONES DE CRITERIOS #===")
            combinations = list(product(
                senders or [None],
                recipients or [None],  # Si no hay recipients, usar None
                themes or [None],      # Si no hay themes, usar None
                attachment_names or [None]  # Si no hay attachment_names, usar None
            ))

            print(f"Generadas {len(combinations)} combinaciones de criterios.")

            # 4. Realizar búsquedas para cada combinación
            all_filtered_emails = []
            for sender, recipient, theme, attachment_name in combinations:
                print("\n===# BÚSQUEDA PARA COMBINACIÓN ESPECÍFICA #===")
                print(f"Sender: {sender}, Recipient: {recipient}, Theme: {theme}, Attachment Name: {attachment_name}")
                
                # Crear un diccionario de filtros específicos para esta combinación
                current_filters = {
                    "senders": [sender] if sender else [],
                    "recipients": [recipient] if recipient else [],
                    "date_range": date_range,
                    "subject": subject,
                    "themes": [theme] if theme else [],
                    "keywords": keywords,
                    "has_attachments": has_attachments,
                    "attachment_names": [attachment_name] if attachment_name else []
                }

                # Filtrar emails usando los criterios actuales
                filtered_emails = self.filter_emails(faiss_results, current_filters)
                print(f"Emails encontrados: {len(filtered_emails)}")
                
                # Agregar resultados a la lista general
                all_filtered_emails.extend(filtered_emails)

            # 5. Eliminar duplicados (basado en combinación de campos únicos)
            unique_emails_set = set()
            unique_emails_list = []

            for email in all_filtered_emails:
                # Crear una clave compuesta única para identificar correos
                unique_key = (
                    email['eml_id'],
                    email["subject"],
                    email["sender"],
                    email["recipients"],
                    email["date"],
                    email["body"],
                )
                if unique_key not in unique_emails_set:
                    unique_emails_set.add(unique_key)
                    unique_emails_list.append(email)

            print(f"\n===# RESULTADO FINAL DE LA BÚSQUEDA #===")
            print(f"Total de emails únicos: {len(unique_emails_list)}")

            return unique_emails_list

        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []

    def filter_emails(self, emails: List[Dict], filters: Dict) -> List[Dict]:
        """
        Filtra emails basándose en criterios específicos.
        :param filters: Diccionario con los criterios de filtrado.
        :return: Lista de emails que cumplen los criterios.
        """
        filtered_emails = emails

        # Filtrar por adjuntos
        if filters["has_attachments"] == "true":
            filtered_emails = [email for email in filtered_emails if email.get("attachments", [])]
        elif filters["has_attachments"] == "false":
            filtered_emails = [email for email in filtered_emails if not email.get("attachments", [])]

        # Filtrar por rango de fechas
        def try_parse_date(date_str):
            """
            Intenta convertir una cadena a un objeto datetime.
            Si falla, devuelve None.
            """
            try:
                return datetime.fromisoformat(date_str).replace(tzinfo=None)
            except Exception:
                return None

        if filters["date_range"].get("type") == "range":
            start_date = try_parse_date(filters["date_range"].get("start_date"))
            end_date = try_parse_date(filters["date_range"].get("end_date"))

            # Solo filtrar si ambas fechas son válidas
            if start_date and end_date:
                filtered_emails = [
                    email for email in filtered_emails
                    if "date" in email
                    and (email_date := try_parse_date(email["date"]))  # Verifica y asigna la fecha del email
                    and start_date <= email_date <= end_date
                ]
        elif filters["date_range"].get("type") == "single":
            single_date = try_parse_date(filters["date_range"].get("date"))

            # Solo filtrar si la fecha es válida
            if single_date:
                filtered_emails = [
                    email for email in filtered_emails
                    if "date" in email
                    and (email_date := try_parse_date(email["date"]))  # Verifica y asigna la fecha del email
                    and email_date.date() == single_date.date()
                ]


        # Filtrar por remitentes, destinatarios, asunto, temas, palabras clave, y nombres de adjuntos
        def matches_criteria(email, field, values, threshold=75):
            if not values:
                    return True # Si no hay valores en la consulta, no se aplica filtro
            
            email_field = email.get(field, [])
            if field in ["subject", "body"]:
                email_field = [email_field] if email_field else []  # Asegurarse de que sea iterable
            else:
                email_field = email_field.split(", ") if email_field else []  # Dividir si es cadena

            # Asegurarse de que los valores sean cadenas antes de aplicar `.lower()`
            return any(
                fuzz.partial_ratio(str(values[0]).lower(), str(field_value).lower()) >= threshold
                for field_value in email_field if field_value  # Ignorar valores None
            )
        
        if filters["senders"]:
            filtered_emails = [
                email for email in filtered_emails
                if matches_criteria(email, "sender", filters["senders"])
            ]

        if filters["recipients"]:
            filtered_emails = [
                email for email in filtered_emails
                if matches_criteria(email, "recipients", filters["recipients"])
            ]

        # if filters["subject"]:
        #     filtered_emails = [
        #         email for email in filtered_emails
        #         if matches_criteria(email, "subject", [filters["subject"]])
        #     ]

        # if filters["themes"]:
        #     filtered_emails = [
        #         email for email in filtered_emails
        #         if matches_criteria(email, "body", filters["themes"])
        #     ]

        if filters["attachment_names"]:
            filtered_emails = [
                email for email in filtered_emails
                if any(
                    fuzz.partial_ratio(name.lower(), attachment["filename"].lower()) >= 75
                    for name in filters["attachment_names"]
                    for attachment in email.get("attachments", [])
                )
            ]

        return filtered_emails