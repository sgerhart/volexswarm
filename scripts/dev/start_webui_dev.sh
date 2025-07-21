#!/bin/bash

# VolexSwarm Web UI Development Startup Script

echo "🚀 Starting VolexSwarm Web UI Development Environment..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the VolexSwarm root directory"
    exit 1
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != *"volexswarm-env"* ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Please activate volexswarm-env"
    echo "   Run: pyenv activate volexswarm-env"
fi

# Start the backend services (Vault, DB, Agents)
echo "📦 Starting backend services..."
docker-compose up -d vault db research signal execution meta

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
docker-compose ps

# Start the web UI backend
echo "🌐 Starting Web UI backend..."
cd webui/backend
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start the React development server
echo "⚛️  Starting React development server..."
cd ..
npm install
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ VolexSwarm Web UI Development Environment Started!"
echo ""
echo "📱 Access Points:"
echo "   Frontend (React): http://localhost:3000"
echo "   Backend (FastAPI): http://localhost:8005"
echo "   API Docs: http://localhost:8005/docs"
echo ""
echo "🔧 Services:"
echo "   Vault: http://localhost:8200"
echo "   Research Agent: http://localhost:8001"
echo "   Signal Agent: http://localhost:8003"
echo "   Execution Agent: http://localhost:8002"
echo "   Meta Agent: http://localhost:8004"
echo ""
echo "🛑 To stop: Press Ctrl+C or run 'pkill -f main.py' and 'pkill -f react-scripts'"
echo ""

# Wait for user to stop
wait 