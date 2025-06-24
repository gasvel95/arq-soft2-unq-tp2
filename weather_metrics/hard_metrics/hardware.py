import psutil
from prometheus_client import Gauge

# Métrica para el uso de la memoria
memory_usage = Gauge('memory_usage_percentage', 'Uso total de la memoria en porcentaje')
# Métrica para la memoria libre
memory_free = Gauge('memory_free_bytes', 'Memoria libre en bytes')

# Función para actualizar las métricas de memoria
def update_memory_metrics():
    memory_info = psutil.virtual_memory()
    memory_usage.set(memory_info.percent)
    memory_free.set(memory_info.available)
############################################################################################################################################
############################################################################################################################################

# Métrica para el uso total de CPU
cpu_usage = Gauge('cpu_usage_percentage', 'Uso total de la CPU en porcentaje')

# Métrica para el uso de cada núcleo de la CPU
cpu_per_core_usage = Gauge('cpu_per_core_usage_percentage', 'Uso de cada núcleo de la CPU en porcentaje', ['core'])

# Función para actualizar las métricas de CPU
def update_cpu_metrics():
    # Uso total de la CPU
    cpu_usage.set(psutil.cpu_percent(interval=1))
    
    # Uso por cada núcleo de la CPU
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        cpu_per_core_usage.labels(core=f'core_{i}').set(percentage)

############################################################################################################################################
############################################################################################################################################

# Métrica para el uso del disco
disk_usage = Gauge('disk_usage_percentage', 'Uso total del disco en porcentaje')

# Métrica para el espacio libre en el disco
disk_free = Gauge('disk_free_bytes', 'Espacio libre en el disco en bytes')

# Función para actualizar las métricas de disco
def update_disk_metrics():
    disk_info = psutil.disk_usage('/')
    disk_usage.set(disk_info.percent)
    disk_free.set(disk_info.free)
############################################################################################################################################
############################################################################################################################################

# Métrica para la temperatura del CPU (si está disponible)
cpu_temp = Gauge('cpu_temperature_celsius', 'Temperatura del CPU en grados Celsius')

# Función para actualizar las métricas de temperatura
def update_cpu_temperature():
    try:
        temp = psutil.sensors_temperatures()
        if 'coretemp' in temp:
            cpu_temp.set(temp['coretemp'][0].current)  # Esto puede variar dependiendo del sistema
    except Exception as e:
        pass  # Si no está disponible, ignora el error

############################################################################################################################################
############################################################################################################################################
