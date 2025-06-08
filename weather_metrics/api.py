import time
from functools import wraps
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from repository import get_latest, avg_since

def ttl_cache(seconds: int):
    cache = {}
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            entry = cache.get(key)
            if entry:
                result, ts = entry
                if time.time() - ts < seconds:
                    print(f"CACHE HIT {func.__name__} args={key}")
                    return result
            # si llegamos acá, es cache miss
            print(f"CACHE MISS {func.__name__} args={key}")
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator

app = FastAPI(
    title="Weather Metrics API",
    version="1.0.0",
    description="API para consultar métricas de temperatura basadas en datos recolectados semanalmente."
)

class CurrentResponse(BaseModel):
    temperature: float
    humidity: int
    pressure: int
    timestamp: float

class AverageResponse(BaseModel):
    average: float

@app.get(
    "/weather/current",
    response_model=CurrentResponse,
    summary="Temperatura actual",
    description="Devuelve la última medición de temperatura, humedad y presión."
)
def current():
    doc = get_latest()
    if not doc:
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
    description="Devuelve la temperatura media de las mediciones del último día."
)
@ttl_cache(seconds=60)  # cache de 1 minuto
def avg_day():
    avg = avg_since(24 * 3600)
    if avg is None:
        raise HTTPException(status_code=404, detail="No hay datos de las últimas 24 horas")
    return {"average": avg}

@app.get(
    "/weather/average/week",
    response_model=AverageResponse,
    summary="Promedio de temperatura última semana",
    description="Devuelve la temperatura media de las mediciones de los últimos 7 días."
)
@ttl_cache(seconds=300)  # cache de 5 minutos
def avg_week():
    avg = avg_since(7 * 24 * 3600)
    if avg is None:
        raise HTTPException(status_code=404, detail="No hay datos de la última semana")
    return {"average": avg}