import os
from pathlib import Path

from pydantic_settings import BaseSettings

APP_ENV = os.environ.get("APP_ENV", "dev")
APP_NAME = os.environ.get("APP_NAME", f"appointment-agent-{APP_ENV}")


class Config(BaseSettings):
    ############################################################################
    # APP
    APP_ENV: str = APP_ENV
    APP_NAME: str = APP_NAME

    APP_DEBUG: bool = True
    APP_LOG_LEVEL: str = "INFO"
    APP_LOGGING_IGNORE: list[str] = [
        "asyncio",
        "aiosqlite",
        "httpx",
        "urllib3",
        "openai",
        "httpcore",
        "websockets",
    ]
    APP_WORKER: int = 4

    APP_DATA_PATH: str = "data"

    ################################################################################
    # APP
    APP_MODEL_SYSTEM_MESSAGE: str = """
You are an autonomous Appointment Agent.
Your task is to create appointments for the user.
For this you will call an api, and create appointments and check whether appointments are available for a given date and time.
Your response will be converted to human speech because the appointment will be created over a phone call.
Hence give answer's concise and like a human would.
"""
    APP_MODEL: str = "gpt-4o-mini"

    LANGCHAIN_PROJECT: str = "appointment-agent-dev"

    ############################################################################
    # FASTAPI
    FAPI_DOCS_ENABLE: bool = True
    FAPI_CORS_ENABLE: bool = True
    FAPI_CORS_ALLOW_CREDENTIALS: bool = True
    FAPI_CORS_ALLOW_ORIGINS: list[str] = ["*"]
    FAPI_CORS_ALLOW_METHODS: list[str] = ["*"]
    FAPI_CORS_ALLOW_HEADERS: list[str] = ["*"]

    def init(self):
        Path(self.APP_DATA_PATH).mkdir(parents=True, exist_ok=True)

        assert (
            os.environ.get("LANGCHAIN_API_KEY", None) is not None
        ), "export LANGCHAIN_API_KEY=<api_key>"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = self.LANGCHAIN_PROJECT

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
config.init()
