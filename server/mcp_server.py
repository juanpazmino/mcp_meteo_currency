import logging
from mcp.server.fastmcp import FastMCP
from server.currency_tools import convert_currency, get_exchange_rates
from server.weather_tools import get_current_weather, get_weather_forecast
from server.geocoding_tools import geocode_city
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Crea y configura el servidor FastMCP con las 5 herramientas disponibles."""
    mcp = FastMCP(
        "Weather and Exchange Server",
        host=settings.MCP_SERVER_HOST,
        port=settings.MCP_SERVER_PORT,
        instructions="""
        Servidor MCP con herramientas de clima y divisas.
        Flujo para clima: primero llama a geocode_city para obtener coordenadas,
        luego usa latitude y longitude del resultado en get_current_weather o get_weather_forecast.
        Herramientas: geocode_city, get_current_weather, get_weather_forecast,
                      get_exchange_rates, convert_currency.
        """,
    )

    # Register all 5 tools
    mcp.tool()(convert_currency)
    mcp.tool()(get_exchange_rates)
    mcp.tool()(geocode_city)
    mcp.tool()(get_current_weather)
    mcp.tool()(get_weather_forecast)

    logger.info(f"Servidor creado en {settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}")
    return mcp
