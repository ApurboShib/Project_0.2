#!/bin/bash

# Legal Drafting Assistant - Run Script

set -e

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Repair missing/broken pip inside the virtual environment
if ! python -m pip --version >/dev/null 2>&1; then
    echo "🛠️  pip is missing in .venv, repairing with ensurepip..."
    python -m ensurepip --upgrade
fi

# Install/update dependencies
echo "📚 Installing dependencies..."
python -m pip install --upgrade pip setuptools wheel 2>&1 | grep -i -E "(success|already|installed|error)" || true
python -m pip install -r requirements.txt 2>&1 | tail -10

# Heal partially installed environments (common after interrupted installs)
if ! python -c "import fastapi, pydantic, chromadb" >/dev/null 2>&1; then
    echo "🛠️  Detected broken package state, repairing dependencies..."
    python -m pip install --force-reinstall -r requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo " Please edit .env and add your ANTHROPIC_API_KEY"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Create data directory
mkdir -p data

# Silence Chroma telemetry in local development
export ANONYMIZED_TELEMETRY="false"
export CHROMA_ANONYMIZED_TELEMETRY="false"

# Start the server
echo ""
echo "🚀 Starting Legal Drafting Assistant..."
echo "📍 Open http://localhost:8000 in your browser"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
