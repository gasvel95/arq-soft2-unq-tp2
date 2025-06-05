from pymongo import MongoClient
from config import CONFIG
from logger import get_logger

logger = get_logger("Repository")

client = MongoClient(CONFIG["mongo_uri"])
db = client[CONFIG["mongo_db"]]
collection = db[CONFIG["mongo_collection"]]

def save_weather_data(data):
    collection.insert_one(data)
    logger.info(f"Saved weather data: {data}")
