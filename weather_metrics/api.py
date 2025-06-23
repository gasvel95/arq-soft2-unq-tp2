# weather_metrics/api.py

import json
import time
import logging
from functools import wraps

from fastapi import FastAPI, HTTPException, Response
import pybreaker
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi_websocket_rpc import RpcMethodsBase, WebSocketRpcClient
import asyncio
from tenacity import RetryError, retry_if_exception_type, wait_fixed, stop_after_attempt


PORT = 8001

circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)


RETRY_CONFIG = {
    'wait':wait_fixed(5), 'stop':stop_after_attempt(3),'retry':retry_if_exception_type(Exception)
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

# ---------------------------------------------------
# MIDDLEWARE PARA INSTRUMENTACIÓN
# ---------------------------------------------------
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
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
    parsed_response = None
    try:
        doc = rpc_call_current()
        if not doc:
            raise HTTPException(status_code=404, detail="No hay datos de clima disponibles aún")
        json_acceptable_string = doc.replace("'", "\"")
        parsed_response = json.loads(json_acceptable_string)
    except pybreaker.CircuitBreakerError:
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
    avg = None
    try:
        avg = rpc_call_avg_day()
        if avg is None:
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
    avg = None
    try:
        avg = rpc_call_avg_week()
        if avg is None:
            raise HTTPException(status_code=404, detail="No hay datos de la última semana")
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
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
