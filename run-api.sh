#!/bin/bash

# Run this script from the project directory
# Usage: ./run-api.sh

source .venv/bin/activate
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting API server (production-like)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
