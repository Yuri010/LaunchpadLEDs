from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from launchpad import Launchpad
import sysex_shell

app = FastAPI()
lp = Launchpad()
forbidden_commands = ["help", "send", "sendraw", "reconnect", "consoleclear", "exit", "listenon", "listenoff"]


class CommandRequest(BaseModel):
    command: str
    args: list = []


@app.post("/command")
async def execute_command(request: CommandRequest):
    command = request.command
    args = request.args

    if command in sysex_shell.COMMANDS:
        if command in forbidden_commands:
            raise HTTPException(status_code=403)
        try:
            sysex_shell.COMMANDS[command](lp, args)
            return {"status": "success", "message": f"Executed command: {command}", "args": args}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        raise HTTPException(status_code=400, detail="Unknown command")


@app.get("/commands")
def list_commands():
    allowed_commands = [cmd for cmd in list(sysex_shell.COMMANDS) if cmd not in forbidden_commands]
    return {"commands": allowed_commands}


@app.on_event("startup")
async def startup_event():
    lp.reconnect()
    lp.set_mode("session")
    lp.listen_to_input()


@app.on_event("shutdown")
async def shutdown_event():
    lp.clear()
    lp.disconnect()
