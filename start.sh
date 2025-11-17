#!/bin/bash

# Startup script for Platform Leveling System
# Starts both backend and frontend in development mode

set -e

echo "=================================="
echo "Platform Leveling System Startup"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Check if backend port is already in use
if check_port 8000; then
    echo -e "${YELLOW}Warning: Port 8000 is already in use${NC}"
    echo "Backend may already be running or port is occupied"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if frontend port is already in use
if check_port 3000; then
    echo -e "${YELLOW}Warning: Port 3000 is already in use${NC}"
    echo "Frontend may already be running or port is occupied"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install backend dependencies if needed
echo -e "${GREEN}Checking backend dependencies...${NC}"
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "Virtual environment exists"
fi

# Install frontend dependencies if needed
echo -e "${GREEN}Checking frontend dependencies...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "Node modules exist"
fi

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Start backend in background
echo "Starting backend API on port 8000..."
cd backend
source venv/bin/activate
python api.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! check_port 8000; then
    echo -e "${RED}Error: Backend failed to start${NC}"
    echo "Check backend.log for details"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ Backend running (PID: $BACKEND_PID)${NC}"

# Start frontend in foreground
echo "Starting frontend on port 3000..."
echo ""
cd frontend
npm start

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Wait for frontend process
wait
