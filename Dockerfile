# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ARG ALPACA_API_KEY
ENV ALPACA_API_KEY $ALPACA_API_KEY
ARG ALPACA_SECRET_KEY
ENV ALPACA_SECRET_KEY $ALPACA_SECRET_KEY

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]