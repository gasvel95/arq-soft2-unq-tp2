from api import app
import uvicorn


def run_server():
    uvicorn.run(app,host="0.0.0.0",port=8001)


if __name__ == "__main__":
    run_server()
    
