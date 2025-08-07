#!/bin/bash
# Cloud Run startup script to handle PORT environment variable

# Set APP_PORT to the Cloud Run PORT if it exists, otherwise use 8000
export APP_PORT=${PORT:-8000}

echo "Starting ChatCal.ai on port $APP_PORT (Cloud Run PORT=$PORT)"

# Start the application
exec uvicorn app.api.main:app --host 0.0.0.0 --port $APP_PORT --workers 1