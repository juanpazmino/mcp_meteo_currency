import logging
import pandas as pd
from config import settings
from server.api_clients import setup_openmeteo_client

logger = logging.getLogger(__name__)

# One shared client instance with caching + retry (defined in api_clients.py)
openmeteo = setup_openmeteo_client()

# WMO weather code -> human-readable Spanish description (subset of most common codes)
WMO_DESCRIPTIONS = {
    0: "Despejado", 1: "Principalmente despejado", 2: "Parcialmente nublado",
    3: "Nublado", 45: "Niebla", 48: "Niebla con escarcha",
    51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna intensa",
    61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia intensa",
    71: "Nevada ligera", 73: "Nevada moderada", 75: "Nevada intensa",
    80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos violentos",
    95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta con granizo intenso",
}


def get_current_weather(latitude: float, longitude: float) -> dict:
    """Obtiene el clima actual (temperatura, humedad y descripcion) para unas coordenadas."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        # Request 3 variables at once; Variables(0)=temp, Variables(1)=humidity, Variables(2)=code
        "current": "temperature_2m,relative_humidity_2m,weather_code",
    }
    logger.info(f"Clima actual para ({latitude}, {longitude})")

    try:
        response = openmeteo.weather_api(settings.URL_WEATHER_API, params=params)[0]
    except Exception as e:
        logger.error(f"Error Open-Meteo: {e}")
        raise

    current = response.Current()
    weather_code = int(current.Variables(2).Value())

    return {
        "temperature_celsius": round(current.Variables(0).Value(), 1),
        "relative_humidity_percent": int(current.Variables(1).Value()),
        # Fall back to the raw code if not in the dict
        "weather_description": WMO_DESCRIPTIONS.get(weather_code, f"Codigo {weather_code}"),
    }


def get_weather_forecast(latitude: float, longitude: float, days: int = 7) -> list[dict]:
    """Obtiene el pronostico diario de temperatura maxima y minima para los proximos dias."""
    if not (1 <= days <= 16):
        raise ValueError(f"'days' debe estar entre 1 y 16, recibido: {days}")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": days,
    }
    logger.info(f"Pronostico {days} dias para ({latitude}, {longitude})")

    try:
        response = openmeteo.weather_api(settings.URL_WEATHER_API, params=params)[0]
    except Exception as e:
        logger.error(f"Error Open-Meteo: {e}")
        raise

    daily = response.Daily()
    temp_max = daily.Variables(0).ValuesAsNumpy()
    temp_min = daily.Variables(1).ValuesAsNumpy()
    n = len(temp_max)

    # Build date list from Unix timestamps
    start = daily.Time()
    step = daily.Interval()
    dates = pd.to_datetime([start + i * step for i in range(n)], unit="s", utc=True).tz_convert(None)

    return [
        {
            # Use str(date) to avoid non-JSON-serializable Timestamp objects
            "date": str(dates[i].date()),
            "temp_max_celsius": round(float(temp_max[i]), 1),
            "temp_min_celsius": round(float(temp_min[i]), 1),
        }
        for i in range(n)
    ]
