import asyncio
import json
from websockets.server import serve


class RemoteControlServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()

    async def handle_commands(self, websocket, command):
        """Send a single command to the client"""
        await websocket.send(json.dumps({"type": "command", "data": command}))

    async def interactive_command_loop(self, websocket):
        """Handle interactive command input"""
        while True:
            command = await asyncio.get_event_loop().run_in_executor(
                None, input, "Enter command to execute (or 'quit' to exit): "
            )
            if command.lower() == "quit":
                break
            await self.handle_commands(websocket, command)

    async def handle_client(self, websocket, path):
        self.clients.add(websocket)
        try:
            # Start command input task
            command_task = asyncio.create_task(self.interactive_command_loop(websocket))

            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "system_info":
                    print(f"System info: {data['data']}")
                elif data.get("type") == "command_result":
                    print(f"Command result: {data['data']}")
        finally:
            self.clients.remove(websocket)
            command_task.cancel()

    async def start(self):
        server = await serve(self.handle_client, self.host, self.port)
        print(f"Server running on ws://{self.host}:{self.port}")
        await server.wait_closed()


if __name__ == "__main__":
    server = RemoteControlServer()
    asyncio.run(server.start())
