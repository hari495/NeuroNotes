#!/bin/bash

echo "========================================="
echo "Frontend TypeScript Setup"
echo "========================================="
echo ""

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    echo "   Please run this script from the frontend directory:"
    echo "   cd frontend && ./setup.sh"
    exit 1
fi

echo "📦 Installing TypeScript..."
npm install --save-dev typescript

echo ""
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server:"
echo "  npm run dev"
echo ""
echo "The app will be available at: http://localhost:5173"
echo ""
