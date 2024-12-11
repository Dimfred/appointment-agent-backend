FROM python:3.12 AS builder

################################################################################
# PYTHON INIT
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

################################################################################
# POETRY INIT
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip3 install --upgrade --no-cache-dir pip \
    && pip3 install --no-cache-dir uv

################################################################################
# SSH INIT
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl openssh-client git gcc
RUN mkdir -m 0600 /root/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

################################################################################
# INSTALL
WORKDIR /app
# hadolint ignore=DL3008
RUN apt-get install --no-install-recommends -y libmariadb3 libmariadb-dev
COPY ./pyproject.toml ./uv.lock ./
RUN --mount=type=ssh uv sync --no-cache

################################################################################
# APP
FROM python:3.12-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y make expect mariadb-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app
COPY ./src ./src
COPY ./Makefile ./entrypoint.sh ./
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic
COPY ./data ./data

EXPOSE 8000

ENTRYPOINT [ "./entrypoint.sh" ]
