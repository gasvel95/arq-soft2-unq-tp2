# weather_metrics/api.py

import logging

from fastapi import FastAPI
from repository import get_latest, avg_since
from fastapi_websocket_rpc import RpcMethodsBase, WebsocketRPCEndpoint
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from weather_client import fetch_weather
from repository import save_weather_data
from config import CONFIG
from logger import get_logger

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    level=logging.WARN
)
logger = get_logger("Scheduler")

def job():
    try:
        data = fetch_weather()
        save_weather_data(data)
    except Exception as e:
        logger.error(f"Failed to load weather data: {e}")

@asynccontextmanager
async def lifespan(app:FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(job,"interval",minutes = CONFIG["interval_minutes"])
    scheduler.start()
    yield

app = FastAPI(lifespan=lifespan)


class WeatherServer(RpcMethodsBase):
    async def getCurrent(self):
        latest = get_latest()
        print(latest['city'])
        return {
        "temperature": latest['temperature'],
        "humidity": latest['humidity'],
        "pressure": latest['pressure'],
        "timestamp": latest['timestamp']
    }
    
    async def avgDay(self):
        return avg_since(24 * 3600)
    
    async def avgWeek(self):
        return avg_since(7 * 24 * 3600)


endpoint = WebsocketRPCEndpoint(WeatherServer())
endpoint.register_route(app, "/ws")
    
