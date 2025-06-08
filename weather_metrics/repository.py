from pymongo import MongoClient
from config import CONFIG
import time

client = MongoClient(CONFIG["mongo_uri"])
collection = client[CONFIG["mongo_db"]][CONFIG["mongo_collection"]]

def get_latest():
    return collection.find().sort("timestamp", -1).limit(1)[0]

def avg_since(seconds):
    threshold = time.time() - seconds
    pipeline = [
        {"$match": {"timestamp": {"$gte": threshold}}},
        {"$group": {"_id": None, "avgTemp": {"$avg": "$temperature"}}}
    ]
    return list(collection.aggregate(pipeline))[0]["avgTemp"]

