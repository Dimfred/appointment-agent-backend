from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config


def create_app(lifespan=None):  # pragma: no cover
    app = (
        FastAPI(lifespan=lifespan)
        if config.FAPI_DOCS_ENABLE
        else FastAPI(openapi_url="", lifespan=lifespan)
    )
    app = _create_cors(app, config)
    return app


def _create_cors(app, config):  # pragma: no cover
    if not config.FAPI_CORS_ENABLE:
        return app

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=config.FAPI_CORS_ALLOW_CREDENTIALS,
        allow_origins=config.FAPI_CORS_ALLOW_ORIGINS,
        allow_methods=config.FAPI_CORS_ALLOW_METHODS,
        allow_headers=config.FAPI_CORS_ALLOW_HEADERS,
    )

    return app
