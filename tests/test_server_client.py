import asyncio
import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rc_server.server import RemoteControlServer
from rc_client.client import RemoteControlClient


@pytest.mark.asyncio
async def test_server_client_interaction():
    server = RemoteControlServer(host="localhost", port=8765)
    client = RemoteControlClient(server_url="ws://localhost:8765")

    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # Allow server to start

    client_task = asyncio.create_task(client.start())
    await asyncio.sleep(0.1)  # Allow client to connect

    # Send a test command from the server to the client
    test_command = "echo 'Hello, World!'"
    await server.handle_commands(next(iter(server.clients)), test_command)

    # Allow time for command execution and result transmission
    await asyncio.sleep(0.1)

    # Assert that the server received the correct command result
    assert len(server.command_results) > 0
    result = server.command_results[0]
    assert result["stdout"].strip() == "Hello, World!"
    assert result["stderr"] == ""
    assert result["return_code"] == 0

    # Shutdown server and client
    server.server.close()
    await server.server.wait_closed()
    client_task.cancel()
    server_task.cancel()
