from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI, HTTPException
from psycopg import Error as PostgresError

from slack_kb import __version__
from slack_kb.config import get_settings
from slack_kb.database import Database


def service_info() -> dict[str, str]:
    return {
        "service": "intelligent-slack-knowledge-base",
        "version": __version__,
    }


def health() -> dict[str, str]:
    return {"status": "ok"}


def readiness() -> dict[str, str]:
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    try:
        database.open()
        with database.pool.connection() as connection:
            connection.execute("select 1").fetchone()
    except (PostgresError, TimeoutError, ValueError) as error:
        raise HTTPException(status_code=503, detail="database unavailable") from error
    finally:
        database.close()
    return {"status": "ready"}


Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(*, lifespan: Lifespan | None = None) -> FastAPI:
    application = FastAPI(
        title="Intelligent Slack Knowledge Base",
        version=__version__,
        description="Operational API for the Slack-native knowledge assistant.",
        lifespan=lifespan,
    )
    application.add_api_route("/", service_info, methods=["GET"], tags=["system"])
    application.add_api_route("/healthz", health, methods=["GET"], tags=["system"])
    application.add_api_route("/readyz", readiness, methods=["GET"], tags=["system"])
    return application


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "slack_kb.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
