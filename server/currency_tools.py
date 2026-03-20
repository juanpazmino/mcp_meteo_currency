import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convierte una cantidad de una moneda a otra usando la tasa de cambio actual."""
    # Basic input validation
    if amount <= 0:
        raise ValueError(f"El monto debe ser positivo, recibido: {amount}")
    from_currency = from_currency.strip().upper()
    to_currency = to_currency.strip().upper()

    url = f"{settings.URL_CURRENCY_API}/{from_currency}/{to_currency}"
    logger.info(f"Convirtiendo {amount} {from_currency} -> {to_currency}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout al conectar con la API de divisas")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error HTTP: {e}")
        raise

    data = response.json()
    if data.get("result") != "success":
        raise ValueError(f"Error de la API: {data.get('error-type', 'desconocido')}")

    exchange_rate = data["conversion_rate"]
    converted_amount = round(amount * exchange_rate, 4)
    logger.info(f"Resultado: {converted_amount} {to_currency}")

    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "exchange_rate": exchange_rate,
        "converted_amount": converted_amount,
    }


def get_exchange_rates(base_currency: str) -> dict:
    """Obtiene las tasas de cambio actuales para una moneda base contra todas las demas monedas."""
    base_currency = base_currency.strip().upper()

    # Uses /latest/ endpoint (different from /pair/ used by convert_currency)
    url = f"{settings.URL_CURRENCY_LATEST}/{base_currency}"
    logger.info(f"Obteniendo tasas para base: {base_currency}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout al conectar con la API de divisas")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error HTTP: {e}")
        raise

    data = response.json()
    if data.get("result") != "success":
        raise ValueError(f"Error de la API: {data.get('error-type', 'desconocido')}")

    return {
        "base_currency": base_currency,
        "last_updated": data.get("time_last_update_utc", "desconocido"),
        "rates": data.get("conversion_rates", {}),
    }
