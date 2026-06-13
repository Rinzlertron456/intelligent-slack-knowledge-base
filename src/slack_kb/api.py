from fastapi import FastAPI, HTTPException
from psycopg import Error as PostgresError

from slack_kb import __version__
from slack_kb.config import get_settings
from slack_kb.database import Database

app = FastAPI(
    title="Intelligent Slack Knowledge Base",
    version=__version__,
    description="Operational API for the Slack-native knowledge assistant.",
)


@app.get("/", tags=["system"])
def service_info() -> dict[str, str]:
    return {
        "service": "intelligent-slack-knowledge-base",
        "version": __version__,
    }


@app.get("/healthz", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["system"])
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
