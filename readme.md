# RC (remote control)

This is remote control application, which goal is remote management the computers.

## architecture

It uses the  python language to write the server and client.
The server is on the public network, the client is on the private network.
The server can send commands to the client, and the client can execute the commands and send the results back to the server.
client can update the system information to the server.

## dependencies

### Runtime Dependencies

- websockets - WebSocket server and client implementation
- psutil - System and process utilities
- asyncio - Asynchronous I/O

### Development Dependencies

- pytest - Testing framework
- pytest-asyncio - Async test support
- pytest-cov - Test coverage
- black - Code formatter
- flake8 - Code linter

## Setup

```bash
pip install -r requirements.txt
```

### server

```bash
PYTHONPATH=$PYTHONPATH:. python rc_server/server.py
```

### client

use the `pyinstaller` to package the client.

```bash
pyinstaller -F rc_client/client.py
```
