#!/bin/bash

echo "Starting local development server..."
echo "=================================="

# Activate virtual environment
source .venv/bin/activate

# Skip collectstatic: DEBUG=True runserver serves static from STATICFILES_DIRS,
# and WhiteNoise compression on iCloud-synced ~/Documents path can hang.
echo "Skipping collectstatic (DEBUG runserver serves static directly)"

# Start the development server
echo "Starting server on http://localhost:8008"
echo "Press Ctrl+C to stop the server"
echo ""
DEBUG=True python run_local.py runserver 8008