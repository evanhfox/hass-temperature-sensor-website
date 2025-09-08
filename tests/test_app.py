import os
import sys
import importlib
import logging
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


# Additional comprehensive tests for better coverage

def test_invalid_temperature_states(monkeypatch):
    """Test handling of invalid temperature states from Home Assistant"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    test_cases = [
        {"state": "unavailable", "expected": None},
        {"state": "unknown", "expected": None},
        {"state": "error", "expected": None},
        {"state": "", "expected": None},
        {"state": None, "expected": None},
        {"state": "not_a_number", "expected": None},
    ]
    
    for case in test_cases:
        class DummyResponse:
            status_code = 200
            @staticmethod
            def json():
                return {"state": case["state"], "last_updated": "2024-01-01T00:00:00Z"}
        
        monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
        temp, _ = app.get_backyard_temperature()
        assert temp == case["expected"]


def test_http_status_codes(monkeypatch):
    """Test different HTTP status codes from Home Assistant API"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    status_codes = [400, 401, 403, 404, 500, 502, 503]
    
    for status_code in status_codes:
        class DummyResponse:
            def __init__(self):
                self.status_code = status_code
            
            @staticmethod
            def json():
                return {"error": "test error"}
        
        monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
        temp, last_updated = app.get_backyard_temperature()
        assert temp is None
        assert last_updated is None


def test_network_timeout(monkeypatch):
    """Test handling of network timeouts"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    def timeout_error(*args, **kwargs):
        raise app.requests.exceptions.Timeout("Request timed out")
    
    monkeypatch.setattr(app.requests, "get", timeout_error)
    temp, last_updated = app.get_backyard_temperature()
    assert temp is None
    assert last_updated is None


def test_invalid_json_response(monkeypatch):
    """Test handling of invalid JSON responses"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            raise ValueError("Invalid JSON")
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp is None
    assert last_updated is None


def test_temperature_conversion_edge_cases(dummy_app):
    """Test temperature conversion with edge cases"""
    # Test extreme temperatures
    assert dummy_app.celsius_to_fahrenheit(-273.15) == -459.67  # Absolute zero
    assert dummy_app.celsius_to_fahrenheit(100) == 212.0  # Boiling point
    assert dummy_app.celsius_to_fahrenheit(0.1) == 32.18  # Small positive
    assert dummy_app.celsius_to_fahrenheit(-0.1) == 31.82  # Small negative
    
    # Test precision
    assert dummy_app.celsius_to_fahrenheit(36.6) == 97.88
    assert dummy_app.celsius_to_fahrenheit(36.666) == 98.0  # Rounded to 2 decimal places


def test_environment_variable_validation():
    """Test various environment variable combinations"""
    # Test partial environment variables
    with pytest.raises(SystemExit):
        load_app({
            "USE_DUMMY_DATA": "false",
            "HOME_ASSISTANT_URL": "http://example.com",
            # Missing ENTITY_ID and API_TOKEN
        })
    
    with pytest.raises(SystemExit):
        load_app({
            "USE_DUMMY_DATA": "false",
            "HOME_ASSISTANT_URL": "",  # Empty URL
            "ENTITY_ID": "sensor.test",
            "API_TOKEN": "token",
        })


def test_url_construction(monkeypatch):
    """Test URL construction with different base URLs"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://ha.example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {"state": "25", "last_updated": "2024-01-01T00:00:00Z"}
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, _ = app.get_backyard_temperature()
    assert temp == 25.0


def test_logging_output(caplog):
    """Test that appropriate log messages are generated"""
    app = load_app({"USE_DUMMY_DATA": "true"})
    
    with caplog.at_level(logging.INFO):
        app.get_backyard_temperature()
    
    assert "Using dummy data for temperature." in caplog.text


def test_full_integration_with_mock_api(monkeypatch):
    """Test full integration with mocked Home Assistant API"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://ha.example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "test_token",
    })
    
    class MockResponse:
        status_code = 200
        @staticmethod
        def json():
            return {
                "state": "23.5",
                "last_updated": "2024-01-01T12:00:00Z",
                "attributes": {"unit_of_measurement": "°C"}
            }
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: MockResponse())
    app.app.config["TESTING"] = True
    client = app.app.test_client()
    
    response = client.get("/")
    assert response.status_code == 200
    assert b"23.5&deg;C" in response.data
    assert b"74.3&deg;F" in response.data


def test_connection_error(monkeypatch):
    """Test handling of connection errors"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    def connection_error(*args, **kwargs):
        raise app.requests.exceptions.ConnectionError("Connection failed")
    
    monkeypatch.setattr(app.requests, "get", connection_error)
    temp, last_updated = app.get_backyard_temperature()
    assert temp is None
    assert last_updated is None


def test_ssl_error(monkeypatch):
    """Test handling of SSL errors"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "https://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    def ssl_error(*args, **kwargs):
        raise app.requests.exceptions.SSLError("SSL certificate verification failed")
    
    monkeypatch.setattr(app.requests, "get", ssl_error)
    temp, last_updated = app.get_backyard_temperature()
    assert temp is None
    assert last_updated is None


def test_malformed_json_response(monkeypatch):
    """Test handling of malformed JSON responses"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {"state": "25", "last_updated": "2024-01-01T00:00:00Z", "malformed": "data" + chr(0)}
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp == 25.0
    assert last_updated == "2024-01-01T00:00:00Z"


def test_negative_temperature_values(monkeypatch):
    """Test handling of negative temperature values"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {"state": "-15.5", "last_updated": "2024-01-01T00:00:00Z"}
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp == -15.5
    assert last_updated == "2024-01-01T00:00:00Z"


def test_very_high_temperature_values(monkeypatch):
    """Test handling of very high temperature values"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {"state": "999.99", "last_updated": "2024-01-01T00:00:00Z"}
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp == 999.99
    assert last_updated == "2024-01-01T00:00:00Z"


def test_zero_temperature_value(monkeypatch):
    """Test handling of zero temperature value"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {"state": "0", "last_updated": "2024-01-01T00:00:00Z"}
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp == 0.0
    assert last_updated == "2024-01-01T00:00:00Z"


def test_missing_last_updated_field(monkeypatch):
    """Test handling when last_updated field is missing"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {"state": "25"}  # Missing last_updated field
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp == 25.0
    assert last_updated is None


def test_empty_response_data(monkeypatch):
    """Test handling of empty response data"""
    app = load_app({
        "USE_DUMMY_DATA": "false",
        "HOME_ASSISTANT_URL": "http://example.com/",
        "ENTITY_ID": "sensor.backyard_temperature",
        "API_TOKEN": "token",
    })
    
    class DummyResponse:
        status_code = 200
        @staticmethod
        def json():
            return {}  # Empty response
    
    monkeypatch.setattr(app.requests, "get", lambda *_, **__: DummyResponse())
    temp, last_updated = app.get_backyard_temperature()
    assert temp is None
    assert last_updated is None
