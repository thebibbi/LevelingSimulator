#!/bin/bash

# Platform Leveling System - Quick Setup Script

echo "=================================="
echo "Platform Leveling System Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✓ $python_version found"
else
    echo "✗ Python 3 not found. Please install Python 3.8 or later."
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [[ $? -eq 0 ]]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Create directory structure
echo ""
echo "Creating directory structure..."
mkdir -p docs
mkdir -p tests
mkdir -p logs

echo "✓ Directory structure created"

# Set file permissions
echo ""
echo "Setting file permissions..."
chmod +x *.py

echo "✓ Permissions set"

# Test imports
echo ""
echo "Testing Python imports..."
python3 -c "import numpy; import matplotlib; import serial; print('✓ All imports successful')"

if [[ $? -ne 0 ]]; then
    echo "✗ Import test failed"
    exit 1
fi

# Display IP address for iPhone connection
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Your computer's IP address for iPhone IMU connection:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "Could not detect IP"
else
    # Linux
    hostname -I | awk '{print $1}' || echo "Could not detect IP"
fi

echo ""
echo "Next steps:"
echo "1. Configure iPhone IMU app with your computer's IP and port 5555"
echo "2. Run: python3 platform_visualizer.py tripod"
echo "3. See README.md for detailed instructions"
echo ""
