import re
import uuid
from typing import Annotated

import requests
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from loguru import logger

from ..config import config
from ..utils.stopwatch import Stopwatch

sw_overall = Stopwatch()


################################################################################
# TOOLS
@tool
def create_appointment(
    name: Annotated[str, "The name of the person creating the appointment"],
    phone_number: Annotated[
        str, "The phone number of the person creating the appointment"
    ],
    appointment_time: Annotated[
        str, "The time for the appointment in the format YYYY-MM-DD HH:MM"
    ],
) -> Annotated[
    tuple[int, str], "Returns the status code of the REST call and a message"
]:
    """Use this to create an appointment. The values can't be empty and should be provided by the user. DOUBLE CHECK with the user before you use this."""
    res = requests.post(
        "http://localhost:8001",
        params={
            "name": name,
            "phone": phone_number,
            "appointment_time": appointment_time,
        },
    )

    return res.status_code, res.text


@tool
def get_appointments(date: Annotated[str, "The date in the format YYYY-MM-DD"]):
    """Use this to obtain the already assigned appointments to have a check whether at that time an appointment can be created. If a time is not present here it means it is available and free to book."""
    year, month, day = date.split("-")
    res = requests.get(
        "http://localhost:8001",
        params={"year": int(year), "month": int(month), "day": int(day)},
    )
    return res.status_code, res.text


@tool
def hang_up():
    """Call this function once the appointment has been successfully scheduled"""
    logger.info(f"Calltook: {sw_overall()}")
    exit(0)


TOOLS = [create_appointment, get_appointments, hang_up]


################################################################################
# BOT INIT
class Agent:
    def __init__(self, agent_model, system_prompt, tools):
        self.input_tokens, self.output_tokens = 0, 0

        memory = MemorySaver()
        self.agent_executor = create_react_agent(
            model=agent_model,
            tools=tools,  # type: ignore
            checkpointer=memory,
            state_modifier=SystemMessage(system_prompt),
        )
        self.agent_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        self.uuid = self.agent_config["configurable"]["thread_id"]

    async def reply(self, user_input: str):
        async for output in self.agent_executor.astream_log(
            input={"messages": [HumanMessage(content=user_input)]},
            config=self.agent_config,  # type: ignore
            include_types=["llm"],
        ):
            for op in output.ops:
                # DEBUG
                # logger.info(op)

                if "op" not in op or op["op"] != "add":
                    continue

                if "path" not in op or not re.match(
                    r"/logs/main(:\d+)?/streamed_output_str/-", op["path"]
                ):
                    continue

                if "value" not in op:
                    continue

                yield op["value"]
