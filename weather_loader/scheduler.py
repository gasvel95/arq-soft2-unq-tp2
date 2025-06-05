import schedule
import time
from weather_client import fetch_weather
from repository import save_weather_data
from config import CONFIG
from logger import get_logger

logger = get_logger("Scheduler")

def job():
    try:
        data = fetch_weather()
        save_weather_data(data)
    except Exception as e:
        logger.error(f"Failed to load weather data: {e}")

def start():
    interval = CONFIG["interval_minutes"]
    schedule.every(interval).minutes.do(job)
    logger.info(f"Scheduler started. Running every {interval} minutes.")

    while True:
        schedule.run_pending()
        time.sleep(1)
