from dotenv import load_dotenv
import os
load_dotenv()


URL_CURRENCY_API = f"https://v6.exchangerate-api.com/v6/{os.getenv('EXCHANGE_RATE_API_KEY')}/pair"
URL_CURRENCY_LATEST = f"https://v6.exchangerate-api.com/v6/{os.getenv('EXCHANGE_RATE_API_KEY')}/latest"

URL_OPEN_METEO_API = "https://geocoding-api.open-meteo.com/v1/search"
URL_WEATHER_API = "https://api.open-meteo.com/v1/forecast"

MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))