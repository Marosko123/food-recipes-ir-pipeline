#!/bin/bash

# Food Recipes - Stop All Services
echo "🛑 Stopping Food Recipes Application..."

# Kill API Server
echo "🔧 Stopping API Server..."
pkill -f "python.*api_server.py" 2>/dev/null || true

# Kill Frontend
echo "🎨 Stopping Frontend..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Check if processes are still running
if pgrep -f "python.*api_server.py" > /dev/null; then
    echo "⚠️  API Server still running, force killing..."
    pkill -9 -f "python.*api_server.py" 2>/dev/null || true
fi

if pgrep -f "next dev" > /dev/null; then
    echo "⚠️  Frontend still running, force killing..."
    pkill -9 -f "next dev" 2>/dev/null || true
fi

echo "✅ All services stopped successfully!"
