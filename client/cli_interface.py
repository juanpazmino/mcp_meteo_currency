import logging
from mcp import ClientSession
from client.openai_client import get_tools, llm_con_mcp

logger = logging.getLogger(__name__)

HELP_TEXT = """
Comandos disponibles:
  /ayuda    - Muestra esta ayuda
  /salir    - Sale del programa
  /monedas  - Lista los códigos de moneda más comunes

Ejemplos de consultas:
  ¿Cuál es el clima en Madrid?
  Convierte 100 USD a EUR
  Dame el pronóstico de Barcelona para 5 días
  ¿Cuál es la tasa de cambio del USD?
"""

COMMON_CURRENCIES = """
Monedas más comunes (código ISO 4217):
  USD - Dólar estadounidense   EUR - Euro
  GBP - Libra esterlina        JPY - Yen japonés
  CAD - Dólar canadiense       AUD - Dólar australiano
  CHF - Franco suizo           CNY - Yuan chino
  MXN - Peso mexicano          BRL - Real brasileño
  ARS - Peso argentino          COP - Peso colombiano

Puedes usar cualquier código de 3 letras (ej: USD, EUR, GBP).
"""


async def interactive_loop(session: ClientSession) -> None:
    """Bucle interactivo principal: lee consultas del usuario y devuelve respuestas del asistente."""
    print("\n=== Asistente de Clima y Divisas ===")
    print(" ")
    print("Escribe /ayuda para ver los comandos disponibles.\n")
    print("=" * 40)
    # Load available tools from the MCP server once at startup
    print("Conectando con el servidor MCP...", end="", flush=True)
    tools = await get_tools(session)
    print(f" listo ({len(tools)} herramientas)")

    while True:
        try:
            user_input = input("\nConsulta: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+C or piped input ending
            print("\nHasta luego.")
            break

        if not user_input:
            continue

        # --- Special slash commands ---
        if user_input.lower() == "/salir":
            print("Hasta luego.")
            break

        if user_input.lower() == "/ayuda":
            print(HELP_TEXT)
            continue

        if user_input.lower() == "/monedas":
            print(COMMON_CURRENCIES)
            continue

        if user_input.startswith("/"):
            print(f"Comando desconocido: '{user_input}'. Escribe /ayuda para ver los comandos.")
            continue

        # --- Normal LLM query ---
        print("Procesando...", end="", flush=True)
        try:
            respuesta = await llm_con_mcp(user_input, session, tools)
            print(f"\r{' ' * 14}\r")  # clear "Procesando..."
            print(f"\nAsistente:\n{respuesta}")
            print("-" * 40)
        except Exception as e:
            print(f"\rError: {e}")
            print("Intenta reformular tu consulta.")
            logger.error(f"Error en consulta: {e}")
