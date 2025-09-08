from flask import Flask, render_template_string, request, jsonify
import requests
import os
import logging
import sys
from urllib.parse import urljoin
from collections import deque
from time import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables for Home Assistant configuration
HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL")
ENTITY_ID = os.getenv("ENTITY_ID")
API_TOKEN = os.getenv("API_TOKEN")
USE_DUMMY_DATA = os.getenv("USE_DUMMY_DATA", "false").lower() == "true"
FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST")
FLASK_RUN_PORT = os.getenv("FLASK_RUN_PORT")
ENTITIES_ENV = os.getenv("ENTITIES", "")
REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL_SECONDS", "15"))
HISTORY_POINTS = int(os.getenv("HISTORY_POINTS", "100"))

# Parse ENTITIES env var into a list
ENTITIES = [e.strip() for e in ENTITIES_ENV.split(",") if e.strip()] if ENTITIES_ENV else []

# Ensure required variables are set if dummy data is not being used
if not USE_DUMMY_DATA:
    if ENTITIES:
        # In multi-entity mode, require base URL and token only
        multi_required = {
            "HOME_ASSISTANT_URL": HOME_ASSISTANT_URL,
            "API_TOKEN": API_TOKEN,
        }
        for var_name, var_value in multi_required.items():
            if not var_value:
                logger.error(f"{var_name} is not set. Please set the environment variable.")
                sys.exit(1)
    else:
        # Single-entity mode requires ENTITY_ID as well
        single_required = {
            "HOME_ASSISTANT_URL": HOME_ASSISTANT_URL,
            "ENTITY_ID": ENTITY_ID,
            "API_TOKEN": API_TOKEN,
        }
        for var_name, var_value in single_required.items():
            if not var_value:
                logger.error(f"{var_name} is not set. Please set the environment variable.")
                sys.exit(1)

# If ENTITIES is provided, allow multi-entity mode. Single-entity index remains available.
if ENTITIES and not USE_DUMMY_DATA:
    # Validate that the base HA URL and token exist for multi-entity too (already checked above)
    logger.info(f"Multi-entity mode enabled with ENTITIES={ENTITIES}")

# Validate Flask host and port environment variables
# Use default values if Flask host and port are not provided
if FLASK_RUN_HOST is None:
    logger.warning("FLASK_RUN_HOST is not set. Using default: '0.0.0.0'")
if FLASK_RUN_PORT is None:
    logger.warning("FLASK_RUN_PORT is not set. Using default: 5000")

# Template used to display the temperature on the website
template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backyard Temperature</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #1e1e2f;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            color: #f0f0f0;
        }
        .card {
            background: #282a36;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        .temperature {
            font-size: 3rem;
            font-weight: 700;
            color: #ff79c6;
        }
        h1 {
            color: #8be9fd;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Backyard Temperature</h1>
        <p class="temperature">{{ temperature_c }}&deg;C / {{ temperature_f }}&deg;F</p>
    </div>
    <p style="font-size: 0.8rem; font-style: italic;">Last updated: {{ last_updated or 'N/A' }}</p>
</body>
</html>
"""

# In-memory history store: entity_id -> deque of (ts, value_c)
_history = {}

def _append_history(entity_id: str, value_c):
    if value_c is None:
        return
    if entity_id not in _history:
        _history[entity_id] = deque(maxlen=HISTORY_POINTS)
    _history[entity_id].append((int(time()), float(value_c)))

# Generic function to get a sensor reading (Celsius and last_updated)
def get_sensor_reading(entity_id: str):
    if USE_DUMMY_DATA:
        logger.info(f"Using dummy data for entity {entity_id}.")
        return 25, "N/A", {"friendly_name": entity_id, "unit_of_measurement": "°C", "icon": "mdi:thermometer"}

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    url = urljoin(HOME_ASSISTANT_URL, f"api/states/{entity_id}")
    logger.info(f"Requesting Home Assistant state: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Received data: {data}")
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return None, None, {}

            state_value = data.get("state", None)
            temperature = None
            if state_value is not None:
                try:
                    temperature = float(state_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid temperature state value: {state_value}")
                    temperature = None
            last_updated = data.get("last_updated", None)
            attributes = data.get("attributes", {}) or {}
            return temperature, last_updated, attributes
        else:
            logger.error(f"Failed to get data from Home Assistant. Status Code: {response.status_code}")
            return None, None, {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error occurred while making request: {e}")
        return None, None, {}

# Function to get temperature from Home Assistant or use dummy data
def get_backyard_temperature():
    # Use dummy data if enabled for testing purposes
    if USE_DUMMY_DATA:
        logger.info("Using dummy data for temperature.")
        # Return a Celsius value and a placeholder for last updated
        return 25, "N/A"

    # Prepare request headers for Home Assistant API
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    # Construct the URL using urljoin to ensure proper URL formatting
    url = urljoin(HOME_ASSISTANT_URL, f"api/states/{ENTITY_ID}")
    logger.info(f"Making request to Home Assistant API at: {url}")
    try:
        # Make a GET request to the Home Assistant API
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response status code: {response.status_code}")

        # If the response is successful, extract the temperature state
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Received data: {data}")
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return None, None
            
            # Extract the temperature value with proper error handling
            state_value = data.get('state', None)
            temperature = None
            if state_value is not None:
                try:
                    temperature = float(state_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid temperature state value: {state_value}")
                    temperature = None
            last_updated = data.get('last_updated', None)
            return temperature, last_updated
        else:
            logger.error(f"Failed to get data from Home Assistant. Status Code: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        # Log any exception that occurs during the request
        logger.error(f"Error occurred while making request: {e}")
        return None, None

# Utility function to convert Celsius to Fahrenheit
def celsius_to_fahrenheit(celsius):
    # Convert temperature from Celsius to Fahrenheit
    return round((celsius * 9/5) + 32, 2)

# Route to display the temperature
@app.route('/')
def index():
    # Get the IP address of the client making the request
    client_ip = request.remote_addr
    logger.info(f"Handling request to '/' route from IP: {client_ip}")
    # Get the backyard temperature
    temperature_c, last_updated = get_backyard_temperature()
    if temperature_c is None:
        # If temperature could not be retrieved, set to 'N/A'
        temperature_c = "N/A"
        temperature_f = "N/A"
        last_updated = "N/A"
    else:
        # Convert Celsius to Fahrenheit if valid temperature is available
        temperature_f = celsius_to_fahrenheit(temperature_c)
    logger.info(f"Temperature retrieved: {temperature_c}°C / {temperature_f}°F")
    # Render the HTML template with the temperature values
    return render_template_string(template, temperature_c=temperature_c, temperature_f=temperature_f, last_updated=last_updated)

# JSON API: return current readings and history for multi-entity dashboard
@app.route('/api/sensors')
def api_sensors():
    entities = ENTITIES if ENTITIES else ([ENTITY_ID] if ENTITY_ID else [])
    results = []
    errors = {}
    for eid in entities:
        temp_c, last_updated, attrs = get_sensor_reading(eid)
        if temp_c is not None:
            _append_history(eid, temp_c)
        else:
            errors[eid] = "unavailable"
        unit = attrs.get("unit_of_measurement", "°C")
        name = attrs.get("friendly_name", eid)
        icon = attrs.get("icon", "mdi:thermometer")
        temp_f = celsius_to_fahrenheit(temp_c) if temp_c is not None else None
        results.append({
            "entity_id": eid,
            "friendly_name": name,
            "icon": icon,
            "value_c": temp_c,
            "value_f": temp_f,
            "unit": unit,
            "last_updated": last_updated,
        })

    history_payload = {eid: list(_history.get(eid, [])) for eid in entities}
    return jsonify({"current": results, "history": history_payload, "errors": errors, "refresh_seconds": REFRESH_INTERVAL_SECONDS})


# Simple dashboard page with auto-refresh and inline SVG sparklines
_dashboard_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sensor Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Roboto', sans-serif; background:#1e1e2f; color:#f0f0f0; margin:0; }
    .container { max-width: 1200px; margin: 0 auto; padding: 1rem; }
    .grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
    .card { background:#282a36; border-radius:10px; padding:1rem; box-shadow: 0 8px 16px rgba(0,0,0,0.4); }
    .title { font-weight:700; color:#8be9fd; margin:0 0 .25rem 0; }
    .value { font-size:2rem; font-weight:700; color:#ff79c6; margin:.25rem 0; }
    .meta { font-size:.85rem; opacity:.8; }
    .error { color:#ff5555; }
    svg { width:100%; height:60px; }
  </style>
  <script>
    async function fetchData() {
      const res = await fetch('/api/sensors');
      return res.json();
    }
    function sparkline(points, width, height) {
      if (!points || points.length === 0) return '';
      const xs = points.map(p => p[0]);
      const ys = points.map(p => p[1]);
      const minX = Math.min(...xs), maxX = Math.max(...xs);
      const minY = Math.min(...ys), maxY = Math.max(...ys);
      const dx = (maxX - minX) || 1; const dy = (maxY - minY) || 1;
      const scaleX = x => ((x - minX) / dx) * (width - 2) + 1;
      const scaleY = y => height - (((y - minY) / dy) * (height - 2) + 1);
      let d = '';
      points.forEach((p,i)=>{
        const x = scaleX(p[0]); const y = scaleY(p[1]);
        d += (i===0? 'M':'L') + x + ' ' + y + ' ';
      });
      return d;
    }
    function render(data) {
      const grid = document.getElementById('grid');
      grid.innerHTML = '';
      data.current.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        const err = data.errors[item.entity_id];
        const valueText = (item.value_c !== null && item.value_c !== undefined)
          ? `${item.value_c}°C / ${item.value_f}°F`
          : 'N/A';
        card.innerHTML = `
          <div class="title">${item.friendly_name}</div>
          <div class="value ${err ? 'error':''}">${valueText}</div>
          <div class="meta">${item.last_updated || 'N/A'}</div>
          <svg viewBox="0 0 200 60"><path d="${sparkline(data.history[item.entity_id] || [], 200, 60)}" fill="none" stroke="#8be9fd" stroke-width="2"/></svg>
        `;
        grid.appendChild(card);
      });
    }
    async function tick() {
      try {
        const data = await fetchData();
        render(data);
        setTimeout(tick, (data.refresh_seconds || 15) * 1000);
      } catch (e) {
        console.error(e);
        setTimeout(tick, 15000);
      }
    }
    window.addEventListener('DOMContentLoaded', tick);
  </script>
</head>
<body>
  <div class="container">
    <h1 class="title">Sensor Dashboard</h1>
    <div id="grid" class="grid"></div>
  </div>
</body>
</html>
"""

@app.route('/dashboard')
def dashboard():
    return render_template_string(_dashboard_template)

# Run the Flask app
if __name__ == '__main__':
    # Get host and port from environment variables, use defaults if not set
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    logger.info("Starting Flask app...")
    # Start the Flask application
    app.run(host=host, port=port)
