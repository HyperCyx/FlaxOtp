# === TELEGRAM BOT DOCKERFILE FOR KOYEB.COM ===
# Optimized for production deployment with health checks

# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bot.py .
COPY config.py .

# Create health check endpoint script
RUN echo '#!/usr/bin/env python3\n\
import http.server\n\
import socketserver\n\
import threading\n\
import time\n\
from datetime import datetime\n\
\n\
class HealthHandler(http.server.BaseHTTPRequestHandler):\n\
    def do_GET(self):\n\
        if self.path == "/health":\n\
            self.send_response(200)\n\
            self.send_header("Content-type", "application/json")\n\
            self.end_headers()\n\
            response = {\n\
                "status": "healthy",\n\
                "message": "Bot Active",\n\
                "timestamp": datetime.utcnow().isoformat() + "Z",\n\
                "service": "telegram-bot"\n\
            }\n\
            import json\n\
            self.wfile.write(json.dumps(response).encode())\n\
        else:\n\
            self.send_response(404)\n\
            self.end_headers()\n\
\n\
    def log_message(self, format, *args):\n\
        pass  # Suppress default logging\n\
\n\
def start_health_server():\n\
    with socketserver.TCPServer(("", 8080), HealthHandler) as httpd:\n\
        httpd.serve_forever()\n\
\n\
if __name__ == "__main__":\n\
    # Start health check server in background\n\
    health_thread = threading.Thread(target=start_health_server, daemon=True)\n\
    health_thread.start()\n\
    print("Health check server started on port 8080")\n\
    \n\
    # Import and run the main bot\n\
    import bot\n\
    import asyncio\n\
    asyncio.run(bot.main())\n\
' > /app/start_bot.py && chmod +x /app/start_bot.py

# Create cache directory for user data
RUN mkdir -p /app/user_cache

# Expose port 8080 for health checks
EXPOSE 8080

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Set proper file permissions
RUN chmod +x /app/start_bot.py

# Run the application
CMD ["python3", "/app/start_bot.py"]