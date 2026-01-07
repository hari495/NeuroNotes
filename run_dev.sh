#!/bin/bash

# Development Runner Script for RAG Notes App
# Starts both FastAPI backend and React frontend

set -e

echo "🚀 Starting RAG Notes App Development Environment"
echo ""

# Check if in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Are you in the project root?"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM

# Check if Ollama is running
echo "🔍 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama doesn't appear to be running on http://localhost:11434"
    echo "   Start it with: ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start FastAPI backend
echo "📦 Starting FastAPI backend on http://localhost:8000..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Error: Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo "   ✅ Backend is healthy"

# Start React frontend
echo ""
echo "⚛️  Starting React frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✨ Services started successfully!"
echo ""
echo "📍 URLs:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
