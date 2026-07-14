FROM python:3.10-slim

# Install system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Create dummy model directory or use existing
RUN mkdir -p model

# Expose port 7860 for Hugging Face Spaces
EXPOSE 7860

# Run the medical theme server as default (uses the PORT environment variable)
ENV PORT=7860
CMD ["python", "app_medical.py"]
