import uvicorn

from . import utils
from .config import config


def main():
    utils.init_logger(config.APP_LOG_LEVEL, config.APP_LOGGING_IGNORE)

    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        workers=1 if config.APP_DEBUG else config.APP_WORKER,
        log_level=config.APP_LOG_LEVEL.lower(),
        reload=config.APP_DEBUG,
    )


if __name__ == "__main__":
    main()
