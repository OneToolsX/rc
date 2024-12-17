import asyncio
import pytest
import sys
import os
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rc_server.server import RemoteControlServer
from rc_client.client import RemoteControlClient


@pytest.mark.asyncio
async def test_server_handle_commands():
    server = RemoteControlServer(host="localhost", port=8765)
    client_id = str(uuid.uuid4())
    client = RemoteControlClient(server_url="ws://localhost:8765", client_id=client_id)

    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # Allow server to start

    client_task = asyncio.create_task(client.start())
    await asyncio.sleep(0.1)  # Allow client to connect and register

    try:
        # Verify client registration
        clients = await server.list_clients()
        assert len(clients) == 1
        assert clients[0]["id"] == client_id

        # Test basic command
        test_command = "echo 'Hello, World!'"
        result = await server.handle_commands(client_id, test_command)
        assert result["stdout"].strip() == "Hello, World!"
        assert result["stderr"] == ""
        assert result["return_code"] == 0

        # Test command with error
        error_command = "nonexistent_command"
        result = await server.handle_commands(client_id, error_command)
        assert result.get("error") is not None or result.get("return_code") != 0

        # Test command with multiple lines output
        multi_line_command = "echo 'Line 1\nLine 2'"
        result = await server.handle_commands(client_id, multi_line_command)
        assert len(result["stdout"].strip().split("\n")) == 2

        # Test invalid client ID
        with pytest.raises(ValueError):
            await server.handle_commands("invalid_id", test_command)

    finally:
        # Cleanup
        server.server.close()
        await server.server.wait_closed()
        client_task.cancel()
        server_task.cancel()
