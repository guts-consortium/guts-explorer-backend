# Use Python as the base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port Flask/Gunicorn will run on
EXPOSE 5000

# Set the default command to run with Gunicorn in production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.app:app"]
