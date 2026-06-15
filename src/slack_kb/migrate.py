from slack_kb.config import get_settings
from slack_kb.database import apply_migrations
from slack_kb.runtime import migration_directory


def main() -> None:
    settings = get_settings()
    apply_migrations(settings.database_url.get_secret_value(), migration_directory())
    print("Database migrations applied.")


if __name__ == "__main__":
    main()
