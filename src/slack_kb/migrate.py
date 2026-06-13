from pathlib import Path

from slack_kb.config import get_settings
from slack_kb.database import Database


def main() -> None:
    settings = get_settings()
    database = Database(settings.database_url.get_secret_value())
    database.open()
    try:
        migration_dir = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
        database.migrate(migration_dir)
        print("Database migrations applied.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
