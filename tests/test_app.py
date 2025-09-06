import os
import sys
import importlib
from pathlib import Path
import pytest

os.environ['USE_DUMMY_DATA'] = 'true'
sys.path.append(str(Path(__file__).resolve().parent.parent))
app = importlib.import_module('app')


@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    return app.app.test_client()


def test_celsius_to_fahrenheit():
    assert app.celsius_to_fahrenheit(0) == 32
    assert app.celsius_to_fahrenheit(25) == 77.0


def test_index_returns_dummy_temp(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'25&deg;C' in response.data
    assert b'77.0&deg;F' in response.data
    assert b'Last updated: N/A' in response.data
