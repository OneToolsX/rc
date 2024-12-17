import asyncio
import json
import subprocess
import websockets.client
from websockets.exceptions import ConnectionClosed, WebSocketException
from utils.logger import setup_logger
import uuid
import platform
import socket
import asyncio
import argparse
import signal


class RemoteControlClient:
    def __init__(
        self, server_url="ws://localhost:8765", client_id=None, retry_interval=5
    ):
        self.server_url = server_url
        self.client_id = client_id or str(uuid.uuid4())
        self.client_info = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }
        self.logger = setup_logger("rc_client", "client.log")
        self.logger.info(f"Client initialized with server URL: {server_url}")
        self.retry_interval = retry_interval
        self.running = True

    async def execute_command(self, command):
        self.logger.debug(f"Executing command: {command}")
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            self.logger.debug(
                f"Command result: stdout={stdout}, stderr={stderr}, rc={process.returncode}"
            )
            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode,
            }
        except Exception as e:
            self.logger.error(f"Command execution error: {str(e)}")
            return {"error": str(e)}

    async def connect_to_server(self):
        """Attempt to connect to server with infinite retry"""
        while self.running:
            try:
                async with websockets.client.connect(self.server_url) as websocket:
                    self.logger.info(f"Connected to server: {self.server_url}")
                    await self.handle_connection(websocket)
            except (ConnectionRefusedError, ConnectionClosed, WebSocketException) as e:
                self.logger.error(f"Connection failed: {str(e)}")
                self.logger.info(f"Retrying in {self.retry_interval} seconds...")
                await asyncio.sleep(self.retry_interval)
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                await asyncio.sleep(self.retry_interval)

    async def handle_connection(self, websocket):
        """Handle the websocket connection and message processing"""
        try:
            # Send client identification
            await websocket.send(
                json.dumps(
                    {"client_id": self.client_id, "client_info": self.client_info}
                )
            )
            self.logger.info(f"Registered with server using ID: {self.client_id}")

            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "command":
                    self.logger.info(f"Received command: {data['data']}")
                    result = await self.execute_command(data["data"])
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "command_result",
                                "data": result,
                                "id": data.get("id"),
                            }
                        )
                    )
        except Exception as e:
            self.logger.error(f"Error in connection: {str(e)}")
            raise

    async def start(self):
        """Start the client with automatic reconnection"""
        self.logger.info("Starting client with auto-reconnection...")
        self.running = True
        await self.connect_to_server()

    async def stop(self):
        """Stop the client and prevent reconnection"""
        self.logger.info("Stopping client...")
        self.running = False


def parse_args():
    parser = argparse.ArgumentParser(description="Remote Control Client")
    parser.add_argument(
        "--server",
        default="ws://localhost:8765",
        help="WebSocket server URL (default: ws://localhost:8765)",
    )
    parser.add_argument("--id", help="Client ID (optional)")
    parser.add_argument(
        "--retry", type=int, default=5, help="Retry interval in seconds (default: 5)"
    )
    return parser.parse_args()


async def main_async():
    args = parse_args()
    client = RemoteControlClient(
        server_url=args.server, client_id=args.id, retry_interval=args.retry
    )

    def signal_handler(*_):
        client.running = False

    # Handle graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    try:
        await client.start()
    except KeyboardInterrupt:
        await client.stop()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
