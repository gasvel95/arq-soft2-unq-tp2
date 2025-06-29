import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "api_key": os.getenv("OPENWEATHER_API_KEY"),
    "mongo_uri": os.getenv("MONGO_URI"),
    "mongo_db": os.getenv("MONGO_DB", "weather"),
    "mongo_collection": os.getenv("MONGO_COLLECTION", "measurements"),
    "city": os.getenv("CITY", "Buenos Aires"),
    "interval_minutes": 15,
    "weatherstack_key": os.getenv("WEATHERSTACK_API_KEY")
}
