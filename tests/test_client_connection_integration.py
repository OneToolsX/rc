import asyncio
import pytest
import uuid
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rc_server.server import RemoteControlServer
from rc_client.client import RemoteControlClient


@pytest.mark.asyncio
async def test_handle_connection_integration():
    """Test client connection handling with real server"""
    # Setup server and client
    server = RemoteControlServer(host="localhost", port=8766)
    client_id = str(uuid.uuid4())
    client = RemoteControlClient(
        server_url="ws://localhost:8766", client_id=client_id, retry_interval=1
    )

    try:
        # Start server
        server_task = asyncio.create_task(server.start())
        await asyncio.sleep(0.1)  # Allow server to start

        # Start client
        client_task = asyncio.create_task(client.start())
        await asyncio.sleep(0.1)  # Allow client to connect

        # Verify client registration
        clients = await server.list_clients()
        assert len(clients) == 1
        assert clients[0]["id"] == client_id

        # Test command execution
        result = await server.handle_commands(client_id, "echo 'test connection'")
        assert result["stdout"].strip() == "test connection"
        assert result["return_code"] == 0

        # Test client reconnection
        server.server.close()
        await server.server.wait_closed()
        await asyncio.sleep(0.1)

        # Restart server
        server = RemoteControlServer(host="localhost", port=8766)
        server_task = asyncio.create_task(server.start())
        await asyncio.sleep(2)  # Allow time for client to reconnect

        # Verify reconnection
        clients = await server.list_clients()
        assert len(clients) == 1
        assert clients[0]["id"] == client_id

        # Test command after reconnection
        result = await server.handle_commands(client_id, "echo 'reconnected'")
        assert result["stdout"].strip() == "reconnected"
        assert result["return_code"] == 0

    finally:
        # Cleanup
        client.running = False
        if hasattr(server, "server"):
            server.server.close()
            await server.server.wait_closed()
        await asyncio.sleep(0.1)
        client_task.cancel()
        server_task.cancel()
