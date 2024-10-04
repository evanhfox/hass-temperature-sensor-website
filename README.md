Home Assistant Temperature Web Application

Overview

This project is a simple Flask web application that connects to a Home Assistant API to display the temperature of your backyard. The application fetches the temperature data from a specific Home Assistant entity and displays it on a sleek and modern web page. You can also run this app in a Docker container for easy deployment.

Features

Connects to a Home Assistant instance to fetch temperature data.

Displays the temperature in both Celsius and Fahrenheit units.

Offers a simple HTML interface styled with CSS for a modern look.

Supports dummy data for development and testing purposes.

Dockerized for easy deployment.

Requirements

To run the application, you need to install the following Python packages (as listed in requirements.txt):

Flask==2.0.1

requests==2.26.0

Setup Instructions

1. Clone the Repository

First, clone this repository to your local machine:

git clone <repository-url>
cd home-assistant-temperature-web

2. Install Dependencies

Make sure you have Python 3.9 or higher installed. Install the required dependencies using pip:

pip install -r requirements.txt

3. Environment Variables

To connect to your Home Assistant instance, you need to set the following environment variables:

HOME_ASSISTANT_URL: The base URL of your Home Assistant instance (e.g., http://your-home-assistant-ip:8123/api/states/).

ENTITY_ID: The entity ID of the temperature sensor in your Home Assistant instance (e.g., sensor.backyard_temperature).

API_TOKEN: A long-lived access token to authenticate with Home Assistant.

USE_DUMMY_DATA (optional): Set to true if you want to use dummy temperature data for testing.

FLASK_RUN_HOST (optional): The host on which to run the Flask app (default is 0.0.0.0).

FLASK_RUN_PORT (optional): The port on which to run the Flask app (default is 5000).

4. Running the Application

To run the application locally, use the following command:

flask run

Or, you can run it using Python directly:

python app.py

The application will be available at http://localhost:5000/ by default.

Running with Docker

You can also run this application inside a Docker container:

1. Build the Docker Image

Use the provided Dockerfile to build the Docker image:

docker build -t home-assistant-temperature-web .

2. Run the Docker Container

Run the container using the following command:

docker run -p 5000:5000 \
  -e HOME_ASSISTANT_URL="<your_home_assistant_url>" \
  -e ENTITY_ID="<your_entity_id>" \
  -e API_TOKEN="<your_api_token>" \
  -e USE_DUMMY_DATA="false" \
  home-assistant-temperature-web

Replace the environment variable values (<your_home_assistant_url>, <your_entity_id>, <your_api_token>) as needed.

Using Dummy Data

If you do not have a Home Assistant instance available for testing, you can set the USE_DUMMY_DATA environment variable to true. This will make the application display a dummy temperature value of 25°C.

Project Structure

home-assistant-temperature-web/
├── app.py             # The main Flask application file
├── Dockerfile         # Dockerfile to containerize the application
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation

License

This project is open source and available under the MIT License.

Contributing

Feel free to submit issues or pull requests for any improvements or suggestions you may have. Contributions are always welcome!

Contact

For any questions or issues, feel free to contact me through the GitHub repository.

