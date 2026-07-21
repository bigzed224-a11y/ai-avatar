#!/bin/bash
# AI Avatar Lip-Sync Setup Script

echo "=== AI Avatar Lip-Sync Setup ==="
echo ""

# Create virtual environment
echo "1. Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install basic dependencies
echo "2. Installing basic dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install ffmpeg if not present
echo "3. Checking ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "   ffmpeg not found. Installing..."
    sudo apt-get update && sudo apt-get install -y ffmpeg
else
    echo "   ffmpeg already installed"
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the server:"
echo "  cd backend"
echo "  python main.py"
echo ""
echo "Then open frontend/index.html in your browser"
