from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from loguru import logger

from . import factory, utils
from .chat.routes import router as chat_router
from .config import config
from .health.routes import router as health_router


################################################################################
# STARTUP
@asynccontextmanager
async def lifespan(_):  # type: ignore
    utils.init_logger(config.APP_LOG_LEVEL, config.APP_LOGGING_IGNORE)
    yield


app = factory.create_app(lifespan=lifespan)

################################################################################
# ROUTES
app.include_router(health_router)
app.include_router(chat_router)

# override all operation ids with function name
for route in app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name


################################################################################
# BadRequest: 400  # noqa: ERA001
@app.exception_handler(RuntimeError)
async def handle_bad_request(_, e):
    logger.error(e)

    return JSONResponse(content={"detail": str(e)}, status_code=400)


################################################################################
# Internal: 500  # noqa: ERA001
@app.exception_handler(Exception)
@app.exception_handler(NotImplementedError)
async def handle_internal_general_error(_, e):  # pragma: no cover
    logger.error("500: !!!!!!!!!!!!!!!!!! UNHANDLED !!!!!!!!!!!!!!!!!!")
    logger.exception(e)

    return JSONResponse(content={"detail": "InternalServerError"}, status_code=500)
