# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the project

The server and client are **two separate processes** — start them in this order:

```bash
# 1. Start the MCP server (SSE transport, listens on http://127.0.0.1:8000)
python main_server.py

# 2. In a second terminal, run the client
python main_client.py

# Run the MCP server standalone with the module flag (for debugging)
python -m server.mcp_server
```

Always run from the project root. The server must be started with `-m server.mcp_server`, not `python server/mcp_server.py`, because the package uses relative imports.

## Architecture

This project connects an LLM (Azure OpenAI) to external APIs via the **Model Context Protocol (MCP)** over **SSE (HTTP) transport**.

```
main_server.py
  └── server/mcp_server.py   → create_server() builds the FastMCP instance
        └── server/currency_tools.py    → convert_currency, get_exchange_rates
        └── server/weather_tools.py     → get_current_weather, get_weather_forecast
        └── server/geocoding_tools.py   → geocode_city
        └── server/api_clients.py       → Open-Meteo HTTP client (cache + retry)
        └── runs SSE transport on host:port from settings

main_client.py
  └── connects to MCP server via SSE at http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/sse
  └── client/openai_client.py   → SERVER_URL, get_tools(), call_mcp_tool(), llm_con_mcp()
  └── client/cli_interface.py   → interactive_loop() — reads user input, calls llm_con_mcp
```

**Server side** (`server/`): FastMCP server exposing 5 tools — `geocode_city`, `get_current_weather`, `get_weather_forecast`, `get_exchange_rates`, `convert_currency`. Tools are defined in separate modules and registered in `mcp_server.py` via `mcp.tool()()`. External calls go through `api_clients.py` (Open-Meteo with cache/retry) and direct `requests` calls to ExchangeRate-API.

**Client side** (`client/`): `openai_client.py` holds `SERVER_URL`, `get_tools()`, `call_mcp_tool()`, and `llm_con_mcp()` (the agentic loop). `cli_interface.py` holds `interactive_loop()` which reads user queries and delegates to `llm_con_mcp`. The LLM used is `gpt-4.1-mini` via the OpenAI **Responses API** (`client.responses.create`).

**Config** (`config/settings.py`): Reads API base URLs and server host/port. `EXCHANGE_RATE_API_KEY` must be set in `.env`.

## Environment variables

Copy `env.example` and fill in:
- `EXCHANGE_RATE_API_KEY` — from [exchangerate-api.com](https://exchangerate-api.com)
- `MCP_SERVER_HOST` — defaults to `127.0.0.1`
- `MCP_SERVER_PORT` — defaults to `8000`
- Azure OpenAI vars expected by `AsyncAzureOpenAI()`: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `OPENAI_API_VERSION`

## Key design decisions

- The MCP server runs SSE transport (HTTP) — client and server are separate processes. The client connects to `http://{host}:{port}/sse`.
- The Open-Meteo client uses `requests_cache` (SQLite, 1h TTL, file `.cache.sqlite`) to avoid redundant API calls.
- Weather tools require lat/lon; the LLM is expected to call `geocode_city` first before calling `get_current_weather` or `get_weather_forecast`.
- `call_mcp_tool()` retries up to 3 times on failure before re-raising the exception.
- The agentic loop (`llm_con_mcp`) uses the OpenAI Responses API: tool call outputs are appended directly to the `input` list as `function_call_output` items until the model returns a plain text response.
- `AsyncAzureOpenAI` is used correctly throughout — all LLM calls are truly async.
