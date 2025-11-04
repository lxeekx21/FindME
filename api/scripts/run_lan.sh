#!/bin/bash
# Run FastAPI server accessible on local network (LAN mode)

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "🚀 Starting FastAPI server in LAN mode..."
echo "📡 Server will be accessible at:"
echo "   - Local: http://localhost:8000"
echo "   - LAN: http://${LOCAL_IP}:8000"
echo ""
echo "📚 API Docs: http://${LOCAL_IP}:8000/docs"
echo ""

# Run uvicorn with host 0.0.0.0 to allow LAN access
uvicorn app.main:app --reload --host 0.0.0.0

