import sys
import requests
import pytest
import uvicorn
from multiprocessing import Process
sys.path.insert(0, './weather_loader')
from weather_loader.api  import WeatherServer
from weather_loader.api  import app as app_loader
sys.path.insert(0, './weather_metrics')
import weather_metrics.api
from weather_metrics.api import app as app_metrics
from fastapi_websocket_rpc import  WebsocketRPCEndpoint

URL_LOADER = "http://localhost:8001"
URL_METRICS = "http://localhost:8000"

#Setup 2 modules servers
def run_server1(monkeypatch):
    monkeypatch.setattr(weather_metrics.api, "HOST", "localhost")

    uvicorn.run(app_metrics,host="localhost",port=8000)

def run_server2():
    endpoint = WebsocketRPCEndpoint(WeatherServer())
    endpoint.register_route(app_loader, "/ws")
    uvicorn.run(app_loader,host="localhost",port=8001)



# Start servers in different process
@pytest.fixture
def server(monkeypatch):
    proc = Process(target=run_server1, args=[monkeypatch], daemon=True)
    proc.start()
    proc2 =Process(target=run_server2, args=(), daemon=True)
    proc2.start()
    yield proc,proc2
    proc.kill() 
    proc2.kill() 

@pytest.fixture
def server_only_one(monkeypatch):
    proc = Process(target=run_server1, args=[monkeypatch], daemon=True)
    proc.start()
    yield proc
    proc.kill() 

@pytest.mark.asyncio
def test_current_weather(server):
    response = requests.get(url= URL_METRICS + "/weather/current")
    assert response.status_code == 200

@pytest.mark.asyncio
def test_avg_day(server):
    response = requests.get(url= URL_METRICS + "/weather/average/day")
    assert response.status_code == 200

@pytest.mark.asyncio
def test_avg_week(server):
    response = requests.get(url= URL_METRICS + "/weather/average/week")
    assert response.status_code == 200

@pytest.mark.asyncio
def test_current_weather_fails(server_only_one):
    response = requests.get(url= URL_METRICS + "/weather/current")
    assert response.status_code == 502

@pytest.mark.asyncio
def test_avg_day_fails(server_only_one):
    response = requests.get(url= URL_METRICS + "/weather/average/day")
    assert response.status_code == 502

@pytest.mark.asyncio
def test_avg_day_fails_CB(server_only_one):
    response = requests.get(url= URL_METRICS + "/weather/average/day")
    assert response.status_code == 502
    response = requests.get(url= URL_METRICS + "/weather/average/day")
    assert response.status_code == 503


@pytest.mark.asyncio
def test_avg_week_fails(server_only_one):
    response = requests.get(url= URL_METRICS + "/weather/average/week")
    assert response.status_code == 502

@pytest.mark.asyncio
def test_avg_week_fails_CB(server_only_one):
    response = requests.get(url= URL_METRICS + "/weather/average/week")
    assert response.status_code == 502
    response = requests.get(url= URL_METRICS + "/weather/average/week")
    assert response.status_code == 503