import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

def geocode_city(city_name: str) -> dict:
    """Obtiene la latitud, longitud, pais y zona horaria de una ciudad por su nombre."""
    city_name = city_name.strip()
    if not city_name:
        raise ValueError("El nombre de la ciudad no puede estar vacio.")

    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    logger.info(f"Geocodificando: {city_name}")

    try:
        response = requests.get(settings.URL_OPEN_METEO_API, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout geocodificando '{city_name}'")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error HTTP: {e}")
        raise

    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"Ciudad '{city_name}' no encontrada.")

    # The API returns all fields we need in results[0]
    r = results[0]
    logger.info(f"Encontrado: ({r['latitude']}, {r['longitude']}), {r.get('country')}")

    return {
        "latitude": r["latitude"],
        "longitude": r["longitude"],
        "country": r.get("country", "Desconocido"),
        "timezone": r.get("timezone", "UTC"),
    }
