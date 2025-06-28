from prometheus_client import Gauge

weather_average_day = Gauge('weather_average_temperature_day', 'Promedio de la temperatura diaria en grados Celsius')

weather_average_week = Gauge('weather_average_temperature_week', 'Promedio de la temperatura semanal en grados Celsius')

# Métrica para la temperatura actual
weather_current_temperature = Gauge('weather_current_temperature', 'Temperatura actual en grados Celsius')

# Métrica para la humedad actual
weather_current_humidity = Gauge('weather_current_humidity', 'Humedad actual en porcentaje')

# Métrica para la presión actual
weather_current_pressure = Gauge('weather_current_pressure', 'Presión actual en hPa')

# Métrica para el timestamp
weather_current_timestamp = Gauge('weather_current_timestamp', 'Timestamp de la medición actual')


