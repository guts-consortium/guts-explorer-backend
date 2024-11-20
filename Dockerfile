# Use Python as the base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Set the default command
CMD ["python", "-m", "flask", "--app", "src/app", "run"]
