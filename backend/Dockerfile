# Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright and Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements from backend folder and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and the Chromium browser
RUN pip install playwright && playwright install chromium

# Copy the contents of the backend folder
COPY backend/ .

# Expose the port Render expects
EXPOSE 10000

# Start the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
