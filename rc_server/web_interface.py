from fastapi import FastAPI, WebSocket, Request, Form, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import asyncio
from typing import Optional
from .server import RemoteControlServer

app = FastAPI()
templates = Jinja2Templates(directory="rc_server/templates")

# Global server instance
rc_server: Optional[RemoteControlServer] = None


@app.on_event("startup")
async def startup_event():
    global rc_server
    rc_server = RemoteControlServer()
    # Start server in background
    asyncio.create_task(rc_server.start())


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if rc_server is None:
        return {"message": "Server not initialized"}
    clients = await rc_server.list_clients()
    return templates.TemplateResponse(
        "index.html", {"request": request, "clients": clients}
    )


class CommandRequest(BaseModel):
    client_id: str
    command: str


@app.post("/execute")
async def execute_command(command_req: CommandRequest):
    try:
        if rc_server is None:
            raise ValueError("Server not initialized")
        print(f"Raw command received: {repr(command_req.command)}")
        result = await rc_server.handle_commands(
            command_req.client_id, command_req.command
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/clients")
async def get_clients():
    if rc_server is None:
        return {"message": "Server not initialized"}
    clients = await rc_server.list_clients()
    return {"clients": clients}


def start_web_server():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


start_web_server()
