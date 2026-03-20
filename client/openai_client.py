import json
import logging
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from mcp import ClientSession
from config import settings

load_dotenv()
logger = logging.getLogger(__name__)

# URL where the MCP server is listening (set in .env or defaults to localhost:8000)
SERVER_URL = f"http://{settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}/sse"

client = AsyncAzureOpenAI()

SYSTEM_PROMPT = """
Eres un asistente experto en clima y divisas con acceso a 5 herramientas:

- geocode_city(city_name): Obtiene coordenadas, país y zona horaria de una ciudad.
  IMPORTANTE: Llama SIEMPRE a esta herramienta primero para obtener coordenadas.
  Usa los campos 'latitude' y 'longitude' del resultado en las herramientas de clima.
- get_current_weather(latitude, longitude): Temperatura, humedad y descripción del clima actual.
- get_weather_forecast(latitude, longitude, days): Pronóstico diario de temperatura máx/mín.
- get_exchange_rates(base_currency): Tasas de cambio de una moneda contra todas las demás.
- convert_currency(amount, from_currency, to_currency): Convierte entre dos monedas.

Responde siempre en el idioma del usuario. Usa las herramientas para dar información real y actualizada.
"""


async def get_tools(session: ClientSession) -> list[dict]:
    """Obtiene las herramientas MCP y las convierte al formato que espera la Responses API."""
    mcp_tools = await session.list_tools()
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        }
        for tool in mcp_tools.tools
    ]


async def call_mcp_tool(session: ClientSession, tool_name: str, tool_args: dict) -> str:
    """Llama a una herramienta MCP con hasta 3 intentos en caso de error."""
    logger.info(f"Herramienta: {tool_name}, args: {tool_args}")

    for attempt in range(1, 4):  # up to 3 attempts
        try:
            result = await session.call_tool(tool_name, tool_args)
            return result.content[0].text
        except Exception as e:
            logger.warning(f"Intento {attempt}/3 fallido para {tool_name}: {e}")
            if attempt == 3:
                raise  # re-raise after last attempt


async def llm_con_mcp(input_text: str, session: ClientSession, tools: list) -> str:
    """Bucle agéntico: envía la consulta al LLM y ejecuta herramientas hasta obtener respuesta final."""
    messages = [{"role": "user", "content": input_text}]

    response = await client.responses.create(
        model="gpt-4.1-mini",
        input=messages,
        instructions=SYSTEM_PROMPT,
        tools=tools,
    )

    # Keep going as long as the model wants to call tools
    while True:
        tool_calls = [item for item in response.output if item.type == "function_call"]
        if not tool_calls:
            break  # model produced a text response, we're done

        # Responses API: output items go directly into the input list, not nested as content
        messages.extend(response.output)

        for tool_call in tool_calls:
            tool_args = json.loads(tool_call.arguments)
            try:
                result = await call_mcp_tool(session, tool_call.name, tool_args)
            except Exception as e:
                # Pass error back to LLM so it can handle it gracefully
                result = f"Error al ejecutar {tool_call.name}: {str(e)}"
                logger.error(f"Herramienta falló: {e}")

            messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": result,
            })

        response = await client.responses.create(
            model="gpt-4.1-mini",
            input=messages,
            instructions=SYSTEM_PROMPT,
            tools=tools,
        )

    return response.output_text
