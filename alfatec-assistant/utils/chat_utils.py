import asyncio
import os
import time
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.functions import KernelArguments
import aiohttp


load_dotenv()

class MaxRetriesExceededError(Exception):
    """Excepción lanzada cuando se excede el número máximo de reintentos."""
    pass

class SemanticQueryEngine:
    def __init__(self, model_name: str, context: str = None, history_limit: int = 10, chat_history=None, rate_limit: float = 0.0):
        self.kernel = sk.Kernel()

        if model_name not in ["gpt-35-16k", "gpt-4-32k", "gpt-4o"]:
            raise ValueError(f"{model_name} is an invalid model.")
        self.deployment_name = f"{model_name}"
        self.service_id = 'aoai_chat_completion'

        # Leer endpoints y claves API desde variables de entorno
        self.endpoints = [
            os.getenv("ENDPOINT_1"),
            os.getenv("ENDPOINT_2"),
            os.getenv("ENDPOINT_3"),
            os.getenv("ENDPOINT_4"),
            os.getenv("ENDPOINT_5"),
            os.getenv("ENDPOINT_6"),
            os.getenv("ENDPOINT_7"),
            os.getenv("ENDPOINT_8"),
            os.getenv("ENDPOINT_9"),
            os.getenv("ENDPOINT_10"),
            os.getenv("ENDPOINT_11"),
            os.getenv("ENDPOINT_12"),
            os.getenv("ENDPOINT_13"),
            os.getenv("ENDPOINT_14")
        ]
        self.api_keys = [
            os.getenv("AZURE_API_KEY_1"),
            os.getenv("AZURE_API_KEY_2"),
            os.getenv("AZURE_API_KEY_3"),
            os.getenv("AZURE_API_KEY_4"),
            os.getenv("AZURE_API_KEY_5"),
            os.getenv("AZURE_API_KEY_6"),
            os.getenv("AZURE_API_KEY_7"),
            os.getenv("AZURE_API_KEY_8"),
            os.getenv("AZURE_API_KEY_9"),
            os.getenv("AZURE_API_KEY_10"),
            os.getenv("AZURE_API_KEY_11"),
            os.getenv("AZURE_API_KEY_12"),
            os.getenv("AZURE_API_KEY_13"),
            os.getenv("AZURE_API_KEY_14")
        ]
        self.current_endpoint_index = 0
        self.endpoint = self.endpoints[self.current_endpoint_index]
        self.api_key = self.api_keys[self.current_endpoint_index]
        self.prompt = context

        print(f"[DEBUG] Inicializando SemanticQueryEngine con Endpoint: {self.endpoint}")
        print(f"[DEBUG] API Key en uso en SemanticQueryEngine: {self.api_key}")

        # Inicializar kernel y configuraciones adicionales
        self.initialize_kernel()
        self.chat_history = chat_history if chat_history else []
        self.history_limit = history_limit
        self.rate_limit = rate_limit

        # Diccionario para guardar las marcas de tiempo de suspensión de cada endpoint
        self.endpoint_timeout_flags = {i: 0 for i in range(len(self.endpoints))}
        self.suspension_duration = 30  # 30 segundos de espera tras alcanzar el límite

    def initialize_kernel(self):
        # Re-inicializar el kernel con el endpoint y API key actuales
        self.kernel = sk.Kernel()
        self.kernel.add_service(
            AzureChatCompletion(
                service_id=self.service_id,
                deployment_name=self.deployment_name,
                endpoint=self.endpoint,
                api_key=self.api_key
            )
        )
        self.execution_settings = OpenAIChatPromptExecutionSettings(
            service_id=self.service_id,
            ai_model_id=self.deployment_name,
            max_tokens=2000,
            temperature=0.7,
        )
        self.prompt_template_config = PromptTemplateConfig(
            template=self.prompt,
            name="chat",
            template_format="semantic-kernel",
            input_variables=[
                InputVariable(name="user_input", description="The user input", is_required=True),
            ],
            execution_settings=self.execution_settings,
        )
        self.chat_function = self.kernel.add_function(
            function_name="chat",
            plugin_name="chatPlugin",
            prompt_template_config=self.prompt_template_config,
        )

    async def chat(self, input_text: str, retries=10, timeout=180) -> str:
        num_endpoints = len(self.endpoints)
        for attempt in range(retries):
            # Verificar si todos los endpoints están en período de espera
            if all(time.time() < self.endpoint_timeout_flags[i] for i in range(num_endpoints)):
                print("[UTILS] Todos los endpoints están en espera. Esperando 5 segundos antes de reintentar.")
                await asyncio.sleep(5)  # Espera general para todos los endpoints en suspensión
                raise MaxRetriesExceededError("No se pudo obtener una respuesta: todos los endpoints están en espera.")
                #continue  # Vuelve a intentar sin rotar

            # Verificar disponibilidad del endpoint actual
            if time.time() < self.endpoint_timeout_flags[self.current_endpoint_index]:
                print(f"[UTILS] Endpoint {self.endpoint} está en período de espera. Cambiando de endpoint.")
                self.rotate_to_next_active_endpoint()
                continue

            try:
                start_time = time.time()
                chat_context = self.get_formatted_history()
                full_prompt = f"Historial:{chat_context}\n User Actual Prompt: {input_text}\n"
                
                print(f"[UTILS] Consultando Endpoint {self.current_endpoint_index + 1}: {self.endpoint}")

                # Realiza la solicitud con timeout
                answer = await asyncio.wait_for(
                    self.kernel.invoke(
                        self.chat_function, KernelArguments(user_input=full_prompt)
                    ), timeout=timeout
                )

                # Calcular tiempo de respuesta
                response_time = time.time() - start_time
                print(f"[UTILS] Attempt {attempt + 1} succeeded in {response_time:.2f} seconds.")

                answer_text = str(answer).replace("\n", "<br>")
                self.add_to_history(input_text, answer_text)
                return answer_text

            except asyncio.TimeoutError:
                print(f"[UTILS] Attempt {attempt + 1} timed out after {timeout} seconds.")
                self.suspend_current_endpoint()  # Marcar el endpoint actual como suspendido
                self.rotate_to_next_active_endpoint()  # Rotar al siguiente endpoint activo

            except Exception as e:
                print(f"[UTILS] Attempt {attempt + 1} failed with error: {e}")
                if hasattr(e, 'status_code') and e.status_code == 429:
                    print(f"[UTILS] Límite de tasa alcanzado en endpoint {self.endpoint}. Aplicando suspensión.")
                    self.suspend_current_endpoint()  # Marcar el endpoint como suspendido
                else:
                    print(f"[UTILS] Error inesperado en endpoint {self.endpoint}. Cambiando de endpoint.")
                self.rotate_to_next_active_endpoint()  # Rotar al siguiente endpoint activo

        # Si todos los reintentos fallan
        raise MaxRetriesExceededError("No se pudo obtener una respuesta después de múltiples reintentos.")

    def suspend_current_endpoint(self):
        """ Marca el endpoint actual como suspendido por el período de suspensión """
        self.endpoint_timeout_flags[self.current_endpoint_index] = time.time() + self.suspension_duration

    def rotate_to_next_active_endpoint(self):
        """ Rota al siguiente endpoint activo en la lista """
        num_endpoints = len(self.endpoints)
        for _ in range(num_endpoints):
            self.current_endpoint_index = (self.current_endpoint_index + 1) % num_endpoints
            if time.time() >= self.endpoint_timeout_flags[self.current_endpoint_index]:
                # Encontró un endpoint activo
                self.endpoint = self.endpoints[self.current_endpoint_index]
                self.api_key = self.api_keys[self.current_endpoint_index]
                print(f"[UTILS] Cambiando al endpoint activo {self.endpoint} con la clave API {self.api_key}")
                self.initialize_kernel()
                return
        print("[UTILS] No hay endpoints activos disponibles en este momento.")
    
    # Otros métodos permanecen iguales

    def add_to_history(self, user_input: str, assistant_response: str) -> None:
        # Solo agrega al historial si ambos mensajes son válidos
        if user_input.strip() and assistant_response.strip():
            # Guarda el par de mensajes del usuario y el asistente como un solo objeto para evitar confusión
            self.chat_history.append({"user": user_input, "assistant": assistant_response})
            
        # Limitar el tamaño del historial
        if len(self.chat_history) > self.history_limit:
            self.chat_history.pop(0)


    def get_formatted_history(self) -> str:
        formatted_history = ""
        for entry in self.chat_history:
            formatted_history += f"User: {entry['user']}\nChatBot: {entry['assistant']}\n"
        return formatted_history


    def count_tokens(self, text):
        return len(text.split())

    async def process_request_with_rate_limit(self, input_text):
        """
        Procesa una solicitud aplicando el control de frecuencia de rate limit.
        """
        await asyncio.sleep(self.rate_limit)  # Control de frecuencia antes de llamar a chat
        return await self.chat(input_text)

    # Nuevo método para facilitar la llamada directa similar a la original
    async def request_with_rate_limit(self, input_text: str):
        """
        Envía una solicitud a la API, respetando el rate limit, y devuelve la respuesta.
        """
        return await self.process_request_with_rate_limit(input_text)

