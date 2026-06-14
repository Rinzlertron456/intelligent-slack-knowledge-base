from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from slack_kb.api import create_app
from slack_kb.config import get_settings
from slack_kb.runtime import build_slack_runtime

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    runtime = build_slack_runtime(settings, apply_migrations=True)
    runtime.handler.connect()
    app.state.slack_runtime = runtime
    LOGGER.info("FastAPI and Slack Socket Mode runtime are ready")
    try:
        yield
    finally:
        runtime.close()
        LOGGER.info("Slack runtime stopped")


app = create_app(lifespan=lifespan)
