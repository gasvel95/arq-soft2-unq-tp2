# Trabajo práctico final


## Estrategias de tolerancia a fallos y monitoreo

- **Timeouts**: Se implementa mediante la librería **request**
Ej: El timeout para la llamada al servicio es de 10 segundos.
```python
response = requests.get(url, timeout=10)
```
- **Circuit Breaker**: Se implementa mediante la librería **pybreaker**
Ej: Si se superan 3 fallos, se abre el circuito y no intenta más durante 60 segundos.
```python
circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)
@circuit_breaker
```
- **Fallback**: Se implementa mediante la librería **tenacity**
Ej: Se reintenta en caso de excepción en el método y se deja de reintentar luego de 3 intentos
```python
@retry(wait=wait_fixed(5), stop=stop_after_attempt(3),retry=retry_if_exception_type(Exception))
```
## Obserbabilidad

Este proyecto configura un stack de monitoreo con **Prometheus**, **Grafana** y **Node Exporter**, para observar métricas personalizadas desde un microservicio FastAPI.

## Tests de carga

Se realizan tests de carga mediante **locust**. Se pueden observar los reportes en la carpeta **reports_locust**.

---

##  Requisitos

###  Sistema operativo
- macOS / Linux / Windows  

###  Docker
- [Docker Engine](https://docs.docker.com/get-docker/)
- Docker Compose

Verificar instalación:
```bash
docker --version
docker compose version
```

###  Ejecución

Sobre la raíz del proyecto
```bash
docker-compose up --build
```

Sobre la carpeta "observability" 
```bash
docker compose up -d
```

### Accesos
Locust: http://localhost:8089

Prometheus: http://localhost:9090

Grafana: http://localhost:3000

Usuario: admin

Contraseña: admin

#### Para ejecutar un ejemplo:

1. Tener corriendo los modulos principales
2. Ir a Grafana: http://localhost:3000

- Ir a Dashboards → Import

- Subir el archivo: examples/wheather-xxxxxxxx.json

- Asignar la fuente de datos: Prometheus

### Test de carga
Ingresar a http://localhost:8089. Ahí puede seleccionar la cantidad maxima de usuarios concurrentes , la cantidad de usuarios por segundo que se van sumando y el host (en el caso de correrlo de manera local http://localhost:8000).
Los resultados de las pruebas realizadas se encuentran en la carpeta **reports_locust**
