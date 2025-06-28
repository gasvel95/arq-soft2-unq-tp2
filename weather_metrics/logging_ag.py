from opensearchpy import OpenSearch
from datetime import datetime
import time
import logging
from config import CONFIG


# ---------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ---------------------------------------------------
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    level=logging.DEBUG
)

# Crear un cliente de OpenSearch
client = OpenSearch(
    hosts=[CONFIG["open_search_uri"]],
    http_auth=("admin", "admin"),  # Si es necesario
    use_ssl=False,
    verify_certs=False,
)

# Definir el nombre del índice en OpenSearch
log_index = "weather_logs"

# Función para enviar logs a OpenSearch
def send_log_to_opensearch(log_message, level):
    document = {
        "timestamp": datetime.utcnow(),
        "log_message": log_message,
        "level": level,  # Puedes cambiar el nivel de los logs según lo que necesites
    }

    response = client.index(
        index=log_index,
        body=document,
        refresh=True  # Asegura que el documento esté disponible inmediatamente
    )
    print(f"Log enviado a OpenSearch: {response['result']}")

# Función para hacer un log y enviarlo a OpenSearch
#def log_to_opensearch(log_message):
#    logging.info(log_message)
#    send_log_to_opensearch(log_message)

## level: INFO | ERROR
def log_to_opensearch(log_message, level):
    if level == "INFO":
        logging.info(log_message)
    else: 
        logging.error(log_message)
    
    send_log_to_opensearch(log_message, level)