import asyncio
import pytest
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from rc_server.server import RemoteControlServer
from rc_client.client import RemoteControlClient

class TestBase:
    @pytest.fixture
    async def server(self):
        server = RemoteControlServer(host="localhost", port=8765)
        server_task = asyncio.create_task(server.start())
        await asyncio.sleep(0.1)  # Wait for server to start
        yield server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    @pytest.fixture
    async def client(self):
        client = RemoteControlClient("ws://localhost:8765")
        client_task = asyncio.create_task(client.start())
        await asyncio.sleep(0.1)  # Wait for client to connect
        yield client
        client_task.cancel()
        try:
            await client_task
        except asyncio.CancelledError:
            pass

class TestIntegration(TestBase):
    @pytest.mark.asyncio
    async def test_command_execution(self, server, client):
        # Test command execution
        websocket = list(server.clients)[0]  # Get the connected client
        await server.handle_commands(websocket, "echo 'test'")
        await asyncio.sleep(0.1)  # Wait for command execution
        
        # Add assertions here based on the expected results
        # This will depend on your specific implementation of result handling
