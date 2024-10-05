



# Dockerfile to package this app into a container
# Create a Dockerfile for building a containerized version of the app
# FROM directive sets the base image to Python 3.9
FROM alpine:python3.20

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV HOME_ASSISTANT_URL=
ENV ENTITY_ID=7
ENV API_TOKEN=
ENV USE_DUMMY_DATA=false

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["flask", "run"]
