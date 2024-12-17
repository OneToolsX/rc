import asyncio
import pytest
import sys
import os
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rc_server.server import RemoteControlServer
from rc_client.client import RemoteControlClient


@pytest.mark.asyncio
async def test_multiple_clients():
    server = RemoteControlServer(host="localhost", port=8765)
    clients = [
        RemoteControlClient(server_url="ws://localhost:8765", client_id=f"client_{i}")
        for i in range(3)
    ]

    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)

    # Start all clients
    client_tasks = [asyncio.create_task(client.start()) for client in clients]
    await asyncio.sleep(0.1)

    try:
        # Verify all clients are connected
        connected_clients = await server.list_clients()
        assert len(connected_clients) == 3

        # Test command on each client
        for i in range(3):
            client_id = f"client_{i}"
            result = await server.handle_commands(client_id, "echo 'test'")
            assert result["stdout"].strip() == "test"

    finally:
        # Cleanup
        server.server.close()
        await server.server.wait_closed()
        for task in client_tasks:
            task.cancel()
        server_task.cancel()
