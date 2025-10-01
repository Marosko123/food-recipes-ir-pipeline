#!/bin/bash

# Food Recipes - Complete Startup Script
# This script starts both the API server and frontend

echo "🍳 Starting Food Recipes Application..."
echo "========================================"

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*api_server.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if required files exist
if [ ! -f "data/normalized/recipes.jsonl" ]; then
    echo "❌ Recipe data not found. Please run the parser first."
    echo "   Run: python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl"
    exit 1
fi

if [ ! -d "data/index/v1" ]; then
    echo "❌ Search index not found. Please run the indexer first."
    echo "   Run: python -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1"
    exit 1
fi

# Start API Server
echo "🚀 Starting API Server on port 8000..."
if check_port 8000; then
    python api_server.py &
    API_PID=$!
    echo "   API Server PID: $API_PID"
    
    # Wait for API server to be ready
    if wait_for_service "http://localhost:8000/api/health" "API Server"; then
        echo "✅ API Server is running successfully!"
    else
        echo "❌ Failed to start API Server"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
else
    echo "❌ Cannot start API Server - port 8000 is in use"
    exit 1
fi

# Start Frontend
echo "🎨 Starting Frontend on port 3000..."
cd frontend

if check_port 3000; then
    npm run dev &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
    
    # Wait for frontend to be ready
    if wait_for_service "http://localhost:3000" "Frontend"; then
        echo "✅ Frontend is running successfully!"
    else
        echo "❌ Failed to start Frontend"
        kill $FRONTEND_PID 2>/dev/null || true
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
else
    echo "❌ Cannot start Frontend - port 3000 is in use"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

cd ..

echo ""
echo "🎉 Food Recipes Application is now running!"
echo "========================================"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 API Server: http://localhost:8000"
echo "📊 API Health: http://localhost:8000/api/health"
echo ""
echo "📝 To stop the application:"
echo "   Press Ctrl+C or run: ./stop_all.sh"
echo ""
echo "🔍 To view logs:"
echo "   API Server: tail -f data/crawl.log"
echo "   Frontend: Check terminal output"
echo ""

# Keep script running and show status
echo "📊 Application Status:"
echo "   API Server PID: $API_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Food Recipes Application..."
    kill $API_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Application stopped successfully!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
echo "Press Ctrl+C to stop the application..."
wait
