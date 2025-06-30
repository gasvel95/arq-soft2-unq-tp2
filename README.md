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

Previo a esto es necesario generar una red para que los contenedores corran sobre una misma red para esto ejecutar:



Sobre la raíz del proyecto
```bash
docker network create monitoring

```
monitoring: red ya configurada en los archivos docker-compose.yaml


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

1- Tener corriendo el modulo weather_loader
2- Tener corriendo el modulo weather_metrics

1. Tener corriendo los modulos principales
2. Ir a Grafana: http://localhost:3000
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


### Test de carga
Ingresar a http://localhost:8089. Ahí puede seleccionar la cantidad maxima de usuarios concurrentes , la cantidad de usuarios por segundo que se van sumando y el host (en el caso de correrlo de manera local http://localhost:8000).
Los resultados de las pruebas realizadas se encuentran en la carpeta **reports_locust**

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


Crear Alertas con OpenSearch: 

Primero vamos a crear un **canal** , lo que nos va a permitir enviar las alertas. Para eso ingresamos a: 

http://localhost:5601/app/notifications-dashboards#/channels


1. Ingresamos el nombre del canal, en este caso: "Slack - CH"
2. Seleccionamos el tipo de canal: "Slack"
3. Agregamos un Hook previamente creado en integracion con Slack para que se envien las alertas como mensaje a un canal: https://hooks.slack.com/services/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

![Channel](/images/channel_slack.png)

Una vez creado el canal vamos a proceder a crear el **Monitor**: 

Para eso: 

Ingresar a  http://localhost:5601/app/alerting#/create-monitor 



1. Ingresar nombre del monitor, ej: Error Weather Logs
2. Seleccionar Tipo de monitor: Per Query monitor
3. Seleccioar el método de definición de monitor: Extraction Query editor.
4. Seleccionar la frecuencia, para el ejemplo: By interval
5. Seleccionar el intervalo de ejecucion: cada 10 minutos.

![crear Monitor](/images/moni_1.png)

6. Seleccion el indice ya creado: weather_logs
7. Ingresar la query que vamos a utilzar en este caso: 

```json
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "level": "error"  
          }
        },
        {
          "range": {
            "timestamp": {
              "gte": "now-5m/m",  
              "lte": "now/m"        
            }
          }
        }
      ]
    }
  }
}
```
Nos permitira filtrar los casos que sean level=ERROR y que se hayan dado dentro de los 5 minutos anteriores a la ejecucion. 

8. Podemos ejecutar con la opcion "run" para verificar si la query es correcta y si ademas nos trae resultados. 
En la imagen ejemplo en el json: hits-> total -> value: 13 indica que se dieron 13 errores en los ultimos 5 minutos. 

![crear Monitor](/images/moni_2.png)

9. Agregamos un Trigger, lo que nos permitira ejecutar las alertas. 

![crear Monitor](/images/moni_3.png)

10. Ingresamos el Trigger Name: count_error

11. En Severity Level, seleccionamos 1 Highest, dado a que son alertas de errores.  En el caso de Trigger condition podemos dejar el campo como esta o ajustarlo, por ej: ctx.results[0].hits.total.value > 2

12. Podemos validar el triger si se esta cumpliendo la condicion.  

![crear Monitor](/images/moni_4.png)

* vamos a la seccion de Actions: 

13. Agregamos el Action Name: ERROR Log 

14. Seleccionamos el canal previamente creado: Slack - CH

15. Podemos validar el funcionamiento del canal y el envio de la alerta. 

![crear Monitor](/images/moni_5.png)

16. Finalmente le damos a "Create"


![crear Monitor](/images/moni_6.png)

Posteriormente podemos ya ver en funcionamiento el Monitor con las alertas generadas hasta el momento actual. 

![crear Monitor](/images/moni_7.png)
