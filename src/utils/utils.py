import base64
import logging
import sys
import uuid

from loguru import logger


################################################################################
# LOGGER
class LoggingInterceptHandler(logging.Handler):  # pragma: no cover
    def __init__(self):
        super().__init__()

    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def init_logger(level, ignore=None):  # pragma: no cover
    if ignore is None:
        ignore = []

    # intercept logs from default logging module
    logging.basicConfig(handlers=[LoggingInterceptHandler()], level=1, force=True)

    # clear the config
    logger.remove()

    # ignore some entries
    for entry in ignore:
        logger.disable(entry)

    # validate that the level is correct
    levels = ("DEBUG", "INFO", "WARNING", "ERROR")
    if level not in levels:
        msg = f"Unknown log level: {level}\nAllowed Values: {levels}"
        raise ValueError(msg)

    # attach this and all above layers
    logger.add(sys.stderr, level=level)

    # Disable WebSocket debug logs
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("asyncio.coroutines").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.WARNING)
    logging.getLogger("websockets.protocol").setLevel(logging.WARNING)


################################################################################
# CREPTO
def sha256(s):  # pragma: no cover
    from Cryptodome.Hash import SHA256

    sha256 = SHA256.new()
    sha256.update(bytes(s, "utf-8"))
    hash_ = sha256.hexdigest()

    return hash_


def urlsafe_unique_token():  # pragma: no cover
    _uuid = str(uuid.uuid4()).encode("utf-8")
    token = base64.urlsafe_b64encode(_uuid)

    return token
