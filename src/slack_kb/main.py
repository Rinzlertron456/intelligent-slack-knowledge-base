import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_kb.answer_graph import AnswerGraph
from slack_kb.config import get_settings
from slack_kb.database import Database
from slack_kb.ingestion import IngestionService
from slack_kb.openai_service import OpenAIService
from slack_kb.slack_app import SlackKnowledgeApp


def main() -> None:
    settings = get_settings()
    settings.validate_slack()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    database = Database(settings.database_url.get_secret_value())
    database.open()
    openai = OpenAIService(settings)
    answer_graph = AnswerGraph(database, openai, settings)
    ingestion = IngestionService(database, openai)
    app = App(token=settings.slack_bot_token.get_secret_value())
    SlackKnowledgeApp(
        app=app,
        database=database,
        openai=openai,
        answer_graph=answer_graph,
        ingestion=ingestion,
    )

    try:
        SocketModeHandler(app, settings.slack_app_token.get_secret_value()).start()
    finally:
        database.close()


if __name__ == "__main__":
    main()
