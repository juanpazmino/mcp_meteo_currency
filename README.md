# MCP Deliver

An LLM-powered assistant for weather and currency queries, built on the **Model Context Protocol (MCP)** over SSE transport. The server exposes 5 tools via FastMCP; the client connects an Azure OpenAI model (`gpt-4.1-mini`) to those tools through an agentic loop.

---

## Architecture

```
main_server.py
└── server/mcp_server.py        # create_server() builds the FastMCP instance
    ├── server/weather_tools.py     # get_current_weather, get_weather_forecast
    ├── server/geocoding_tools.py   # geocode_city
    ├── server/currency_tools.py    # convert_currency, get_exchange_rates
    └── server/api_clients.py       # Open-Meteo HTTP client (cache + retry)

main_client.py
└── client/openai_client.py     # SERVER_URL, get_tools(), call_mcp_tool(), llm_con_mcp()
    └── client/cli_interface.py     # interactive_loop() — reads input, calls llm_con_mcp

config/settings.py              # Reads env vars; exposes API base URLs and server host/port
```

The server and client run as **separate processes**. The server listens on `http://{host}:{port}/sse`; the client connects to that endpoint and drives an agentic loop until the model returns a final text response.

---

## Tools

| Tool | Description |
|---|---|
| `geocode_city(city_name)` | Returns latitude, longitude, country, and timezone for a city |
| `get_current_weather(latitude, longitude)` | Current temperature, humidity, and weather description |
| `get_weather_forecast(latitude, longitude, days)` | Daily max/min temperature forecast (1–16 days) |
| `get_exchange_rates(base_currency)` | All exchange rates for a given base currency |
| `convert_currency(amount, from_currency, to_currency)` | Converts an amount between two currencies |

> The LLM is instructed to always call `geocode_city` first to obtain coordinates before calling any weather tool.

---

## Prerequisites

- Python 3.12+
- An [ExchangeRate-API](https://exchangerate-api.com) key
- Azure OpenAI deployment with `gpt-4.1-mini` (or compatible model)

---

## Setup

**1. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies**

```bash
.venv/bin/pip install -r requirements.txt
```

**3. Configure environment variables**

```bash
cp env.example .env
```

Edit `.env` and fill in:

```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_API_VERSION=2024-12-01-preview
EXCHANGE_RATE_API_KEY=your_key_here
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
```

---

## Running

Start the server and client in **separate terminals**, in this order:

```bash
# Terminal 1 — MCP server (SSE transport on http://127.0.0.1:8000)
python main_server.py

# Terminal 2 — interactive client
python main_client.py
```

To run the MCP server as a standalone module (e.g. for debugging):

```bash
python -m server.mcp_server
```

> Always run from the project root. The server must be started with `-m server.mcp_server` (not `python server/mcp_server.py`) because the package uses relative imports.

---

## Usage

Once both processes are running, type natural-language queries at the `Consulta:` prompt:

```
Consulta: ¿Cuál es el clima en Madrid?
Consulta: Convierte 100 USD a EUR
Consulta: Dame el pronóstico de Barcelona para 5 días
Consulta: ¿Cuál es la tasa de cambio del USD?
```

**CLI commands:**

| Command | Action |
|---|---|
| `/ayuda` | Show available commands and example queries |
| `/monedas` | List common ISO 4217 currency codes |
| `/salir` | Exit the program |

---

## Design notes

- **SSE transport** — server and client are separate OS processes; the client connects via HTTP long-poll at `/sse`.
- **Response caching** — the Open-Meteo client uses `requests-cache` (SQLite, 1 h TTL, file `.cache.sqlite`) to avoid redundant API calls.
- **Tool retry** — `call_mcp_tool()` retries up to 3 times on failure before re-raising.
- **Agentic loop** — `llm_con_mcp()` uses the OpenAI Responses API; tool call outputs are appended directly to the `input` list as `function_call_output` items until the model returns plain text.
- **Async throughout** — `AsyncAzureOpenAI` is used for all LLM calls.
