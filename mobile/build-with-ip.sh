#!/bin/bash

# Script to automatically detect local IP and build Android app with correct server URL
# Usage: ./build-with-ip.sh [build_command]
# Example: ./build-with-ip.sh assembleDebug
#          ./build-with-ip.sh installDebug

# Detect local IP address
# Try different methods based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1 | awk '{print $7}' | head -n1)
else
    echo "Unsupported OS. Please set SERVER_URL manually."
    exit 1
fi

if [ -z "$IP" ]; then
    echo "Could not detect IP address. Using default."
    IP="192.168.1.101"
fi

SERVER_URL="http://${IP}:5173"
echo "Detected IP: $IP"
echo "Using server URL: $SERVER_URL"
echo ""

# Default build command if none provided
BUILD_CMD=${1:-assembleDebug}

# Build with the detected IP
./gradlew -PSERVER_URL="$SERVER_URL" $BUILD_CMD

