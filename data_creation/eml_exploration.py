import email
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
import html
import os
import json
import re
from datetime import datetime
import dateparser
import hashlib

INDEX_FILE = "/home/connecthing/alfatec/data_creation/processed_emails_index.json"

def load_processed_index():
    """Carga el índice de eml_id procesados desde un archivo."""
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_processed_index(processed_ids):
    """Guarda el índice de eml_id procesados en un archivo."""
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_ids), f, ensure_ascii=False, indent=4)
        

def generate_eml_id(file_path):
    """Genera un ID único para un archivo .eml usando su contenido."""
    with open(file_path, 'rb') as f:
        content = f.read()
    return hashlib.md5(content).hexdigest()  # Genera un hash MD5 único basado en el contenido del archivo

def delete_email_disclaimers(body: str) -> str:
    """Elimina disclaimers comunes de un cuerpo de correo."""
    # Eliminar secuencias de símbolos innecesarios (----, **, etc.)
    body = re.sub(r'[-]{2,}', ' ', body)  # Reemplazar "----" o más por un espacio
    body = re.sub(r'\*+', ' ', body)  # Reemplazar "*" o más por un espacio
    body = re.sub(r'>+', '', body)
 
    # Eliminar cualquier espacio en exceso generado por los reemplazos
    body = re.sub(r'\s+', ' ', body).strip()
 
    # Eliminar disclaimers usando las expresiones regulares
    disclaimer_patterns = [
        r"Do you really need to print this email.*?oposición previstos en la propia ley..",
        r"(?i)AVISO DE CONFIDENCIALIDAD.*?CONFIDENTIALITY WARNING.*?lopd@gruposanjose\.biz",  # Combina ambos disclaimers en un solo patrón
        r"(?i)([*\/]*Este mensaje.*?antes de imprimir este mensaje\.*)",  # Disclaimer en español
        r"(?i)([*\/]*This message.*?before printing this message\.*)",  # Disclaimer en inglés
        r"Wasting paper is harmful to the enviroment\. Please consider that before printing this message\.*",  # Variante de disclaimer común
        r"(?i)AVISO LEGAL: Este mensaje va dirigido.*?prohibidas por la ley\.",  # Nuevo disclaimer
        r"CEDINOX se ha esforzado.*?Madrid \(Spain\)\.",  # Nuevo disclaimer de CEDINOX
        r"(?i)Este mensaje se dirige.*?por esta misma vía y proceda a su destrucción\.",  # Disclaimer de confidencialidad
        r"(?i)This message is intended.*?please immediately notify us via e-mail and delete it\.",  # Disclaimer de confidencialidad en ingles
        r"(?i)AVISO LEGAL De acuerdo con la normativa.*?por su parte del contenido de este aviso legal\.",  # Aviso legal de ACERINOX
        r"(?i)LEGAL WARNING According to the Spanish legislation.*?acceptance to the content of this legal warning\.",  # Legal Warning en inglés  
        r"(?i)Responsable del tratamiento\:.*?detallada sobre protección de Datos en nuestra página web\: www\.alfatec\.es",
        r"(?i)“INFORMACIÓN PROTECCIÓN DE DATOS.*?destinado únicamente a la persona o entidad a quien ha sido enviado\.”",
        r"(?i)De acuerdo con lo establecido en la Ley de Protección de Datos.*?y proceda a su destrucción\.",
        r"(?i)CONFIDENCIALIDAD\:.*?Si lo desea puede ejercitar los derechos A\.R\.C\.O\. en ARBEGUI S\.A\.\, Pol\. Industrial Bildosola Auzunea\, Parcela K2\, Artea\, Bizkaia\(48142\)",        
        r"(?i)Antes de imprimir este mensaje.*?Please notify us immediately by e\-mail and delete this message and all its attachments\.",        
    ]
    for pattern in disclaimer_patterns:
        body = re.sub(pattern, "", body, flags=re.DOTALL).strip()
 
 
    return body
 
 
def clean_text(text):
    """Limpia el texto eliminando disclaimers, espacios extraños y etiquetas HTML."""
    text = html.unescape(text)  # Decodifica caracteres HTML
    #soup = BeautifulSoup(text, "html.parser")
    #text = soup.get_text()
 
    # Paso 1: Normalizar tabs, saltos de línea y espacios múltiples
    text = re.sub(r'[\t\r\n]', ' ', text)  # Reemplazar tabs y saltos de línea por espacios
    text = re.sub(r'\s+', ' ', text)  # Reducir múltiples espacios consecutivos a uno solo
    text = re.sub(r'>+', '', text)
    text = re.sub(r'<+', '', text)
    text = re.sub(r'\*\_|\_\*|\*\*', '', text)
    text = re.sub(r'\*+', ' ', text)

    # Paso 2: Eliminar disclaimers comunes
    # text = delete_email_disclaimers(text)
 
    # Paso 3: Recortar espacios sobrantes
    text = text.strip()
 
    return text
 
 
def extract_body_parts(part):
    """Extrae y limpia las partes de texto del correo, priorizando `text/plain` y evitando duplicaciones."""
    if part.is_multipart():
        # Si es multipart, iterar sobre las partes
        for subpart in part.iter_parts():
            result = extract_body_parts(subpart)
            if result:  # Si encontramos una parte válida, devolvemos solo esa
                return result
    else:
        # Procesar solo `text/plain` o `text/html`
        if part.get_content_type() == "text/plain":
            try:
                charset = part.get_content_charset() or 'utf-8'
                raw_text = part.get_payload(decode=True).decode(charset)
                return clean_text(raw_text)  # Priorizar texto plano
            except Exception as e:
                print(f"Error al procesar `text/plain`: {e}")
        elif part.get_content_type() == "text/html":
            try:
                charset = part.get_content_charset() or 'utf-8'
                raw_text = part.get_payload(decode=True).decode(charset)
                return clean_text(raw_text)  # Procesar HTML solo si no hay texto plano
            except Exception as e:
                print(f"Error al procesar `text/html`: {e}")
 
    return None  # Si no se encuentra contenido válido
 
 
def extract_attachments(msg):
    """Extrae los adjuntos de un correo."""
    attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True)
        size = len(payload) if payload else 0
        attachments.append({
            "filename": filename,
            "content_type": content_type,
            "size": size
        })
    return attachments
 
 
def split_email_thread(body, first_to, first_from):
    """Divide un hilo de correos en mensajes individuales y devuelve una lista de mensajes."""
    # Eliminar espacios en exceso y normalizar el texto
    body = re.sub(r'\s+', ' ', body)
 
    # Definir patrones para detectar los encabezados de los mensajes
    header_patterns = [
        r"De:\s*(.{1,100})\s*(?:\[mailto:(.{1,100})\])?\s*Enviado el:\s*(.{1,100})"
        r"(?:\s*Para:\s*(.{1,100}))?"
        r"(?:\s*CC:\s*(.{1,100}))?"
        r"(?:\s*Asunto:\s*(.{1,100}))?",

        r"De:\s*(.{1,100})\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*"
        r"Para:\s*(.{1,100})\s*"
        r"cc:\s*(.{1,100})\s*"
        r"Fecha:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})\s*"
        r"Asunto:\s*(.{1,100})\s*",

        r"De:\s*(.{1,100})\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*"
        r"Para:\s*(.{1,100})\s*"
        r"Fecha:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})\s*"
        r"Asunto:\s*(.{1,100})\s*",

        r"El \d{1,2}/\d{1,2}/\d{4} a las \d{1,2}:\d{2}, .{1,100}?escribió:",

        r"El (\d{1,2} \w{3} \d{4}), a las (\d{1,2}:\d{2}), (.{1,100}) (.*?@.{1,100})(?:mailto:(.{1,100}))?\s*escribió:",

        r"El (\d{1,2}-\d{1,2}-\d{4} \d{1,2}:\d{2}),\s*(.*?)\s*escribió:"
    ]
 
    # Combinar patrones en una sola expresión regular
    combined_pattern = '|'.join(header_patterns)
 
    # Compilar el patrón con los flags adecuados
    pattern = re.compile(combined_pattern, flags=re.DOTALL | re.IGNORECASE)
 
    # Encontrar todas las coincidencias de los encabezados en el cuerpo
    matches = list(pattern.finditer(body))
 
    # Si no se encuentran encabezados, devolver el cuerpo completo como un solo mensaje
    if not matches:
        body = delete_email_disclaimers(body)
        return [{'body': body}]
 
    # Obtener las posiciones de inicio de cada encabezado
    positions = [match.start() for match in matches] + [len(body)]
 
    messages = []
 
    # Si hay texto antes del primer encabezado, incluirlo como el primer mensaje
    if positions[0] > 0:
        first_message = body[:positions[0]].strip()
        if first_message:
            messages.append({"body":first_message})
 
    # Extraer los mensajes basados en las posiciones
    for i in range(len(matches)):
        start_idx = positions[i]
        end_idx = positions[i + 1]
        message = body[start_idx:end_idx].strip()
        if message:
            messages.append({"body":message})
 
    # Procesar mensajes para extraer 'from' y 'date' si no son el primero
    all_recipients = list(set(first_to + first_from))
    for i, msg in enumerate(messages):
        if i > 0:  # Solo procesar los mensajes que no son el primero
            header_match1 = re.match(
                r"El (\d{1,2}/\d{1,2}/\d{4} a las \d{1,2}:\d{2}),\s*(.*?)\s*escribió:",
                msg["body"]
            )

            header_match2 = re.match(
                r"De:\s*(.*?)\s*(?:\[mailto:(.*?)\])?\s*Enviado el:\s*(.*?)"
                r"(?:\s*Para:\s*(.*?))?"
                r"(?:\s*CC:\s*(.*?))?"
                r"(?:\s*Asunto:\s*(.*?))?"
                r"(?:\s*Nº Encargo:\s*(.*?))?"
                r"(?:\s*Nº Salida:\s*(.*?))\s*",  # Elimina el '?' final aquí
                msg["body"], flags=re.DOTALL | re.IGNORECASE
            )
            header_match3 = re.match(
                r"De:\s*(.*?)\s*(?:\[mailto:(.*?)\])?\s*Enviado el:\s*(.*?)"
                r"(?:\s*Para:\s*(.*?))?"
                r"(?:\s*CC:\s*(.*?))?"
                r"(?:\s*Asunto:\s*(.*?))\s*",
                msg["body"], flags=re.DOTALL | re.IGNORECASE
            )
            header_match4 = re.match(
                r"De:\s*(.*?)\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*"
                r"Para:\s*(.*?)\s*"
                r"cc:\s*(.*?)\s*"
                r"Fecha:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})\s*"
                r"Asunto:\s*(.*?)\s*",
                msg["body"], flags=re.DOTALL | re.IGNORECASE
            )
            header_match5 = re.match(
                r"De:\s*(.*?)\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*"
                r"Para:\s*(.*?)\s*"
                r"Fecha:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})\s*"
                r"Asunto:\s*(.*?)\s*",
                msg["body"], flags=re.DOTALL | re.IGNORECASE
            )
            header_match6 = re.match(
                r"El (\d{1,2} \w{3} \d{4}, a las \d{1,2}:\d{2}), (.*?.*?@.*?)(?:mailto:(.*?))?\s*escribió:",
                msg["body"], flags=re.DOTALL | re.IGNORECASE
            )            
            header_match7 = re.match(
                r"El (\d{1,2}-\d{1,2}-\d{4} \d{1,2}:\d{2}),\s*(.*?)\s*escribió:",
                msg["body"], flags=re.DOTALL | re.IGNORECASE
            )

            if header_match1:  
                #Extract from
                msg["from"] = header_match1.group(2).strip()  # Extraer nombre
                for all_recipients_i in all_recipients:
                    match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                    if match:
                        if match.group(1) == header_match1.group(2).strip():
                            msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                            break  
                #Extract to
                remaining_recipients = [r for r in all_recipients if msg['from'] not in r]
                msg['to'] = ", ".join(remaining_recipients)
                all_recipients = list(set(all_recipients) | set(remaining_recipients) | set([msg['from']]))
                raw_date = header_match1.group(1)  # Extraer fecha
                parsed_date = dateparser.parse(raw_date, languages=['es', 'fr'])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match1.end():].strip()
 
            elif header_match2:
                if header_match2.group(2):
                    msg["from"] = header_match2.group(1).strip() + " " + header_match2.group(2).strip() # Extraer dirección de correo
                else:
                    msg["from"] = header_match2.group(1).strip()  # Extraer nombre
                    for all_recipients_i in all_recipients:
                        match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                        if match:
                            if match.group(1) == header_match2.group(1).strip():
                                msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                                break  
                msg["to"] = re.sub(r" mailto:[^,;]*", "", header_match2.group(4).strip().replace("'", "").replace(";", ","))
                all_recipients = list(set(all_recipients) | set(msg["to"].split(", ")) | set([msg['from']]))
                raw_date = header_match2.group(3)
                parsed_date = dateparser.parse(raw_date, languages=['es', 'fr'])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match2.end():].strip()
 
            elif header_match3:
                if header_match3.group(2):
                    msg["from"] = header_match3.group(1).strip() + " " + header_match3.group(2).strip()
                else:
                    msg["from"] = header_match3.group(1).strip()  # Extraer nombre
                    for all_recipients_i in all_recipients:
                        match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                        if match:
                            if match.group(1) == header_match3.group(1).strip():
                                msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                                break  
                msg["to"] = re.sub(r" mailto:[^,;]*", "", header_match3.group(4).strip().replace("'", "").replace(";", ","))
                all_recipients = list(set(all_recipients) | set(msg["to"].split(", ")) | set([msg['from']]))
                raw_date = header_match3.group(3)
                parsed_date = dateparser.parse(raw_date, languages=['es', 'fr'])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match3.end():].strip() # Eliminar el encabezado del cuerpo después de extraer la información        

            elif header_match4:
                if header_match4.group(2):
                    msg["from"] = header_match4.group(1).strip() + " " + header_match4.group(2).strip()  # Nombre y correo
                else:
                    msg["from"] = header_match4.group(1).strip()  # Extraer nombre
                    for all_recipients_i in all_recipients:
                        match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                        if match:
                            if match.group(1) == header_match4.group(1).strip():
                                msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                                break  
                msg["to"] = re.sub(r" mailto:[^,;]*", "", header_match4.group(3).strip().replace("'", "").replace(";", ","))
                all_recipients = list(set(all_recipients) | set(msg["to"].split(", ")) | set([msg['from']]))
                raw_date = header_match4.group(5)  # Fecha
                parsed_date = dateparser.parse(raw_date, languages=["es", "fr"])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match4.end():].strip()  # Cuerpo del mensaje después del encabezado

            elif header_match5:
                if header_match4.group(2):
                    msg["from"] = header_match5.group(1).strip() + " " + header_match5.group(2).strip()  # Nombre y correo
                else:
                    msg["from"] = header_match5.group(1).strip()  # Extraer nombre
                    for all_recipients_i in all_recipients:
                        match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                        if match:
                            if match.group(1) == header_match5.group(1).strip():
                                msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                                break  
                msg["to"] = re.sub(r" mailto:[^,;]*", "", header_match5.group(3).strip().replace("'", "").replace(";", ","))
                all_recipients = list(set(all_recipients) | set(msg["to"].split(", ")) | set([msg['from']]))
                raw_date = header_match5.group(4)  # Fecha
                parsed_date = dateparser.parse(raw_date, languages=["es", "fr"])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match5.end():].strip()  # Cuerpo del mensaje después del encabezado

            elif header_match6:
                msg["from"] = header_match6.group(2).strip()  # Extraer nombre
                for all_recipients_i in all_recipients:
                    match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                    if match:
                        if match.group(1) == header_match6.group(2).strip():
                            msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                            break  
                #Extract to
                remaining_recipients = [r for r in all_recipients if msg['from'] not in r]
                msg['to'] = ", ".join(remaining_recipients)
                all_recipients = list(set(all_recipients) | set(remaining_recipients) | set([msg['from']]))
                raw_date = header_match6.group(1)
                parsed_date = dateparser.parse(raw_date, languages=["es", "fr"])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match6.end():].strip()  # Cuerpo del mensaje después del encabezado
            elif header_match7:
                msg["from"] = header_match7.group(2).strip()  # Extraer nombre
                for all_recipients_i in all_recipients:
                    match = re.match(r"^(.*?)\s+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", all_recipients_i)
                    if match:
                        if match.group(1) == header_match7.group(2).strip():
                            msg["from"] = all_recipients_i  # Devuelve el nombre capturado, sin espacios extra
                            break  
                remaining_recipients = [r for r in all_recipients if msg['from'] not in r]
                msg['to'] = ", ".join(remaining_recipients)
                all_recipients = list(set(all_recipients) | set(remaining_recipients) | set([msg['from']]))
                raw_date = header_match7.group(1)  # Extraer fecha
                parsed_date = dateparser.parse(raw_date, date_formats=["%d-%m-%Y %H:%M"])
                msg["date"] = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else raw_date
                msg["body"] = msg["body"][header_match7.end():].strip()  # Cuerpo del mensaje después del encabezado
        
        msg["body"] = delete_email_disclaimers(msg["body"])
 
    return messages
 
 
def process_eml(file_path, root_path):
    """Procesa un archivo .eml y extrae los mensajes como entradas individuales."""
    eml_id = generate_eml_id(file_path)  # Generar el ID único para el .eml

    with open(file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
 
    attachments = extract_attachments(msg)
    body_parts = extract_body_parts(msg)
 
    # Extraer todos los correos/nombres del primer mensaje
    normalized_msg_to = msg["to"].replace("'", "").replace('"', "").replace("<", "").replace(">", "")
    first_to = normalized_msg_to.split(", ") if msg["to"] else []
    normalized_msg_from = msg["from"].replace("'", "").replace('"', "").replace("<", "").replace(">", "")
    first_from = [normalized_msg_from] if msg["from"] else []
    #all_recipients = list(set(first_to + first_from))  # Unificar y eliminar duplicados

    # Normalizar la fecha a datetime
    raw_date = msg["date"]
    normalized_date = None
    if raw_date:
        try:
            normalized_date = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            print(f"Error al analizar la fecha '{raw_date}': {e}")
            normalized_date = raw_date  # Dejar la fecha como está si no se puede analizar
 
    # Dividir el hilo en mensajes individuales
    email_thread = split_email_thread(body_parts, first_to, first_from)
    emails = []
 
    for i, message_info in enumerate(email_thread):
        if i == 0:
            # Primer mensaje
            email_info = {
                "eml_id": eml_id,
                "subject": msg['subject'],
                "sender": normalized_msg_from,
                "recipients": normalized_msg_to,
                "date": normalized_date,
                "body": message_info['body'],
                "attachments": attachments,  # Adjuntos solo para el primer mensaje
                "root_path": file_path  # Añadir el root_path completo
            }
            emails.append(email_info)
        else:
            # Segundo mensaje y siguientes
            #from_email = message_info["from"]
            #remaining_recipients = [r for r in all_recipients if r != from_email]  # Excluir el "from" actual
            #remaining_recipients_str = ", ".join(remaining_recipients)
            email_info = {
                "eml_id": eml_id,
                "subject": f"Re: {msg['subject']}",
                "sender": message_info['from'],
                "recipients": message_info['to'],  # Lista de correos excluyendo el "from" actual
                "date": message_info['date'],
                "body": message_info['body'],
                "attachments": [],  # Adjuntos solo para el primer mensaje
                "root_path": file_path  # Añadir el root_path completo
            }
            emails.append(email_info)
 
    return emails
 
 
def process_all_eml_in_directory(base_directory):
    """Procesa todos los archivos .eml en un directorio y guarda los resultados en un JSON."""
    processed_ids = load_processed_index()  # Cargar índice de eml_id procesados
    all_emails = []
    error_logs = []  # Lista para registrar errores

    # Lista de filtros a buscar en las rutas
    valid_projects = [
        "mad 179 - Bodega Casa Madero",
        "mad 185 - Ampliación Marqués de Murrieta",
        "mad 199 - Bodega y Almazara EL MOLINILLO",
        "mad 236 - BOC DEL ARXIDUC",
        "mad 273 - GRUPO PEÑAFLOR-VALLE DE UCO",
        "mad 281 - AMPLIACION BODEGA NUMANTHIA",
        "mad 289 - BODEGA DEIVA",
        "mad 297 - CASERIO DE DUENAS",
        "mad 298 - MASTER PLAN MURFATLAR RUMANIA",
        "mad 299 - REHABILITACION BODEGA GRANJA SANTULLANO"
    ]

    for root, _, files in os.walk(base_directory):
        for filename in files:
            if filename.endswith(".eml"):
                file_path = os.path.join(root, filename)

                # Filtrar por las rutas que no contienen los strings válidos
                if not any(valid_project in file_path for valid_project in valid_projects):
                    print(f"Ignorando archivo: {file_path} (no contiene strings válidos)")
                    continue

                try:
                    eml_id = generate_eml_id(file_path)

                    # Verificar si ya fue procesado
                    if eml_id in processed_ids:
                        print(f"Saltando archivo ya procesado: {file_path}")
                        continue

                    print(f"Procesando archivo: {file_path}")
                    email_data = process_eml(file_path, root)
                    all_emails.extend(email_data)
                    processed_ids.add(eml_id)  # Agregar el ID al índice de procesados

                except Exception as e:
                    print(f"Error al procesar el eml. {e}")
                    error_logs.append({"file": file_path, "error": str(e)})

    # Guardar los datos en un archivo JSON sin perder los emails anteriores
    output_file = "/home/connecthing/alfatec/data_creation/processed_emails.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Cargar emails previamente guardados si el archivo ya existe
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as json_file:
            try:
                existing_data = json.load(json_file)
                existing_emails = existing_data.get("emails", [])
            except json.JSONDecodeError:
                existing_emails = []  # Si hay un error en el JSON, empezar desde cero
    else:
        existing_emails = []

    # Añadir solo los nuevos emails sin duplicados
    existing_emails.extend(all_emails)

    # Guardar la lista completa de emails procesados
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump({"emails": existing_emails}, json_file, ensure_ascii=False, indent=4)

    # Actualizar el índice de procesados
    save_processed_index(processed_ids)

    # Guardar errores en un archivo JSON
    if error_logs:
        error_file = "/home/connecthing/alfatec/data_creation/error_logs.json"
        with open(error_file, "w", encoding="utf-8") as error_json:
            json.dump(error_logs, error_json, ensure_ascii=False, indent=4)
        print(f"Se encontraron {len(error_logs)} errores. Revisa {error_file} para más detalles.")

    print(f"Procesamiento completado. Se guardaron {len(all_emails)} correos nuevos.")
    return all_emails


# Ejecutar el procesamiento
if __name__ == "__main__":
    base_directory = "/srv/datos/encargos_sintratar"  # Cambia este directorio según sea necesario
    process_all_eml_in_directory(base_directory)