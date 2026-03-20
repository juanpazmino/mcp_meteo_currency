import asyncio
import logging
from mcp import ClientSession
from mcp.client.sse import sse_client
from client.openai_client import SERVER_URL
from client.cli_interface import interactive_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


async def main():
    """Conecta al servidor MCP vía SSE y lanza el bucle interactivo."""
    try:
        async with sse_client(SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await interactive_loop(session)
    except ConnectionRefusedError:
        # Server is not running
        print(f"\nNo se puede conectar al servidor en {SERVER_URL}")
        print("Asegúrate de que el servidor está corriendo: python main_server.py")
    except Exception as e:
        print(f"\nError inesperado: {e}")


if __name__ == "__main__":
    asyncio.run(main())
