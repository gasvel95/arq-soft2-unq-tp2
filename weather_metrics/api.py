# weather_metrics/api.py

from datetime import datetime
import json
import time
import logging
from functools import wraps
import pytz
import requests
from fastapi import FastAPI, HTTPException, Response
import pybreaker
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from hard_metrics.hardware import update_memory_metrics, update_cpu_metrics, update_disk_metrics, update_cpu_temperature 
from business_metrics.bussines_metrics import weather_average_day, weather_average_week, weather_current_temperature, weather_current_humidity, weather_current_pressure, weather_current_timestamp
from repository import get_latest, avg_since
from logging_ag import log_to_opensearch
from fastapi_websocket_rpc import RpcMethodsBase, WebSocketRpcClient
import asyncio
from tenacity import RetryError, retry_if_exception_type, wait_fixed, stop_after_attempt

from config import CONFIG


PORT = 8001

circuit_breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=60)


RETRY_CONFIG = {
    'wait':wait_fixed(3), 'stop':stop_after_attempt(2),'retry':retry_if_exception_type(Exception)
}

# ---------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ---------------------------------------------------
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    level=logging.DEBUG
)

# ---------------------------------------------------
# AISLAMOS EN METODOS PARA IMPLEMENTAR PYBREAKER
# ---------------------------------------------------
@circuit_breaker
def rpc_call_current():
    return asyncio.run(get_current(f"ws://weather_loader:{PORT}/ws"))
@circuit_breaker
def rpc_call_avg_day():
    return asyncio.run(get_avg_day(f"ws://weather_loader:{PORT}/ws"))
@circuit_breaker
def rpc_call_avg_week():
    return asyncio.run(get_avg_week(f"ws://weather_loader:{PORT}/ws"))

# ---------------------------------------------------
# METODOS RPC CLIENT
# ---------------------------------------------------
async def get_current(uri):
    async with WebSocketRpcClient(uri,RpcMethodsBase(),RETRY_CONFIG) as client:
        response = await client.other.getCurrent()
        return response.result
    
async def get_avg_day(uri):
    async with WebSocketRpcClient(uri,RpcMethodsBase(),RETRY_CONFIG) as client:
        response = await client.other.avgDay()
        return response.result
    
async def get_avg_week(uri):
    async with WebSocketRpcClient(uri,RpcMethodsBase(),RETRY_CONFIG) as client:
        response = await client.other.avgWeek()
        return response.result
    
# ---------------------------------------------------
# DECORADOR DE CACHE EN MEMORIA CON TTL
# ---------------------------------------------------
def ttl_cache(seconds: int):
    cache = {}  # key -> (result, timestamp)

    def decorator(func):
        logger = logging.getLogger("cache")
        logger.setLevel(logging.DEBUG)

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            entry = cache.get(key)
            now = time.time()

            if entry and (now - entry[1] < seconds):
                logger.debug(f"CACHE HIT  {func.__name__} args={key}")
                return entry[0]

            logger.debug(f"CACHE MISS {func.__name__} args={key}")
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        return wrapper

    return decorator

# ---------------------------------------------------
# CREACIÓN DE LA APP
# ---------------------------------------------------
app = FastAPI(
    title="Weather Metrics API",
    version="1.0.0",
    description="API para consultar métricas de temperatura con observabilidad Prometheus"
)

# ---------------------------------------------------
# MODELOS Pydantic
# ---------------------------------------------------
class CurrentResponse(BaseModel):
    temperature: float
    humidity: int
    pressure: int
    datetime: str

class AverageResponse(BaseModel):
    average: float

# ---------------------------------------------------
# MÉTRICAS Prometheus
# ---------------------------------------------------
REQUEST_COUNT = Counter(
    'weather_api_request_count',
    'Contador de peticiones HTTP',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'weather_api_request_latency_seconds',
    'Latencia de peticiones en segundos',
    ['method', 'endpoint']
)

REQUEST_COUNT_ERROR = Counter(
    'weather_api_request_count_failed',
    'Contador de peticiones HTTP fallidas (errores 500 u otros)',
    ['method', 'endpoint', 'http_status']
)

# ---------------------------------------------------
# MIDDLEWARE PARA INSTRUMENTACIÓN
# ---------------------------------------------------
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = None 
        try:
            response = await call_next(request)
            elapsed = time.time() - start

            # Registrar latencia
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(elapsed)

            # Contar la petición
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                http_status=response.status_code
            ).inc()
        except Exception as e:
            log_to_opensearch(f"ERROR -> {e}",  "ERROR")
            elapsed = time.time() - start
            # Registrar latencia
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(elapsed)

            REQUEST_COUNT_ERROR.labels(                
                method=request.method,
                endpoint=request.url.path,
                http_status= "500" if (response == None) else response.status_code
                ).inc()
        return response

app.add_middleware(MetricsMiddleware)

# ---------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------
@app.get(
    "/weather/current",
    response_model=CurrentResponse,
    summary="Temperatura actual",
    description="Devuelve la última medición de temperatura, humedad y presión."
)
def current():
    log_to_opensearch(f"================ consulta current ==================",  "INFO")    
    parsed_response = None
    try:
        doc = rpc_call_current()
        if not doc:
           log_to_opensearch(f"404  - No hay datos de clima disponibles aún",  "ERROR")                   
            raise HTTPException(status_code=404, detail="No hay datos de clima disponibles aún")
        json_acceptable_string = doc.replace("'", "\"")
        parsed_response = json.loads(json_acceptable_string)
    except pybreaker.CircuitBreakerError:
        city = CONFIG["city"]
        api_key = CONFIG["weatherstack_key"]
        gmt_timezone = pytz.timezone("America/Buenos_Aires")
        url = f"http://api.weatherstack.com/current?query={city}&access_key={api_key}&units=m"
        response = requests.get(url, timeout=10)
        if(response.status_code == 200):
            data = response.json()
            weather_date = datetime.now().astimezone(gmt_timezone)
            parsed_response = {
                "temperature": data["current"]["temperature"],
                "humidity": data["current"]["humidity"],
                "pressure": data["current"]["pressure"],
                "datetime": weather_date.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            raise HTTPException(status_code=503, detail="Servicio temporalmente fuera de servicio")
    except RetryError:
        raise HTTPException(status_code=502, detail="Servicio no responde. Vuelva a intentar.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error de conexión: {str(e)}")
    return parsed_response


@app.get(
    "/weather/average/day",
    response_model=AverageResponse,
    summary="Promedio de temperatura últimas 24 horas",
    description="Devuelve la temperatura media del último día."
)
@ttl_cache(seconds=60)
def avg_day():
    log_to_opensearch(f"================ consulta avg_day ==================",  "INFO")
    avg = None
    try:
        avg = rpc_call_avg_day()
        if avg is None:
            log_to_opensearch(f"404  - No hay datos de las últimas 24 horas",  "ERROR")                              
            raise HTTPException(status_code=404, detail="No hay datos de las últimas 24 horas")
    except pybreaker.CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Servicio temporalmente fuera de servicio")
    except RetryError:
        raise HTTPException(status_code=502, detail="Servicio no responde. Vuelva a intentar.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error de conexión: {str(e)}")
    return {"average": avg}

@app.get(
    "/weather/average/week",
    response_model=AverageResponse,
    summary="Promedio de temperatura última semana",
    description="Devuelve la temperatura media de los últimos 7 días."
)
@ttl_cache(seconds=300)
def avg_week():

    log_to_opensearch(f"================ consulta avg_week ==================",  "INFO")
    avg = None
    try:
        avg = rpc_call_avg_week()
        if avg is None:
            raise HTTPException(status_code=404, detail="No hay datos de la última semana")
            log_to_opensearch(f"404  - No hay datos de la última semana",  "ERROR")                            
            
    except pybreaker.CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Servicio temporalmente fuera de servicio")
    except RetryError:
        raise HTTPException(status_code=502, detail="Servicio no responde. Vuelva a intentar.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error de conexión: {str(e)}")
    return {"average": avg}


# ---------------------------------------------------
# ENDPOINT PARA PROMETHEUS
# ---------------------------------------------------
@app.get("/metrics")
def metrics():
    """
    Punto de exposición para Prometheus.
    """
    log_to_opensearch(f"================ consulta metrics ==================",  "INFO")
    update_memory_metrics()
    update_disk_metrics()
    update_cpu_metrics()
    update_cpu_temperature()
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
