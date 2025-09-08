# Home Assistant Temperature Web Application

## Overview

This project is a robust Flask web application that connects to a Home Assistant API to display temperature data in a sleek, modern web interface. The application features comprehensive error handling, security scanning, automated testing, and CI/CD integration for production-ready deployment.

## Features

- 🌡️ **Temperature Display**: Shows temperature in both Celsius and Fahrenheit
- 🏠 **Home Assistant Integration**: Connects to HA API with proper authentication
- 🎨 **Modern UI**: Clean, responsive design with dark theme
- 🧪 **Dummy Data Mode**: Built-in testing mode for development
- 🐳 **Docker Support**: Multi-platform container builds (AMD64/ARM64)
- 🔒 **Security Scanning**: Automated Trivy vulnerability scanning
- 🧪 **Comprehensive Testing**: 25 test cases covering edge cases and errors
- 🚀 **CI/CD Pipeline**: GitHub Actions with automated builds and security scans
- 📊 **Error Handling**: Robust handling of network issues, invalid data, and API errors
- 📝 **Logging**: Comprehensive logging for debugging and monitoring

### New (Multi-Entity + Dashboard)
- 📦 Multi-entity support via `ENTITIES` env var
- 🔁 Auto-refreshing dashboard at `/dashboard`
- 📈 Inline SVG sparklines showing recent trends
- 🔌 JSON API at `/api/sensors` with current values and in-memory history

## Requirements

### Python Dependencies
- **Python 3.9+** (tested with Python 3.13)
- **Flask==3.1.2** - Web framework
- **requests==2.32.5** - HTTP client for Home Assistant API
- **pytest==8.4.2** - Testing framework

### System Requirements
- **Docker** (optional, for containerized deployment)
- **Home Assistant** instance with API access

## Setup Instructions

### 1. Clone the Repository

First, clone this repository to your local machine:

```bash
git clone <repository-url>
cd home-assistant-temperature-web
```

### 2. Install Dependencies

Make sure you have Python 3.9 or higher installed. Install the required dependencies using `pip`:

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

To connect to your Home Assistant instance, you need to set the following environment variables:

- `HOME_ASSISTANT_URL`: The base URL of your Home Assistant instance (e.g., `http://your-home-assistant-ip:8123/api/states/`).
- `ENTITY_ID`: The entity ID of the temperature sensor in your Home Assistant instance (e.g., `sensor.backyard_temperature`).
- `API_TOKEN`: A long-lived access token to authenticate with Home Assistant.
- `USE_DUMMY_DATA` (optional): Set to `true` if you want to use dummy temperature data for testing.
- `FLASK_RUN_HOST` (optional): The host on which to run the Flask app (default is `0.0.0.0`).
- `FLASK_RUN_PORT` (optional): The port on which to run the Flask app (default is `5000`).

Additional (for multi-entity/dashboard):
- `ENTITIES` (optional): Comma-separated list of entity IDs (e.g., `sensor.backyard_temp,sensor.garage_temp`). If set, enables multi-entity mode and powers `/dashboard` and `/api/sensors`.
- `REFRESH_INTERVAL_SECONDS` (optional): Auto-refresh interval for the dashboard and API clients. Default: `15`.
- `HISTORY_POINTS` (optional): Number of recent points to keep per entity in in-memory history (ring buffer). Default: `100`.

### 4. Running the Application

To run the application locally, use the following command:

```bash
flask run
```

Or, you can run it using Python directly:

```bash
python app.py
```

The application will be available at `http://localhost:5000/` by default.

## Testing

Run the comprehensive test suite to ensure everything works correctly:

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

The test suite includes 25 test cases covering:
- Temperature conversion edge cases
- Error handling (network timeouts, invalid data, API errors)
- Home Assistant API integration
- Environment variable validation
- Template rendering
- Multi-entity JSON API and dashboard route

## Running with Docker

You can also run this application inside a Docker container:

### 1. Build the Docker Image

Use the provided Dockerfile to build the Docker image:

```bash
# Build for current platform
docker build -t home-assistant-temperature-web .

# Build for multiple platforms (AMD64/ARM64)
docker buildx build --platform linux/amd64,linux/arm64 -t home-assistant-temperature-web .
```

### 2. Run the Docker Container (single-entity)

Run the container using the following command:

```bash
docker run -p 5000:5000 \
  -e HOME_ASSISTANT_URL="http://your-home-assistant-ip:8123" \
  -e ENTITY_ID="sensor.backyard_temperature" \
  -e API_TOKEN="your_long_lived_access_token" \
  -e USE_DUMMY_DATA="false" \
  home-assistant-temperature-web
```

**Note**: Replace the environment variable values with your actual Home Assistant configuration.

### 3. Run the Docker Container (multi-entity + dashboard)

```bash
docker run -p 5000:5000 \
  -e HOME_ASSISTANT_URL="http://your-home-assistant-ip:8123" \
  -e API_TOKEN="your_long_lived_access_token" \
  -e ENTITIES="sensor.backyard_temp,sensor.garage_temp,sensor.kitchen_temp" \
  -e REFRESH_INTERVAL_SECONDS="15" \
  -e HISTORY_POINTS="200" \
  home-assistant-temperature-web
```

Then open:
- Dashboard (multi-entity): `http://localhost:5000/dashboard`
- JSON API: `http://localhost:5000/api/sensors`

## Using Dummy Data

If you do not have a Home Assistant instance available for testing, you can set the `USE_DUMMY_DATA` environment variable to `true`. This will make the application display a dummy temperature value of 25°C.

## CI/CD Pipeline

This project includes automated CI/CD pipelines via GitHub Actions:

### Features
- 🐳 **Multi-platform Docker builds** (AMD64/ARM64)
- 🔒 **Automated security scanning** with Trivy
- 🧪 **Comprehensive testing** on every push/PR
- 📦 **Container registry publishing** to GitHub Container Registry
- 💬 **PR comments** with security scan results
- 📊 **Security summaries** in GitHub Actions

### Workflows
- **CI Pipeline** (`ci-pipeline.yml`): Main build, test, and security scan workflow
- **Tests** (`tests.yml`): Python test suite execution

## Project Structure

```
hass-temperature-sensor-website/
├── app.py                          # Main Flask application
├── Dockerfile                      # Multi-platform container build
├── requirements.txt                # Python dependencies
├── tests/
│   └── test_app.py                # Comprehensive test suite (25 tests)
├── .github/
│   └── workflows/
│       ├── ci-pipeline.yml        # Main CI/CD pipeline
│       ├── tests.yml              # Test execution workflow
│       └── README.md              # Workflow documentation
└── README.md                      # This file
```

## License

This project is open source and available under the [MIT License](LICENSE).

## Troubleshooting

### Common Issues

**Application shows "N/A" for temperature:**
- Check that `HOME_ASSISTANT_URL` is correct and accessible
- Verify `ENTITY_ID` exists in your Home Assistant instance
- Ensure `API_TOKEN` is valid and has proper permissions
- Check Home Assistant logs for API errors

**Docker build fails:**
- Ensure Docker is running and up to date
- Check that all files are present in the build context
- Verify Dockerfile syntax

**Tests fail:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Run tests in a virtual environment
- Check Python version compatibility (3.9+)

**Security scan shows vulnerabilities:**
- Review Trivy scan results in GitHub Actions
- Update base Docker image if needed
- Check for false positives in scan results

### Debug Mode

Enable debug logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
python app.py
```

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `python -m pytest tests/ -v`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to your branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- Follow existing code style and patterns
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR
- Use descriptive commit messages

## License

This project is open source and available under the [MIT License](LICENSE).

## Contact

For questions, issues, or contributions:
- 📧 **Issues**: [GitHub Issues](https://github.com/evanhfox/hass-temperature-sensor-website/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/evanhfox/hass-temperature-sensor-website/discussions)
- 🔧 **Pull Requests**: [GitHub Pull Requests](https://github.com/evanhfox/hass-temperature-sensor-website/pulls)
