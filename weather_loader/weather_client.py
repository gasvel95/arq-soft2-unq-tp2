import requests
from tenacity import retry, retry_if_exception_type, wait_fixed, stop_after_attempt
from config import CONFIG
from logger import get_logger
import pybreaker
from logging_ag import log_to_opensearch


logger = get_logger("WeatherClient")
circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)

@circuit_breaker
@retry(wait=wait_fixed(5), stop=stop_after_attempt(3),retry=retry_if_exception_type(Exception))
def fetch_weather():
    city = CONFIG["city"]
    api_key = CONFIG["api_key"]
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    logger.info(f"Fetched weather data for {city}: {data['main']}")
    log_to_opensearch(f"Fetched weather data for {city}: {data['main']}", "INFO")
    return {
        "city": city,
        "timestamp": data["dt"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"]
    }
