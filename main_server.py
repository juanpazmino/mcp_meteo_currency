import logging
from server.mcp_server import create_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

if __name__ == "__main__":
    server = create_server()
    # SSE transport exposes GET /sse and POST /messages/
    server.run(transport="sse")
