import asyncio
import json
import subprocess
import websockets.client
from utils.logger import setup_logger
import uuid
import platform
import socket

class RemoteControlClient:
    def __init__(self, server_url="ws://localhost:8765", client_id=None):
        self.server_url = server_url
        self.client_id = client_id or str(uuid.uuid4())
        self.client_info = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version()
        }
        self.logger = setup_logger('rc_client', 'client.log')
        self.logger.info(f"Client initialized with server URL: {server_url}")

    async def execute_command(self, command):
        self.logger.debug(f"Executing command: {command}")
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            self.logger.debug(f"Command result: stdout={stdout}, stderr={stderr}, rc={process.returncode}")
            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode,
            }
        except Exception as e:
            self.logger.error(f"Command execution error: {str(e)}")
            return {"error": str(e)}

    async def start(self):
        self.logger.info("Starting client...")
        async with websockets.client.connect(self.server_url) as websocket:
            # Send client identification
            await websocket.send(
                json.dumps({
                    "client_id": self.client_id,
                    "client_info": self.client_info
                })
            )
            self.logger.info(f"Connected to server: {self.server_url} with ID: {self.client_id}")
            
            try:
                async for message in websocket:
                    data = json.loads(message)
                    if data.get("type") == "command":
                        self.logger.info(f"Received command: {data['data']}")
                        result = await self.execute_command(data["data"])
                        self.logger.debug(f"Sending result: {result}")
                        await websocket.send(
                            json.dumps({
                                "type": "command_result", 
                                "data": result,
                                "id": data.get("id")
                            })
                        )
            except Exception as e:
                self.logger.error(f"Connection error: {str(e)}")
            finally:
                self.logger.info("Client disconnected")
