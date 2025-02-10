from utils.chat_utils import SemanticQueryEngine, MaxRetriesExceededError
from utils.prompts import CLASSIFICATION_PROMPT, CONVERSATIONAL_PROMPT
from search_engine.search_engine import SearchEngine
from response_creator.response_creator import ResponseCreator

class ChatKernel:
    def __init__(self, chat_history, conversational=True, password=False,flows=None,tone=""):
        """
        Inicializa el ChatKernel con los estados de los flujos.
        
        :param chat_history: Historial del chat.
        :param conversational: Booleano, activa o desactiva el flujo conversacional (por defecto True).
        :param password: Booleano, activa o desactiva el flujo de contraseñas (por defecto False).
        :param kwargs: Otros flujos adicionales como claves booleanas (e.g., custom_flow=True).
        """
        self.chat_history = chat_history
        self.last_classification = None
        self.tone = ""
        
        # Estados de los flujos: usa el diccionario proporcionado o valores predeterminados
        default_flows = {
            "conversational": True,
            "consult": False
        }
        self.flows = flows if flows else default_flows


        # Motores semánticos
        self.semantic_engine_classifier = SemanticQueryEngine(
            model_name="gpt-4o",
            context=CLASSIFICATION_PROMPT,
            history_limit=1,
            chat_history=[]  # No necesita historial compartido
        )

        self.semantic_engine_conversational = SemanticQueryEngine(
            model_name="gpt-4o",
            context=self.tone + CONVERSATIONAL_PROMPT,
            history_limit=5,
            chat_history=self.chat_history
        )

        self.semantic_engine_consult = SemanticQueryEngine(
            model_name="gpt-4o",
            context="",
            history_limit=5,
            chat_history=self.chat_history
        )

        print("[KERNEL] ChatKernel inicializado con flujos:", self.flows)

    async def run_consult(self, user_input):
        search_engine = SearchEngine()
        #filtered_emails = await search_engine.search(query=user_input)
        filtered_emails = await search_engine.search(query=user_input, k=1000)

        if not filtered_emails:
            return "No se encontraron correos relevantes."

        response_creator = ResponseCreator(filtered_emails, user_input)
        resumen = await response_creator.summarize_emails()

        return resumen
    
    async def classify_input(self, user_input):
        """
        Clasifica el input del usuario en uno de los flujos definidos.
        """
        try:
            print(f"[KERNEL] Clasificando input: '{user_input}'")
            classification_prompt = f"Por favor, clasifica el siguiente mensaje:\n'{user_input}'"
            response = await self.semantic_engine_classifier.request_with_rate_limit(classification_prompt)
            print(f"[KERNEL] Respuesta de clasificación: '{response}'")
            
            if "consult" in response.lower():
                self.last_classification = "consult"
                return "consult"
            
            # Añade más flujos si es necesario aquí
            
            self.last_classification = "conversational"
            return "conversational"
        
        except MaxRetriesExceededError as e:
            print("[KERNEL] Error: No se pudo clasificar el mensaje.")
            print(f"[KERNEL] Detalle del error: {e}")
            self.last_classification = "conversational"  # Por defecto, redirigir al conversacional
            return "conversational"

    async def handle_user_input(self, user_input):
        """
        Procesa el input del usuario según el flujo clasificado.
        Si el flujo está desactivado, redirige al flujo conversacional con un mensaje contextual.
        """
        print(f"[KERNEL] Procesando input: '{user_input}'")
        message_type = await self.classify_input(user_input)
        print(f"[KERNEL] Tipo de mensaje clasificado como: '{message_type}'")
        
        # Si el flujo está desactivado, redirigir al conversacional
        if not self.flows.get(message_type, False):
            if self.flows.get("conversational", False):  # Conversacional está activo
                # Generar dinámicamente un mensaje usando el motor semántico
                unavailable_message = await self.semantic_engine_conversational.request_with_rate_limit(
                    f"Genera un mensaje para informar al usuario que el flujo '{message_type}' no está disponible en este momento. Interpreta el nombre del flujo para dar la respuesta no des el nombre literalmente."
                )
                # Retornar el mensaje dinámico junto con la redirección al flujo conversacional
                return f"{unavailable_message}" \
                    
            else:
                return "El flujo básico conversacional está desactivado. No puedo procesar tu solicitud."
        
        # Si el flujo está activo, manejar normalmente
        try:
            if message_type == "conversational":
                print("[KERNEL] Redirigiendo al motor de conversación.")
                return await self.semantic_engine_conversational.request_with_rate_limit(user_input)

            elif message_type == "consult":
                print("[KERNEL] Redirigiendo al motor de conversación para consulta.")
                #return await self.semantic_engine_consult.request_with_rate_limit(user_input)
                return await self.run_consult(user_input)
            
            else:
                return "Lo siento, no puedo clasificar tu solicitud. Por favor, intenta de nuevo."
        
        except MaxRetriesExceededError as e:
            print("[KERNEL] Error: No se pudo manejar el mensaje.")
            print(f"[KERNEL] Detalle del error: {e}")
            return "Lo siento, no se pudo procesar tu solicitud en este momento. Por favor, intenta más tarde."

    def get_last_classification(self):
        """
        Devuelve el valor de la última clasificación realizada.
        """
        return self.last_classification

    def get_active_flows(self):
        """
        Devuelve una lista de los flujos activos actualmente.
        """
        return [flow for flow, active in self.flows.items() if active]