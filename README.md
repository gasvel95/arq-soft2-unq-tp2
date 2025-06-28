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

Sobre la carpeta "observability" 
```bash
docker compose up -d
```

## Metricas - Accesos

Prometheus: http://localhost:9090

Grafana: http://localhost:3000

Usuario: admin

Contraseña: admin


Se genero un Dashboard Gafaga, con las diferentes metricas, con 3 tipos de metricas:

### Metricas de negocio

![Metricas de Negocio](/images/gafana_business_metric.png)

* Tempreatura Actual
* Presión Atmosférica
* % de Humedad Actual
* Temperatura promedio del dia
* Temperatura promedio semanal


### Metricas de Hardware:

![Metricas de Hardware](/images/gafana_hardware_metric.png)

* % de uso de CPU x Core
* Memoria Libre
* % de uso de Disco

### Metricas de Api:

![Metricas de Api](/images/gafana_api_metric.png)

 * /weather/current
    * % Error
    * % Ok

*  /weather/average/day
    * % Error
    * % Ok

* /weather/average/week
    * % Error
    * % Ok


#### Para ejecutar un ejemplo:

1- Tener corriendo el modulo weather_loader
2- Tener corriendo el modulo weather_metrics

3- Ir a Grafana: http://localhost:3000

- Ir a Dashboards → Import

- Subir el archivo: examples/wheather-xxxxxxxx.json

- Asignar la fuente de datos: Prometheus

## NOTA: 
    en caso de tener que resetear la password:

Verificar container de docker

```bash
docker ps
```

Seleccionar el container de Gafana
```bash
CONTAINER ID   IMAGE                COMMAND                  CREATED       STATUS       PORTS                    NAMES
f2e312a45b8d   grafana/grafana      "/run.sh"                12 days ago   Up 2 hours   0.0.0.0:3000->3000/tcp   observability-grafana-1
d36a1dfdac7d   prom/prometheus      "/bin/prometheus --c…"   12 days ago   Up 2 hours   0.0.0.0:9090->9090/tcp   observability-prometheus-1
b28b98a06e60   prom/node-exporter   "/bin/node_exporter"     12 days ago   Up 2 hours   0.0.0.0:9100->9100/tcp   observability-node_exporter-1
```

y ejecutar el siguiente comando con la nueva password elegida, en este caso "pepe":

```bash
docker exec -ti f2e312a45b8d grafana cli admin reset-admin-password pepe
```


## Logs Aggregation -> OpenSearch

Antes una vez que se levanta va a estar via docker compose: /observability/docker_compose.yaml

Ejecutar el siguiente comando: 

```bash
curl -u elastic:Mercado2255$ -X PUT "http://localhost:9200/weather_logs"
```
Esto va a generar un indice, dentro de openSearch  los índices son estructuras clave para almacenar y organizar los datos de manera eficiente. Los índices son esenciales para las operaciones de búsqueda y análisis de grandes volúmenes de datos.

### Viualizacion de logs: 

* Acceder a OpenSearch Dashboards en http://localhost:5601.

    * En el menú de la izquierda, seleccionar Discover. Este es el lugar donde podrás buscar e interactuar con los índices que contienen los logs.

    * Seleccionar el índice 'weather_logs' desde el menú desplegable de índice en la parte superior de la pantalla de Discover.


![Dashboards](/images/open_search_dashboard_view.png)

