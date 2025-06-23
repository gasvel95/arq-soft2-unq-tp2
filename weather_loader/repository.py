import logging
import time
from pymongo import MongoClient
from config import CONFIG
from logger import get_logger

logger = get_logger("Repository").setLevel(logging.WARN)

client = MongoClient(CONFIG["mongo_uri"])
db = client[CONFIG["mongo_db"]]
collection = db[CONFIG["mongo_collection"]]

def save_weather_data(data):
    collection.insert_one(data)
    logger.info(f"Saved weather data: {data}")

def get_latest():
    return collection.find().sort("timestamp", -1).limit(1)[0]

def avg_since(seconds):
    threshold = time.time() - seconds
    pipeline = [
        {"$match": {"timestamp": {"$gte": threshold}}},
        {"$group": {"_id": None, "avgTemp": {"$avg": "$temperature"}}}
    ]
    return list(collection.aggregate(pipeline))[0]["avgTemp"]