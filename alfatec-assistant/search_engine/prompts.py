DETECT_SENDER_PROMPT = """
Eres un sistema especializado en extraer remitentes de correos electrónicos mencionados en una consulta. El remitente es la persona o dirección de correo electrónico que envía un mensaje.

Tarea:
1. Identifica todas las direcciones de correo electrónico o nombres que se mencionen como remitentes en la consulta. 
2. Ignora los destinatarios o cualquier otra referencia que no sea un remitente.
Nota: Puede ser que no se indique explicitamente que es un remitente, como por ejemplo: "Encuentra los correos de Antuan". En este caso tiene que deducirse que Antuan es el remitente.
Ejemplos:
1. "Quiero todos los correos mandados por maria@ejemplo.com que hablen de X y que tengan como destinatario manuel@ejemplo.com"
    Respuesta: ["maria@ejemplo.com"]
2. "Necesito correos enviados por Juan o por juan@correo.com"
    Respuesta: ["juan@correo.com"]
3. "Encuentra los correos de Antuan"
    Respuesta: ["Antuan"]
4. "Los correos mandados a jose@example.com"
    Respuesta: []

Texto del usuario: {{$user_input}}

Nota: Responde únicamente con un string que simule una lista de python. Por ejemplo: ["remitente1@example.com", "remitente2@example.com"]
"""


DETECT_RECIPIENTS_PROMPT = """
Eres un sistema especializado en extraer destinatarios de correos electrónicos mencionados en una consulta. El destinatario es la persona o dirección de correo electrónico a la que se envía un mensaje.

Tarea:
1. Identifica todas las direcciones de correo electrónico o nombres que se mencionen como destinatarios en la consulta. 
2. Ignora remitentes u otras referencias que no sean destinatarios.

Ejemplos:
1. "Quiero todos los correos mandados por maria@ejemplo.com que tengan como destinatario manuel@ejemplo.com"
    Respuesta: ["manuel@ejemplo.com"]
2. "Los correos enviados a Juan o a juan@correo.com"
    Respuesta: ["juan@correo.com"]
3. "Quiero correos mandados por jose@example.com"
    Respuesta: []

Texto del usuario: {{$user_input}}

Nota: Responde únicamente con un string que simule una lista de python. Por ejemplo: ["destinatario1@example.com", "destinatario2@example.com"]
"""

DETECT_DATE_PROMPT = """
Eres un sistema especializado en identificar fechas y rangos de fechas en una consulta proporcionada por el usuario.

Tareas:
1. Detecta si el usuario menciona una fecha única, un rango de fechas o una expresión relativa de tiempo.
2. Para expresiones relativas como "los últimos 7 días" o "el último mes", calcula y devuelve las fechas absolutas basándote en la fecha actual: {{current_date}}.
3. Extrae la fecha o el rango en cualquier formato legible por humanos, como "21/07/2022", "el 3 de marzo de 2023", "entre el 1 de enero y el 5 de febrero de 2023", o expresiones relativas como "los últimos 7 días", "el mes pasado", etc.
4. Devuelve el resultado de la detección en formato JSON:
   - Si es una sola fecha: {"type": "single", "date": "YYYY-MM-DD"}.
   - Si es un rango de fechas: {"type": "range", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
   - Si no hay fechas mencionadas: {"type": "none"}.

Ejemplos:
1. "Quiero todos los correos del 21/07/2022"
   Respuesta: {"type": "single", "date": "2022-07-21"}
2. "Los correos entre el 1 de marzo y el 15 de marzo de 2023"
   Respuesta: {"type": "range", "start_date": "2023-03-01", "end_date": "2023-03-15"}
3. "Quiero correos mandados en los últimos 7 días"
   Respuesta: {"type": "range", "start_date": "2023-03-14", "end_date": "2023-03-21"} (suponiendo que hoy es 2023-03-21)
4. "Quiero correos del último mes"
   Respuesta: {"type": "range", "start_date": "2023-02-01", "end_date": "2023-02-28"} (suponiendo que hoy es marzo de 2023)
5. "Quiero correos mandados recientemente"
   Respuesta: {"type": "none"}

Texto del usuario: {{$user_input}}

Nota: Responde únicamente con un string que simule un diccionario de python. No incluyas explicaciones adicionales.
"""


DETECT_ATTACHMENTS_PROMPT = """
Eres un sistema especializado en detectar si el usuario solicita específicamente correos electrónicos que contengan o no contengan documentos adjuntos, o si no menciona nada al respecto.

Tarea:
1. Determina si el usuario menciona explícitamente que los correos:
   - Deben tener documentos adjuntos. Responde con "true".
   - No deben tener documentos adjuntos. Responde con "false".
   - No menciona nada sobre documentos adjuntos. Responde con "null".

Ejemplos:
1. "Quiero correos que tengan documentos adjuntos"
   Respuesta: true
2. "Quiero correos que no tengan documentos adjuntos"
   Respuesta: false
3. "Quiero todos los correos enviados por maria@example.com"
   Respuesta: null
4. "Los correos que incluyan archivos o fotos"
   Respuesta: true
5. "Quiero correos sobre el tema 'ampliación de la bodega'"
   Respuesta: null

Texto del usuario: {{$user_input}}

Nota: Responde únicamente con "true", "false" o "null". No incluyas explicaciones adicionales.
"""


DETECT_ATTACHMENT_NAMES_PROMPT = """
Eres un sistema especializado en extraer nombres de archivos mencionados en una consulta de usuario.

Tarea:
1. Detecta todos los nombres de documentos adjuntos mencionados en la consulta, como "fotos_bodega.png" o "documento.pdf".
2. Los nombres de los documentos suelen tener extensiones comunes como .pdf, .png, .jpg, .docx, .xlsx, etc.
3. Si no se menciona ningún documento adjunto, devuelve una lista vacía: [].

Ejemplos:
1. "Quiero los correos que incluyan un archivo llamado informe_final.pdf"
   Respuesta: ["informe_final.pdf"]
2. "Los correos con adjuntos como reporte_2023.xlsx y datos.csv"
   Respuesta: ["reporte_2023.xlsx", "datos.csv"]
3. "Correos que tienen imágenes adjuntas como foto1.png"
   Respuesta: ["foto1.png"]
4. "Quiero el correo que tiene una imágen con el nombre Informe Final o algo parecido"
   Respuesta: ['Informa Final']
4. "Quiero correos pero no menciono ningún documento"
   Respuesta: []

Texto del usuario: {{$user_input}}

Nota: Responde únicamente con un string que simule una lista de python. Por ejemplo: ["archivo1.pdf", "imagen.png"]. No incluyas explicaciones adicionales.
"""


DETECT_THEME_SUBJECT_BODY_PROMPT = """
Eres un sistema especializado en detectar si el usuario menciona explícitamente el contenido del correo electrónico, su temática o su asunto en la consulta.

Tareas:
1. Si el usuario menciona palabras como:
   - "tema", "temática", "asunto", "contenido", "hablen de", "mencionen", "se trate de", "relacionados con", etc.
   - O cualquier frase que indique interés en el **contenido del correo** o su **asunto**, responde con **true**.
   
2. Si el usuario **no menciona** nada relacionado con el contenido o el asunto del correo (por ejemplo, solo busca por remitente, destinatario, fechas o adjuntos), responde con **false**.

### **Ejemplos:**
1. **"Quiero todos los correos que hablen de contratos y licitaciones"**
   - Respuesta: 'true'
2. **"Los correos enviados por maria@example.com que hablen sobre la ampliación de la bodega"**
   - Respuesta: 'true'
3. **"Quiero los correos cuyo asunto contenga la palabra 'factura'"**
   - Respuesta: 'true'
4. **"Dame los correos enviados por manuel@example.com a juan@example.com"**
   - Respuesta: 'false'
5. **"Necesito ver los emails con documentos adjuntos"**
   - Respuesta: 'false'
6. **"Los correos recibidos por Pedro sobre cambios en el contrato"**
   - Respuesta: 'true'
7. **"Correos de Juan con archivos adjuntos"**
   - Respuesta: 'false'

### **Texto del usuario:** {{$user_input}}

Nota: Responde únicamente con un string que sea 'true' o 'false' sin explicaciones adicionales.
"""
