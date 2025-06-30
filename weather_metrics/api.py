# weather_metrics/api.py

import time
import logging
from functools import wraps

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from hard_metrics.hardware import update_memory_metrics, update_cpu_metrics, update_disk_metrics, update_cpu_temperature 
from business_metrics.bussines_metrics import weather_average_day, weather_average_week, weather_current_temperature, weather_current_humidity, weather_current_pressure, weather_current_timestamp
from repository import get_latest, avg_since
from logging_ag import log_to_opensearch

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
    timestamp: float

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
    doc = get_latest()
    weather_current_temperature.set(doc["temperature"])
    weather_current_humidity.set(doc["humidity"])
    weather_current_pressure.set(doc["pressure"])
    weather_current_timestamp.set(doc["timestamp"])
    if not doc:
        log_to_opensearch(f"404  - No hay datos de clima disponibles aún",  "ERROR")            
        raise HTTPException(status_code=404, detail="No hay datos de clima disponibles aún")
    return {
        "temperature": doc["temperature"],
        "humidity": doc["humidity"],
        "pressure": doc["pressure"],
        "timestamp": doc["timestamp"],
    }

@app.get(
    "/weather/average/day",
    response_model=AverageResponse,
    summary="Promedio de temperatura últimas 24 horas",
    description="Devuelve la temperatura media del último día."
)
@ttl_cache(seconds=60)
def avg_day():
    log_to_opensearch(f"================ consulta avg_day ==================",  "INFO")
    avg = avg_since(24 * 3600)
    weather_average_day.set(avg)
    if avg is None:
        log_to_opensearch(f"404  - No hay datos de las últimas 24 horas",  "ERROR")                    
        raise HTTPException(status_code=404, detail="No hay datos de las últimas 24 horas")
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
    avg = avg_since(7 * 24 * 3600)
    weather_average_week.set(avg)
    if avg is None:
        log_to_opensearch(f"404  - No hay datos de la última semana",  "ERROR")                            
        raise HTTPException(status_code=404, detail="No hay datos de la última semana")
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
