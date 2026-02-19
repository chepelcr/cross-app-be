#!/bin/bash

echo "Rebooting JCampos server..."

# Kill existing server processes
pkill -f "server/index.ts" || true
pkill -f "node.*server" || true
pkill -f "npm run dev" || true

# Wait a moment for processes to terminate
sleep 2

# Start the server
npm run dev