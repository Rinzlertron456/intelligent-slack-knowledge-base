from slack_kb.config import get_settings
from slack_kb.database import Database
from slack_kb.runtime import migration_directory


def main() -> None:
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    database.open()
    try:
        database.migrate(migration_directory())
        print("Database migrations applied.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
