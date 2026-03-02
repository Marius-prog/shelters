#!/bin/bash

echo "Starting local development server..."
echo "=================================="

# Activate virtual environment
source venv/bin/activate

# Collect static files (suppress output)
echo "Collecting static files..."
python run_local.py collectstatic --noinput > /dev/null 2>&1

# Start the development server
echo "Starting server on http://localhost:8008"
echo "Press Ctrl+C to stop the server"
echo ""
DEBUG=True python run_local.py runserver 8008