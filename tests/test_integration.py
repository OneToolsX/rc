import asyncio
import pytest
import sys
import os
import json
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

    async def get_last_message(self, websocket, timeout=1):
        """Helper method to get the last message from websocket messages"""
        try:
            async with asyncio.timeout(timeout):
                async for message in websocket:
                    last_message = json.loads(message)
                    if last_message.get('type') == 'command_result':
                        return last_message
        except asyncio.TimeoutError:
            return None

class TestIntegration(TestBase):
    @pytest.mark.asyncio
    async def test_command_execution(self, server, client):
        """Test basic command execution"""
        await asyncio.sleep(0.1)  # Ensure connection is established
        websocket = list(server.clients)[0]
        
        # Test echo command
        await server.handle_commands(websocket, "echo 'test message'")
        result = await self.get_last_message(websocket)
        
        assert result is not None
        assert result['type'] == 'command_result'
        assert 'test message' in result['data']['stdout']
        assert result['data']['return_code'] == 0

    @pytest.mark.asyncio
    async def test_system_info(self, server, client):
        """Test system information updates"""
        await asyncio.sleep(0.1)
        websocket = list(server.clients)[0]
        
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'system_info':
                system_info = data['data']
                assert 'cpu_percent' in system_info
                assert 'memory_percent' in system_info
                assert 'disk_usage' in system_info
                assert isinstance(system_info['cpu_percent'], (int, float))
                assert isinstance(system_info['memory_percent'], (int, float))
                assert isinstance(system_info['disk_usage'], (int, float))
                break

    @pytest.mark.asyncio
    async def test_invalid_command(self, server, client):
        """Test handling of invalid commands"""
        await asyncio.sleep(0.1)
        websocket = list(server.clients)[0]
        
        await server.handle_commands(websocket, "invalid_command_123")
        result = await self.get_last_message(websocket)
        
        assert result is not None
        assert result['type'] == 'command_result'
        assert result['data']['return_code'] != 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
