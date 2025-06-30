import schedule
import time
from weather_client import fetch_weather
from repository import save_weather_data
from config import CONFIG
from logger import get_logger
from logging_ag import log_to_opensearch

logger = get_logger("Scheduler")

def job():
    try:
        data = fetch_weather()
        save_weather_data(data)
    except Exception as e:
        logger.error(f"Failed to load weather data: {e}")
        log_to_opensearch(f"Failed to load weather data: {e}", "ERROR")

def start():
    interval = CONFIG["interval_minutes"]
    schedule.every(interval).minutes.do(job)
    logger.info(f"Scheduler started. Running every {interval} minutes.")
    log_to_opensearch(f"Scheduler started. Running every {interval} minutes.", "INFO")


    while True:
        schedule.run_pending()
        time.sleep(1)
