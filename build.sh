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

echo "=== Build Complete ==="
