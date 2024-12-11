import json

from fastapi import APIRouter, WebSocket
from loguru import logger

from ..common import agent_model
from ..config import config
from .agent import Agent, tools

router = APIRouter(prefix="/chat")


class WsRapper:
    """WsWrapper yo!"""

    def __init__(self, ws: WebSocket):
        self.ws = ws

    async def send(self, data: str | dict):
        if isinstance(data, str):
            data = {"message": data}
        data = json.dumps(data)
        await self.ws.send_text(data)

    async def send_text(self, data: str):
        await self.ws.send_text(data)

    async def receive(self):
        return json.loads(await self.receive_text())

    async def receive_text(self):
        return await self.ws.receive_text()

    async def close(self):
        await self.ws.close()


@router.websocket("")
async def chat(ws_: WebSocket):  # pragma: no cover
    await ws_.accept()
    ws = WsRapper(ws_)

    try:
        user_input = await ws.receive_text()
        if user_input != "dimihatnemagischegurke!":
            await ws.send_text("false")
            await ws.close()
            return

        await ws.send_text("true")
    except Exception as e:
        logger.error(e)
        return

    while True:
        agent = Agent(agent_model, config.APP_MODEL_SYSTEM_MESSAGE, tools)
        await ws.send(
            "Oi you cheeky wanker, how can I help you with your stupid magic questions?"
        )
        await ws.send("DONE")

        while True:
            try:
                user_input = await ws.receive()
                message = user_input["message"]
                if message == "reset":
                    logger.info("Restarting agent...")
                    break

                async for agent_output in agent.reply(message):
                    await ws.send(agent_output)
                await ws.send("DONE")
            except Exception as e:
                await ws.send(f"An error occured: {e}")
                logger.exception(e)
                break
