from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from launchpad import Launchpad
import sysex_shell

app = FastAPI()
lp = Launchpad()


class CommandRequest(BaseModel):
    command: str
    args: list = []


@app.post("/command")
async def execute_command(request: CommandRequest):
    command = request.command
    args = request.args

    if command in sysex_shell.COMMANDS:
        try:
            sysex_shell.COMMANDS[command](lp, args)
            return {"status": "success", "message": f"Executed command: {command}", "args": args}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        raise HTTPException(status_code=400, detail="Unknown command")


@app.get("/commands")
def list_commands():
    return {"commands": list(sysex_shell.COMMANDS.keys())}


@app.on_event("startup")
async def startup_event():
    lp.reconnect()
    lp.set_mode("session")
    lp.listen_to_input()


@app.on_event("shutdown")
async def shutdown_event():
    lp.clear()
    lp.disconnect()