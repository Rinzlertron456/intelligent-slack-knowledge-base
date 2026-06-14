import logging

from slack_kb.config import get_settings
from slack_kb.runtime import build_slack_runtime


def main() -> None:
    settings = get_settings()
    settings.validate_slack()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    runtime = build_slack_runtime(settings)
    try:
        runtime.handler.start()
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
