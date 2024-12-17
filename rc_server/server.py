import asyncio
import json
from websockets.server import serve
from utils.logger import setup_logger

class RemoteControlServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.command_futures = {}
        self.logger = setup_logger('rc_server', 'server.log')
        self.logger.info(f"Server initialized on {host}:{port}")

    async def handle_commands(self, websocket, command):
        self.logger.debug(f"Sending command: {command}")
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
        client_id = id(websocket)
        self.logger.info(f"New client connected: {client_id}")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "command_result":
                    self.logger.info(f"Command result from client {client_id}: {data['data']}")
                    print(f"Command result: {data['data']}")
                    if "id" in data:
                        future = self.command_futures.get(data["id"])
                        if future and not future.done():
                            future.set_result(data["data"])
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {str(e)}")
        finally:
            self.logger.info(f"Client disconnected: {client_id}")
            self.clients.remove(websocket)

    async def start(self):
        self.logger.info("Starting server...")
        self.server = await serve(self.handle_client, self.host, self.port)
        print(f"Server running on ws://{self.host}:{self.port}")
        await self.server.wait_closed()
