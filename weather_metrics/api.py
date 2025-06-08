from fastapi import FastAPI
from repository import get_latest, avg_since

app = FastAPI()

@app.get("/weather/current")
def current():
    doc = get_latest()
    return {"temperature": doc["temperature"], "timestamp": doc["timestamp"]}

@app.get("/weather/average/day")
def avg_day():
    return {"average": avg_since(24*3600)}

@app.get("/weather/average/week")
def avg_week():
    return {"average": avg_since(7*24*3600)}

