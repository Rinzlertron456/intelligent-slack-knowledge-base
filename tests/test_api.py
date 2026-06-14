from slack_kb.api import create_app, health


def test_health_endpoint() -> None:
    assert health() == {"status": "ok"}


def test_create_app_registers_operational_routes() -> None:
    paths = {route.path for route in create_app().routes}

    assert {"/", "/healthz", "/readyz"} <= paths
