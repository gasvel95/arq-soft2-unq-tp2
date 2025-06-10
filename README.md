# Trabajo práctico final


## Obserbailidad

Este proyecto configura un stack de monitoreo con **Prometheus**, **Grafana** y **Node Exporter**, para observar métricas personalizadas desde un microservicio FastAPI.

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

### Accesos

Prometheus: http://localhost:9090

Grafana: http://localhost:3000

Usuario: admin

Contraseña: admin

#### Para ejecutar un ejemplo:

1- Tener corriendo el modulo weather_loader
2- Tener corriendo el modulo weather_metrics

3- Ir a Grafana: http://localhost:3000

- Ir a Dashboards → Import

- Subir el archivo: examples/wheather-xxxxxxxx.json

- Asignar la fuente de datos: Prometheus
