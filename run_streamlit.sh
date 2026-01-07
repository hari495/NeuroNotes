#!/bin/bash

# Launch script for Streamlit RAG Notes App
#
# This script starts the Streamlit interface for the RAG Notes App.
# Make sure the FastAPI backend is running first!

echo "🚀 Starting RAG Notes Streamlit Interface..."
echo ""
echo "Make sure the FastAPI backend is running:"
echo "  python main.py"
echo ""
echo "Access the app at: http://localhost:8501"
echo ""

streamlit run app/frontend.py
