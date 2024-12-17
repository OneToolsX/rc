import asyncio
import json
from websockets.server import serve
from utils.logger import setup_logger


class RemoteControlServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = {}
        self.command_futures = {}

        self.logger = setup_logger("rc_server", "server.log")
        self.logger.info(f"Server initialized on {host}:{port}")

    async def list_clients(self):
        """Return list of connected clients"""
        return [
            {"id": client_id, "info": info["client_info"]}
            for client_id, info in self.clients.items()
        ]

    async def handle_commands(self, client_id, command):
        """Send command to specific client"""
        if client_id not in self.clients:
            self.logger.error(f"Client {client_id} not found")
            raise ValueError(f"Client {client_id} not found")

        websocket = self.clients[client_id]["websocket"]
        self.logger.debug(f"Sending command to client {client_id}: {command}")

        future = asyncio.Future()
        command_id = len(self.command_futures)
        self.command_futures[command_id] = future

        await websocket.send(
            json.dumps({"type": "command", "data": command, "id": command_id})
        )

        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            self.logger.debug(f"Command result received: {result}")
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"Command timeout: {command}")
            raise
        finally:
            self.command_futures.pop(command_id, None)

    async def handle_client(self, websocket, path):
        try:
            # Wait for client identification
            init_message = await websocket.recv()
            client_data = json.loads(init_message)
            client_id = client_data.get("client_id")
            client_info = client_data.get("client_info", {})

            self.logger.info(
                f"New client connected - ID: {client_id}, Info: {client_info}"
            )
            self.clients[client_id] = {
                "websocket": websocket,
                "client_info": client_info,
            }

            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "command_result":
                    self.logger.info(
                        f"Command result from client {client_id}: {data['data']}"
                    )
                    if "id" in data:
                        future = self.command_futures.get(data["id"])
                        if future and not future.done():
                            future.set_result(data["data"])
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {str(e)}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            self.logger.info(f"Client disconnected: {client_id}")

    async def start(self):
        self.logger.info("Starting server...")
        self.server = await serve(self.handle_client, self.host, self.port)
        self.logger.info(f"Server running on ws://{self.host}:{self.port}")
        await self.server.wait_closed()


if __name__ == "__main__":
    server = RemoteControlServer()
    asyncio.run(server.start())
