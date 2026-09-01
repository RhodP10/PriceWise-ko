# Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Copy requirements from backend folder and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and the Chromium browser with all system dependencies
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

# Copy the contents of the backend folder
COPY backend/ .

# Expose the port Render expects
EXPOSE 10000

# Start the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
