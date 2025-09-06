from flask import Flask, render_template_string, request
import requests
import os
import logging
import sys
from urllib.parse import urljoin

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

# Ensure required variables are set if dummy data is not being used
required_env_vars = {
    "HOME_ASSISTANT_URL": HOME_ASSISTANT_URL,
    "ENTITY_ID": ENTITY_ID,
    "API_TOKEN": API_TOKEN
}

if not USE_DUMMY_DATA:
    for var_name, var_value in required_env_vars.items():
        if not var_value:
            logger.error(f"{var_name} is not set. Please set the environment variable.")
            sys.exit(1)

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
    <p style="font-size: 0.8rem; font-style: italic;">Last updated: {{ last_updated }}</p>
</body>
</html>
"""

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
            data = response.json()
            logger.info(f"Received data: {data}")
            # Extract the temperature value
            temperature = float(data.get('state', None)) if data.get('state') is not None else None
            last_updated = data.get('last_updated', None)
            return temperature, last_updated
        else:
            logger.error(f"Failed to get data from Home Assistant. Status Code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        # Log any exception that occurs during the request
        logger.error(f"Error occurred while making request: {e}")
        return None

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
    else:
        # Convert Celsius to Fahrenheit if valid temperature is available
        temperature_f = celsius_to_fahrenheit(temperature_c)
    logger.info(f"Temperature retrieved: {temperature_c}°C / {temperature_f}°F")
    # Render the HTML template with the temperature values
    return render_template_string(template, temperature_c=temperature_c, temperature_f=temperature_f, last_updated=last_updated)

# Run the Flask app
if __name__ == '__main__':
    # Get host and port from environment variables, use defaults if not set
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    logger.info("Starting Flask app...")
    # Start the Flask application
    app.run(host=host, port=port)
