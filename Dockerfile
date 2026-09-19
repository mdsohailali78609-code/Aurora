# Use the official Python slim image for a smaller footprint
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if required (e.g., for building sqlite/Postgres extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI server using Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
