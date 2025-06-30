FROM python:3.10-slim

WORKDIR /locust

RUN pip install --no-cache-dir locust

COPY locustfile.py .

CMD ["locust", "-f", "locustfile.py"]
