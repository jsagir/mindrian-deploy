#!/usr/bin/env bash
# Render Build Script for Mindrian
# This runs before pip install

set -e

echo "=== Mindrian Build Script ==="

# Install system dependencies for pdf2image
echo "Installing poppler-utils for PDF processing..."
apt-get update && apt-get install -y poppler-utils

echo "poppler-utils installed successfully!"
which pdftoppm && pdftoppm -v

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database tables (safe to run multiple times)
echo "Initializing database tables..."
if [ -n "$DATABASE_URL" ]; then
    python scripts/init_database.py || echo "Warning: Database init failed (may already exist)"
else
    echo "No DATABASE_URL set, skipping database init"
fi

echo "=== Build Complete ==="
