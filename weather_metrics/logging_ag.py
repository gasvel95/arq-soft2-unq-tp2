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

client = OpenSearch(
    hosts=[CONFIG["open_search_uri"]],
    http_auth=("admin", "admin"), 
    use_ssl=False,
    verify_certs=False,
)

log_index = "weather_logs"

# Función para enviar logs a OpenSearch
def send_log_to_opensearch(log_message, level):
    document = {
        "timestamp": datetime.utcnow(),
        "log_message": log_message,
        "level": level, 
    }
    print(f"++++++++++++++++++++++++++++++++++++++++++++++++++++++++ document { document} ")
    print(f"++++++++++++++++++++++++++++++++++++++++++++++++++++++++ document { document} ")

    response = client.index(
        index=log_index,
        body=document,
        refresh=True   
    )
    print(f"Log enviado a OpenSearch: {response['result']}")

## level: INFO | ERROR
def log_to_opensearch(log_message, level):
    log_message_to_send = f"METRIC - {log_message}"  
    if level == "INFO":
        logging.info(log_message_to_send)
    else: 
        logging.error(log_message_to_send)
    
    send_log_to_opensearch(log_message_to_send, level)