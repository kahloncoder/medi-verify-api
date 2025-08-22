# Use a stable, official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# --- THIS IS THE CRITICAL STEP ---
# Update package lists and install the zbar system library.
# Then, clean up to keep the image small.
RUN apt-get update && apt-get install -y libzbar0 && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# --- RENDER SPECIFIC STEP ---
# Tell Docker to expose port 10000. Render will route traffic to this port.
EXPOSE 10000

# The command to run when the container starts.
# Note we are explicitly using port 10000 here.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]