import os
import sys
import importlib
from pathlib import Path

import pytest

# Ensure the application module can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))


def load_app(env=None):
    """Import the app module with specific environment variables."""
    env = env or {}
    for key in [
        "USE_DUMMY_DATA",
        "HOME_ASSISTANT_URL",
        "ENTITY_ID",
        "API_TOKEN",
    ]:
        os.environ.pop(key, None)
    os.environ.update(env)
    if "app" in sys.modules:
        del sys.modules["app"]
    return importlib.import_module("app")


@pytest.fixture
def dummy_app():
    return load_app({"USE_DUMMY_DATA": "true"})


@pytest.fixture
def client(dummy_app):
    dummy_app.app.config["TESTING"] = True
    return dummy_app.app.test_client()


def test_celsius_to_fahrenheit(dummy_app):
    assert dummy_app.celsius_to_fahrenheit(0) == 32
    assert dummy_app.celsius_to_fahrenheit(25) == 77.0
    assert dummy_app.celsius_to_fahrenheit(-40) == -40
    assert dummy_app.celsius_to_fahrenheit(36.6) == 97.88


def test_index_returns_dummy_temp(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"25&deg;C" in response.data
    assert b"77.0&deg;F" in response.data
    assert b"Last updated: N/A" in response.data


def test_get_backyard_temperature_success(monkeypatch):
    app = load_app(
        {
            "USE_DUMMY_DATA": "false",
            "HOME_ASSISTANT_URL": "http://example.com/",
            "ENTITY_ID": "sensor.backyard_temperature",
            "API_TOKEN": "token",
        }
    )

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"state": "30", "last_updated": "2024-01-01T00:00:00Z"}

    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp == 30.0
    assert last_updated == "2024-01-01T00:00:00Z"


def test_index_handles_api_error(monkeypatch):
    app = load_app(
        {
            "USE_DUMMY_DATA": "false",
            "HOME_ASSISTANT_URL": "http://example.com/",
            "ENTITY_ID": "sensor.backyard_temperature",
            "API_TOKEN": "token",
        }
    )

    def raise_error(*args, **kwargs):
        raise app.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(app.requests, "get", raise_error)
    app.app.config["TESTING"] = True
    client = app.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"N/A&deg;C / N/A&deg;F" in response.data
    assert b"Last updated: N/A" in response.data


def test_missing_env_vars_raise_system_exit():
    with pytest.raises(SystemExit):
        load_app({"USE_DUMMY_DATA": "false"})
